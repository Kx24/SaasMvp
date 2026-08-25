"""
Gatekeeper determinista para el piloto agéntico (docs/kanban_agente.md,
PILOT-01). Corre los 3 gates de verificación de §0.2 del kanban agéntico
(idénticos a Documentacion/KANBAN_PROYECTO.md §2.2: ruff, suite, migraciones)
y emite un único JSON a stdout, exit code 0 solo cuando `passed` es true.

    python scripts/gatekeeper.py

El gate de ruff cuenta solo errores en archivos tocados respecto de HEAD
(diff + untracked) -- el repo tiene ~135 errores preexistentes fuera de
alcance (#AUD-10), y este script no debe bloquear cards que no los tocan.

Sin variables de entorno, sin red. No modifica nada fuera de su propio
stdout (no escribe archivos, no toca settings, no corre con --keepdb).
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# apps/core/tests/test_gatekeeper.py invoca este script como subproceso
# para probarlo -- y esos tests viven dentro de "apps", que es justo lo
# que el gate de tests corre. Sin esta guarda, el gate de tests lanza
# manage.py test apps -> descubre test_gatekeeper.py -> vuelve a invocar
# este script -> vuelve a correr manage.py test apps -> ... recursión sin
# límite (confirmado en vivo: más de 150 procesos python.exe en ~3 min
# antes de encontrarlo). El gate de tests propaga esta env var al
# subproceso; test_gatekeeper.py se salta a sí mismo cuando la ve.
RECURSION_GUARD_ENV = 'GATEKEEPER_TEST_RUN'


def _run(cmd, timeout=180, env=None):
    # stdin=DEVNULL es obligatorio: sin él, un proceso hijo (python.exe)
    # lanzando otro subproceso hereda un stdin que en Windows se queda
    # esperando lectura indefinidamente -- el comando nunca hace timeout
    # a nivel de subprocess, se cuelga por completo. Confirmado en vivo:
    # el mismo comando corrido a mano en la shell termina en ~10s; corrido
    # vía subprocess.run() sin stdin=DEVNULL nunca retorna.
    return subprocess.run(
        cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=timeout,
        stdin=subprocess.DEVNULL, env=env,
    )


def _changed_python_files():
    """Archivos .py tocados vs HEAD (diff) + no trackeados, que aún existen en disco."""
    tracked = _run(['git', 'diff', '--name-only', 'HEAD', '--', '*.py'])
    untracked = _run(['git', 'ls-files', '--others', '--exclude-standard', '--', '*.py'])

    candidates = set(tracked.stdout.splitlines()) | set(untracked.stdout.splitlines())
    return sorted(
        path for path in candidates
        if path and (BASE_DIR / path).is_file()
    )


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


def _run_tests_gate():
    child_env = {**os.environ, RECURSION_GUARD_ENV: '1'}
    result = _run(
        [sys.executable, 'manage.py', 'test', 'apps', '-v', '1'],
        timeout=300,
        env=child_env,
    )
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


def main():
    start = time.monotonic()

    gates = {
        'ruff': _run_ruff_gate(),
        'tests': _run_tests_gate(),
        'migrations': _run_migrations_gate(),
    }
    passed = all(gate['passed'] for gate in gates.values())

    payload = {
        'passed': passed,
        'gates': gates,
        'duration_s': round(time.monotonic() - start, 2),
    }
    print(json.dumps(payload))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
