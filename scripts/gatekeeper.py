"""
Gatekeeper determinista para el piloto agéntico (docs/kanban_agente.md,
PILOT-01). Corre los 3 gates de verificación de §0.2 del kanban agéntico
(idénticos a Documentacion/KANBAN_PROYECTO.md §2.2: ruff, suite, migraciones)
y emite un único JSON a stdout, exit code 0 solo cuando `passed` es true.

    python scripts/gatekeeper.py

El gate de ruff cuenta solo errores en archivos tocados respecto de HEAD
(diff + untracked).

Modo estricto (ronda 4, lo usa orchestrate.py):

    python scripts/gatekeeper.py --strict            # + cobertura, bandit, e2e
    python scripts/gatekeeper.py --strict --update-baseline
    python scripts/gatekeeper.py --red-check apps.x.tests.test_y [...]

--strict agrega tres gates que el contrato de TDD pedía y nadie verificaba:
cobertura y bandit como trinquete contra scripts/gate_baseline.json (no
pueden empeorar; la deuda previa no bloquea) y Playwright cuando la card
toca templates/, static/ o tests/e2e/. --update-baseline es la única
escritura del script y solo ocurre con el gate en verde.

--red-check confirma el rojo sin depender de la palabra del agente: corre
los tests indicados en un worktree temporal de HEAD al que solo se copian
los archivos de test nuevos o modificados. Si pasan ahí, el test no prueba
el cambio.

Sin variables de entorno, sin red.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BASELINE_PATH = BASE_DIR / 'scripts' / 'gate_baseline.json'

# Grupos de cobertura del contrato (KANBAN_PROYECTO.md, Arnés de TDD).
COVERAGE_GROUPS = {
    'orders': ('apps/orders/',),
    'tenants_core': ('apps/tenants/middleware.py', 'apps/tenants/managers.py'),
    'total': ('apps/',),
}
COVERAGE_TOLERANCE = 0.2  # puntos porcentuales de ruido aceptado
COVERAGE_OMIT = '*/migrations/*,*/tests/*,*/tests.py,*/tests_*.py'
E2E_PATHS = ('templates/', 'static/', 'tests/e2e/')
_TEST_FILE_RE = re.compile(r'(^|/)(tests/.*\.py|tests[^/]*\.py|test_[^/]*\.py)$')

# apps/core/tests/test_gatekeeper.py invoca este script como subproceso
# para probarlo -- y esos tests viven dentro de "apps", que es justo lo
# que el gate de tests corre. Sin esta guarda, el gate de tests lanza
# manage.py test apps -> descubre test_gatekeeper.py -> vuelve a invocar
# este script -> vuelve a correr manage.py test apps -> ... recursión sin
# límite (confirmado en vivo: más de 150 procesos python.exe en ~3 min
# antes de encontrarlo). El gate de tests propaga esta env var al
# subproceso; test_gatekeeper.py se salta a sí mismo cuando la ve.
RECURSION_GUARD_ENV = 'GATEKEEPER_TEST_RUN'


def _venv_env(extra=None):
    """PATH con el venv primero: `npx playwright test` lanza `python manage.py ...`
    y con el Python del sistema el servidor e2e no levanta (verificado 2026-11-14)."""
    env = {**os.environ, **(extra or {})}
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    return env


def _run(cmd, timeout=180, env=None, cwd=None):
    # stdin=DEVNULL es obligatorio: sin él, un proceso hijo (python.exe)
    # lanzando otro subproceso hereda un stdin que en Windows se queda
    # esperando lectura indefinidamente -- el comando nunca hace timeout
    # a nivel de subprocess, se cuelga por completo. Confirmado en vivo:
    # el mismo comando corrido a mano en la shell termina en ~10s; corrido
    # vía subprocess.run() sin stdin=DEVNULL nunca retorna.
    return subprocess.run(
        cmd, cwd=cwd or BASE_DIR, capture_output=True, text=True, timeout=timeout,
        stdin=subprocess.DEVNULL, env=env, encoding='utf-8', errors='replace',
    )


def _changed_files():
    """Todo archivo tocado vs HEAD (diff) + no trackeado."""
    tracked = _run(['git', 'diff', '--name-only', 'HEAD'])
    untracked = _run(['git', 'ls-files', '--others', '--exclude-standard'])
    return sorted(
        path for path in set(tracked.stdout.splitlines()) | set(untracked.stdout.splitlines())
        if path
    )


def _changed_python_files():
    """Archivos .py tocados vs HEAD (diff) + no trackeados, que aún existen en disco."""
    return [
        path for path in _changed_files()
        if path.endswith('.py') and (BASE_DIR / path).is_file()
    ]


def _load_baseline():
    if BASELINE_PATH.is_file():
        return json.loads(BASELINE_PATH.read_text(encoding='utf-8'))
    return {}


def _run_ruff_gate():
    files = _changed_python_files()
    if not files:
        return {'passed': True, 'files_checked': 0, 'errors': 0, 'detail': ''}

    result = _run([sys.executable, '-m', 'ruff', 'check', *files])
    # ruff devuelve 0 sin errores, 1 con errores encontrados.
    passed = result.returncode == 0
    error_lines = [
        line for line in result.stdout.splitlines()
        if line and not line.startswith('Found ') and not line.startswith('[*]')
    ]
    return {
        'passed': passed,
        'files_checked': len(files),
        'errors': 0 if passed else len(error_lines),
        'detail': result.stdout.strip(),
    }


_TESTS_SUMMARY_RE = re.compile(r'^Ran (\d+) tests? in')
_TESTS_OK_SKIPPED_RE = re.compile(r'^OK \(skipped=(\d+)\)')
_TESTS_FAILED_RE = re.compile(
    r'^FAILED \('
    r'(?:failures=(\d+))?,?\s*'
    r'(?:errors=(\d+))?,?\s*'
    r'(?:skipped=(\d+))?'
    r'\)'
)


def _run_tests_gate(coverage_file=None):
    child_env = {**os.environ, RECURSION_GUARD_ENV: '1'}
    cmd = [sys.executable, 'manage.py', 'test', 'apps', '-v', '1']
    if coverage_file:
        child_env['COVERAGE_FILE'] = coverage_file
        cmd = [
            sys.executable, '-m', 'coverage', 'run', '--source=apps', f'--omit={COVERAGE_OMIT}',
            'manage.py', 'test', 'apps', '-v', '1',
        ]
    result = _run(cmd, timeout=600 if coverage_file else 300, env=child_env)
    output = result.stdout + result.stderr

    total = 0
    failures = 0
    skipped = 0

    for line in output.splitlines():
        line = line.strip()
        m = _TESTS_SUMMARY_RE.match(line)
        if m:
            total = int(m.group(1))
            continue
        m = _TESTS_OK_SKIPPED_RE.match(line)
        if m:
            skipped = int(m.group(1))
            continue
        if line == 'OK':
            continue
        m = _TESTS_FAILED_RE.match(line)
        if m:
            failures = int(m.group(1) or 0) + int(m.group(2) or 0)
            skipped = int(m.group(3) or 0)

    passed = result.returncode == 0 and failures == 0
    return {
        'passed': passed,
        'total': total,
        'failures': failures,
        'skipped': skipped,
        'detail': '' if passed else output[-4000:],
    }


def _run_migrations_gate():
    result = _run(
        [sys.executable, 'manage.py', 'makemigrations', '--check', '--dry-run'],
        timeout=60,
    )
    passed = result.returncode == 0
    return {
        'passed': passed,
        'detail': '' if passed else (result.stdout + result.stderr).strip(),
    }


def _coverage_percentages(coverage_file):
    env = {**os.environ, 'COVERAGE_FILE': coverage_file}
    out_path = coverage_file + '.json'
    result = _run([sys.executable, '-m', 'coverage', 'json', '-o', out_path, '-q'], env=env)
    if not Path(out_path).is_file():
        return None, (result.stdout + result.stderr).strip()
    files = json.loads(Path(out_path).read_text(encoding='utf-8'))['files']
    percentages = {}
    for group, prefixes in COVERAGE_GROUPS.items():
        statements = covered = 0
        for name, data in files.items():
            if name.replace('\\', '/').startswith(prefixes):
                statements += data['summary']['num_statements']
                covered += data['summary']['covered_lines']
        percentages[group] = round(100 * covered / statements, 2) if statements else 100.0
    return percentages, ''


def _run_coverage_gate(coverage_file, baseline):
    percentages, error = _coverage_percentages(coverage_file)
    if percentages is None:
        return {'passed': False, 'detail': f'coverage json falló: {error}'}
    base = baseline.get('coverage', {})
    drops = {
        group: {'antes': base[group], 'ahora': pct}
        for group, pct in percentages.items()
        if group in base and pct < base[group] - COVERAGE_TOLERANCE
    }
    return {
        'passed': not drops,
        'percent': percentages,
        'baseline': base,
        'detail': '' if not drops else f'La cobertura bajó: {json.dumps(drops)}',
    }


def _run_bandit_gate(baseline):
    result = _run([
        sys.executable, '-m', 'bandit', '-r', 'apps', 'config',
        '-x', '*/tests/*,*/migrations/*', '-ll', '-q', '-f', 'json',
    ], timeout=180)
    try:
        findings = json.loads(result.stdout)['results']
    except (ValueError, KeyError):
        return {'passed': False, 'detail': (result.stdout + result.stderr)[-2000:]}
    count = len(findings)
    base = baseline.get('bandit_medium_high')
    passed = base is None or count <= base
    changed = set(_changed_files())
    in_changed = [
        f"{f['filename']}:{f['line_number']} {f['test_id']} {f['issue_text']}"
        for f in findings
        if f['filename'].replace('\\', '/').removeprefix('./') in changed
    ]
    return {
        'passed': passed,
        'medium_high': count,
        'baseline': base,
        'detail': '' if passed else (
            f'bandit -ll subió de {base} a {count}. En archivos tocados: ' + '; '.join(in_changed)
        ),
    }


def _run_e2e_gate():
    touched = [path for path in _changed_files() if path.startswith(E2E_PATHS)]
    if not touched:
        return {'passed': True, 'ran': False, 'detail': ''}
    npx = shutil.which('npx')
    if not npx:
        return {'passed': False, 'ran': False, 'detail': 'npx no está en el PATH'}
    result = _run([npx, 'playwright', 'test', '--reporter=line'], timeout=420, env=_venv_env())
    passed = result.returncode == 0
    return {
        'passed': passed,
        'ran': True,
        'detail': '' if passed else (result.stdout + result.stderr)[-4000:],
    }


def red_check(labels):
    """Corre `labels` contra HEAD + solo los archivos de test tocados.
    Rojo confirmado = esa corrida FALLA."""
    test_files = [path for path in _changed_files() if _TEST_FILE_RE.search(path)]
    tmp = Path(tempfile.mkdtemp(prefix='gate_red_'))
    worktree = tmp / 'head'
    added = _run(['git', 'worktree', 'add', '--detach', str(worktree), 'HEAD'])
    if added.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        return {'red_confirmed': False, 'detail': f'no se pudo crear el worktree: {added.stderr.strip()}'}
    try:
        # .env no esta versionado y sin el settings no importa (SECRET_KEY):
        # sin esta copia todo test "falla" y el rojo seria un falso positivo
        # (paso en BOLT-17, lo detecto el validador).
        if (BASE_DIR / '.env').is_file():
            shutil.copy2(BASE_DIR / '.env', worktree / '.env')
        for rel in test_files:
            src = BASE_DIR / rel
            if src.is_file():
                dest = worktree / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
        result = _run(
            [sys.executable, 'manage.py', 'test', *labels, '-v', '1'],
            timeout=300, cwd=worktree, env={**os.environ, RECURSION_GUARD_ENV: '1'},
        )
        output = result.stdout + result.stderr
        ran = re.search(r'^Ran (\d+) tests? in', output, re.M)
        tests_ran = int(ran.group(1)) if ran else 0
        # Rojo = los tests llegaron a ejecutarse y fallaron. Un error de
        # entorno antes de correr (settings, import de manage.py) no cuenta.
        red = result.returncode != 0 and tests_ran > 0
        if red:
            detail = output[-1500:]
        elif tests_ran == 0:
            detail = 'Los tests no llegaron a ejecutarse en HEAD (error de entorno): ' + output[-1200:]
        else:
            detail = 'Los tests PASAN sin el cambio: no prueban la card.'
        return {
            'red_confirmed': red,
            'tests_ran': tests_ran,
            'labels': list(labels),
            'test_files_copied': test_files,
            'detail': detail,
        }
    finally:
        _run(['git', 'worktree', 'remove', '--force', str(worktree)])
        _run(['git', 'worktree', 'prune'])
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Gatekeeper determinista del piloto agéntico.')
    parser.add_argument('--strict', action='store_true',
                        help='agrega cobertura, bandit y e2e (trinquete contra gate_baseline.json)')
    parser.add_argument('--update-baseline', action='store_true',
                        help='con --strict y gate verde, reescribe gate_baseline.json')
    parser.add_argument('--red-check', nargs='+', metavar='LABEL',
                        help='confirma que estos tests fallan sin el cambio')
    args = parser.parse_args(argv)

    start = time.monotonic()

    if args.red_check:
        payload = red_check(args.red_check)
        payload['duration_s'] = round(time.monotonic() - start, 2)
        print(json.dumps(payload))
        return 0 if payload['red_confirmed'] else 1

    coverage_dir = tempfile.mkdtemp(prefix='gate_cov_') if args.strict else None
    coverage_file = str(Path(coverage_dir) / '.coverage') if coverage_dir else None
    try:
        gates = {
            'ruff': _run_ruff_gate(),
            'tests': _run_tests_gate(coverage_file),
            'migrations': _run_migrations_gate(),
        }
        if args.strict:
            baseline = _load_baseline()
            gates['coverage'] = _run_coverage_gate(coverage_file, baseline)
            gates['bandit'] = _run_bandit_gate(baseline)
            gates['e2e'] = _run_e2e_gate()
    finally:
        if coverage_dir:
            shutil.rmtree(coverage_dir, ignore_errors=True)

    passed = all(gate['passed'] for gate in gates.values())

    if args.strict and args.update_baseline and passed:
        BASELINE_PATH.write_text(json.dumps({
            'coverage': gates['coverage']['percent'],
            'bandit_medium_high': gates['bandit']['medium_high'],
        }, indent=2) + '\n', encoding='utf-8')

    payload = {
        'passed': passed,
        'gates': gates,
        'duration_s': round(time.monotonic() - start, 2),
    }
    print(json.dumps(payload))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
