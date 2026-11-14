"""
Orquestador del piloto AI-DLC (docs/kanban_agente.md, PILOT-03). Cierra el
circuito planificador -> dev/tester -> gatekeeper -> validador (roles
definidos en .claude/workflows/, PILOT-02) respetando WIP=1 y el tope de
3 reintentos de docs/kanban_agente.md §0.3.

Este script implementa solo la MAQUINA DE ESTADOS: secuenciar turnos,
contar reintentos, decidir DONE/BLOCKED/REJECTED. No invoca un agente
real -- recibe un `AgentRunner` (protocolo con 3 métodos) que hace el
trabajo de cada turno. Conectar un agente real (p.ej. invocar el CLI de
Claude Code en modo no interactivo con los prompts de .claude/workflows/,
o la API de Anthropic) es un paso de integración aparte, fuera de este
script -- por eso no maneja API keys ni credenciales de ningún tipo.
Tampoco hace `git commit` por sí mismo: eso es responsabilidad del turno
de validador (03_validador.md), que corre APROBADO un gate en verde.

    python orchestrate.py [--max-cards N] [--dry-run]

--dry-run usa un runner simulado (ver DryRunAgentRunner) que no invoca
ningún agente real -- sirve para probar que la máquina de estados anda,
sin costo. Sin --dry-run, el runner por defecto (NotWiredAgentRunner)
levanta NotImplementedError: este script, usado como CLI standalone, no
trae un agente real conectado todavía -- hace falta pasar un AgentRunner
propio si se usa orchestrate.py como librería.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / 'scripts' / 'output'
MAX_REPAIR_ATTEMPTS = 3

# --- Runner real (ronda 4, 2026-11-14) -------------------------------------
DEFAULT_MODEL = 'claude-sonnet-5-5'
AGENT_SETTINGS = BASE_DIR / '.claude' / 'settings.agent.json'
WORKFLOWS_DIR = BASE_DIR / '.claude' / 'workflows'
GATEKEEPER = BASE_DIR / 'scripts' / 'gatekeeper.py'
BASELINE_PATH = BASE_DIR / 'scripts' / 'gate_baseline.json'
DEV_TIMEOUT_S = 60 * 60
VALIDATOR_TIMEOUT_S = 20 * 60
MAX_BUDGET_USD = '25'
# Rutas que ninguna card puede tocar salvo que su entrada en cola.json las
# liste en "rutas_permitidas_extra". Es la guardia real: los permisos del
# agente (settings.agent.json) son la primera barrera, esta es la que no
# depende de él.
FORBIDDEN_PATHS = (
    '.env', '.claude/', '.github/', '.idea/', 'orchestrate.py', 'scripts/gatekeeper.py',
    'scripts/gate_baseline.json', 'docs/agente/', 'render.yaml', 'build.sh', 'Procfile',
    'templates/themes/ranchocachimba/', 'CLAUDE.md',
)
VALIDATOR_SCHEMA = {
    'type': 'object',
    'properties': {
        'veredicto': {'type': 'string', 'enum': ['APPROVE', 'REJECT']},
        'motivo': {'type': 'string'},
        'commit_subject': {'type': 'string'},
        'commit_body': {'type': 'string'},
        'hallazgos': {'type': 'array', 'items': {'type': 'string'}},
        'revisar_humano': {'type': 'array', 'items': {'type': 'string'}},
    },
    'required': ['veredicto', 'motivo', 'commit_subject', 'commit_body', 'hallazgos', 'revisar_humano'],
}


class AgentRunner(Protocol):
    def run_planificador(self) -> dict:
        """
        Debe devolver {'queue_empty': True} cuando no hay ninguna card TODO
        elegible, o {'queue_empty': False, 'card': <ID>, ...} en caso
        contrario (ver .claude/workflows/01_planificador.md).
        """
        ...

    def run_dev_tester(self, card: str, attempt: int) -> dict:
        """
        Debe devolver {'passed': bool, ...} -- 'passed' refleja
        GATEKEEPER_JSON.passed del handoff (ver 02_dev_tester.md), no un
        juicio del propio runner.
        """
        ...

    def run_validador(self, card: str, dev_tester_result: dict) -> dict:
        """Debe devolver {'verdict': 'APPROVE' | 'REJECT', ...} (ver 03_validador.md)."""
        ...


class NotWiredAgentRunner:
    """Runner por defecto: no hay ningún agente real conectado todavía."""

    def _unwired(self, turn):
        raise NotImplementedError(
            f"orchestrate.py no tiene un agente real conectado para el turno "
            f"'{turn}'. Usa --dry-run para probar la máquina de estados, o "
            f"pasa tu propio AgentRunner si estás usando run_pipeline() como "
            f"librería (ver .claude/workflows/ para el contrato de cada turno)."
        )

    def run_planificador(self):
        self._unwired('planificador')

    def run_dev_tester(self, card, attempt):
        self._unwired('dev_tester')

    def run_validador(self, card, dev_tester_result):
        self._unwired('validador')


class DryRunAgentRunner:
    """
    Simula un único card pasando limpio por los 3 turnos, sin invocar
    ningún agente real -- solo para probar que la máquina de estados
    (secuenciación, logging) funciona de punta a punta sin costo.
    """

    def __init__(self):
        self._planned = False

    def run_planificador(self):
        if self._planned:
            return {'queue_empty': True}
        self._planned = True
        return {'queue_empty': False, 'card': 'DRY-RUN-CARD'}

    def run_dev_tester(self, card, attempt):
        return {'passed': True, 'gatekeeper_json': {'passed': True, 'dry_run': True}}

    def run_validador(self, card, dev_tester_result):
        return {'verdict': 'APPROVE', 'detail': 'dry-run, sin commit real'}


@dataclass
class CardOutcome:
    card: str
    status: str  # 'DONE' | 'BLOCKED' | 'REJECTED'
    attempts: int
    detail: dict = field(default_factory=dict)


def run_pipeline(runner: AgentRunner, max_cards: Optional[int] = None, log_fn=None,
                 max_failures: Optional[int] = None) -> list:
    outcomes = []

    def _failed(card, status, detail):
        hook = getattr(runner, 'on_card_failed', None)
        if hook:
            hook(card, status, detail)

    while max_cards is None or len(outcomes) < max_cards:
        failures = sum(1 for o in outcomes if o.status != 'DONE')
        if max_failures is not None and failures >= max_failures:
            if log_fn:
                log_fn({'turn': 'orchestrator', 'stopped': f'{failures} cards fallidas'})
            break

        plan = runner.run_planificador()
        if log_fn:
            log_fn({'turn': 'planificador', **plan})
        if plan.get('queue_empty'):
            break
        card = plan['card']

        dev_result = {'passed': False}
        attempt = 0
        for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
            dev_result = runner.run_dev_tester(card, attempt)
            if log_fn:
                log_fn({'turn': 'dev_tester', 'card': card, 'attempt': attempt, **dev_result})
            # 'abort': el agente declaro la card bloqueada (falta una decision
            # o un insumo) o murio -- reintentar a ciegas no ayuda.
            if dev_result.get('passed') or dev_result.get('abort'):
                break

        if not dev_result.get('passed'):
            outcomes.append(CardOutcome(card=card, status='BLOCKED', attempts=attempt, detail=dev_result))
            if log_fn:
                log_fn({'turn': 'orchestrator', 'card': card, 'status': 'BLOCKED', 'attempts': attempt})
            _failed(card, 'BLOCKED', dev_result)
            continue

        verdict = runner.run_validador(card, dev_result)
        if log_fn:
            log_fn({'turn': 'validador', 'card': card, **verdict})

        status = 'DONE' if verdict.get('verdict') == 'APPROVE' else 'REJECTED'
        outcomes.append(CardOutcome(card=card, status=status, attempts=attempt, detail=verdict))
        if status != 'DONE':
            _failed(card, status, verdict)

    return outcomes


class PreconditionError(RuntimeError):
    """El repo no está en condiciones de correr una ronda desatendida."""


def _trim(text, limit=6000):
    text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit // 2] + '\n[...]\n' + text[-limit // 2:]


class ClaudeCliRunner:
    """
    Runner real: cada turno es una sesión nueva de `claude -p` (Claude Code
    en modo no interactivo) con el modelo de ejecución. Reparto de trabajo:

    - Planificador: NO es un LLM. Los specs los escribe la sesión de
      planificación (modelo grande) en docs/agente/<ronda>/; acá solo se
      toma la primera card TODO de cola.json.
    - Dev/Tester: sesión con permisos de edición (settings.agent.json).
      No commitea ni declara el gate: al volver, ESTE proceso corre
      gatekeeper --strict, el red-check y el control de alcance.
    - Validador: sesión de solo lectura que devuelve un veredicto con
      esquema JSON. Con APPROVE, este proceso commitea y hace push.

    El agente nunca ejecuta git commit/push ni edita el gate: lo que decide
    DONE es código determinista.
    """

    def __init__(self, queue_path, model=DEFAULT_MODEL, push=True):
        self.queue_path = Path(queue_path).resolve()
        self.round_dir = self.queue_path.parent
        self.model = model
        self.push = push
        self.claude = shutil.which('claude')
        self._sessions = {}       # card id -> session_id del dev/tester
        self._last_failure = {}   # card id -> detalle del último gate fallido
        self._costs = {}          # card id -> USD acumulado
        if not self.claude:
            raise PreconditionError('No encuentro el ejecutable `claude` en el PATH.')

    # --- utilidades -------------------------------------------------------
    def _env(self):
        env = dict(os.environ)
        env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
        return env

    def _git(self, *args, check=False):
        result = subprocess.run(
            ['git', *args], cwd=BASE_DIR, capture_output=True, text=True,
            stdin=subprocess.DEVNULL, encoding='utf-8', errors='replace',
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} falló: {result.stderr.strip()}")
        return result

    def _load_queue(self):
        return json.loads(self.queue_path.read_text(encoding='utf-8'))

    def _save_queue(self, queue):
        self.queue_path.write_text(
            json.dumps(queue, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        self._write_status(queue)

    def _card(self, queue, card_id):
        return next(c for c in queue['cards'] if c['id'] == card_id)

    def _write_status(self, queue):
        icon = {'TODO': '⏳', 'DONE': '✅', 'BLOCKED': '⛔', 'REJECTED': '❌'}
        lines = [
            f"# Ronda {queue['ronda']} — estado",
            '',
            f"Rama `{queue['rama']}` · generado por `orchestrate.py` (no editar a mano).",
            '',
            '| Card | Maestra | Título | Estado | Commit | Costo USD |',
            '|---|---|---|---|---|---|',
        ]
        for c in queue['cards']:
            lines.append(
                f"| `{c['id']}` | `{c['maestra']}` | {c['titulo']} | "
                f"{icon.get(c['estado'], '')} {c['estado']} | {c.get('commit', '')} | {c.get('costo_usd', '')} |")
        review = [(c['id'], item) for c in queue['cards'] for item in c.get('revisar_humano', [])]
        if review:
            lines += ['', '## Revisar a mano en el PR', '']
            lines += [f'- `{cid}`: {item}' for cid, item in review]
        findings = [(c['id'], item) for c in queue['cards'] for item in c.get('hallazgos', [])]
        if findings:
            lines += ['', '## Hallazgos incidentales', '']
            lines += [f'- `{cid}`: {item}' for cid, item in findings]
        blocked = [c for c in queue['cards'] if c['estado'] in ('BLOCKED', 'REJECTED')]
        if blocked:
            lines += ['', '## Pendiente de tu decisión', '']
            lines += [f"- `{c['id']}` ({c['estado']}): {c.get('motivo', '')}" for c in blocked]
        (self.round_dir / 'ESTADO.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    def _claude(self, prompt, extra_args, timeout):
        cmd = [
            self.claude, '-p', '--model', self.model, '--output-format', 'json',
            '--settings', str(AGENT_SETTINGS), '--max-budget-usd', MAX_BUDGET_USD, *extra_args,
        ]
        try:
            result = subprocess.run(
                cmd, cwd=BASE_DIR, input=prompt, capture_output=True, text=True,
                timeout=timeout, env=self._env(), encoding='utf-8', errors='replace',
            )
        except subprocess.TimeoutExpired:
            return {'is_error': True, 'result': f'timeout de {timeout}s'}
        try:
            payload = json.loads(result.stdout)
        except ValueError:
            return {'is_error': True, 'result': (result.stdout + result.stderr)[-2000:]}
        if isinstance(payload, list):  # algunos formatos devuelven la lista de eventos
            payload = next((e for e in reversed(payload) if e.get('type') == 'result'), {})
        return payload

    def _changed_files(self):
        tracked = self._git('diff', '--name-only', 'HEAD').stdout.splitlines()
        untracked = self._git('ls-files', '--others', '--exclude-standard').stdout.splitlines()
        return sorted({path for path in tracked + untracked if path})

    def _scope_violations(self, card):
        files = self._changed_files()
        allowed_extra = tuple(card.get('rutas_permitidas_extra', []))
        violations = [
            f'ruta prohibida: {path}' for path in files
            if path.startswith(FORBIDDEN_PATHS) and not path.startswith(allowed_extra or ('\0',))
        ]
        if not card.get('permite_migracion'):
            violations += [f'migración no autorizada por el spec: {p}' for p in files if '/migrations/' in p]
        diff = self._git('diff', 'HEAD', '--', 'requirements.txt', 'requirements-dev.txt').stdout
        allowed_deps = {d.lower() for d in card.get('deps_permitidas', [])}
        removed = {m.group(1).lower() for m in re.finditer(r'^-([A-Za-z0-9_.\-]+)', diff, re.M)}
        for match in re.finditer(r'^\+([A-Za-z0-9_.\-]+)\s*[=<>~!]', diff, re.M):
            name = match.group(1).lower()
            if name not in removed and name not in allowed_deps:
                violations.append(f'dependencia nueva no autorizada: {name}')
        return violations

    def _run_gate(self, card):
        result = subprocess.run(
            [sys.executable, str(GATEKEEPER), '--strict'], cwd=BASE_DIR, capture_output=True,
            text=True, stdin=subprocess.DEVNULL, timeout=1500, encoding='utf-8', errors='replace',
        )
        try:
            gate = json.loads(result.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            gate = {'passed': False, 'gates': {}, 'detail': (result.stdout + result.stderr)[-2000:]}
        red = None
        if card.get('red_tests'):
            red_run = subprocess.run(
                [sys.executable, str(GATEKEEPER), '--red-check', *card['red_tests']], cwd=BASE_DIR,
                capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=600,
                encoding='utf-8', errors='replace',
            )
            try:
                red = json.loads(red_run.stdout.strip().splitlines()[-1])
            except (ValueError, IndexError):
                red = {'red_confirmed': False, 'detail': (red_run.stdout + red_run.stderr)[-1500:]}
        return gate, red

    # --- turnos -----------------------------------------------------------
    def run_planificador(self):
        queue = self._load_queue()
        branch = self._git('branch', '--show-current').stdout.strip()
        if not branch.startswith('agent/') or branch != queue['rama']:
            raise PreconditionError(f"Rama actual `{branch}`; la ronda exige `{queue['rama']}`.")
        dirty = self._git('status', '--porcelain').stdout.strip()
        if dirty:
            raise PreconditionError(f'El árbol de trabajo no está limpio:\n{dirty}')
        card = next((c for c in queue['cards'] if c['estado'] == 'TODO'), None)
        if card is None:
            return {'queue_empty': True}
        return {'queue_empty': False, 'card': card['id'], 'maestra': card['maestra']}

    def run_dev_tester(self, card_id, attempt):
        queue = self._load_queue()
        card = self._card(queue, card_id)
        cierre = self.round_dir / '_CIERRE.md'
        if attempt == 1 or card_id not in self._sessions:
            prompt = '\n\n'.join([
                (WORKFLOWS_DIR / '02_dev_tester.md').read_text(encoding='utf-8'),
                f"# Card a ejecutar: {card['id']} (card maestra {card['maestra']})",
                (self.round_dir / card['spec']).read_text(encoding='utf-8'),
                *([cierre.read_text(encoding='utf-8')] if cierre.is_file() else []),
            ])
            extra = ['--permission-mode', 'acceptEdits']
        else:
            prompt = (
                f"El gate determinista rechazó tu trabajo en {card_id} (intento {attempt - 1} de "
                f"{MAX_REPAIR_ATTEMPTS}). Diagnostica con este detalle, corrige y vuelve a cerrar con la "
                f"línea RESULTADO. No debilites ni borres tests para pasar.\n\n"
                f"{_trim(self._last_failure.get(card_id, ''))}"
            )
            extra = ['--permission-mode', 'acceptEdits', '--resume', self._sessions[card_id]]

        response = self._claude(prompt, extra, DEV_TIMEOUT_S)
        if response.get('session_id'):
            self._sessions[card_id] = response['session_id']
        self._costs[card_id] = self._costs.get(card_id, 0) + (response.get('total_cost_usd') or 0)
        text = response.get('result') or ''

        if response.get('is_error'):
            return {'passed': False, 'abort': True, 'motivo': f'la sesión del agente falló: {_trim(text, 800)}'}
        blocked = re.search(r'RESULTADO:\s*BLOQUEADA\s*[—\-:]*\s*(.*)', text)
        if blocked:
            return {'passed': False, 'abort': True, 'motivo': blocked.group(1).strip()[:600],
                    'agent_report': _trim(text, 3000)}

        gate, red = self._run_gate(card)
        violations = self._scope_violations(card)
        nothing_changed = not self._changed_files()
        passed = (
            gate.get('passed') is True and not violations and not nothing_changed
            and (red is None or red.get('red_confirmed') is True)
        )
        if not passed:
            self._last_failure[card_id] = {
                'gates_fallidos': {k: v for k, v in gate.get('gates', {}).items() if not v.get('passed')},
                'gate_detail': gate.get('detail', ''),
                'rojo': red if red and not red.get('red_confirmed') else 'ok',
                'alcance': violations,
                'sin_cambios': nothing_changed,
            }
        return {
            'passed': passed,
            'gatekeeper_json': gate,
            'red_check': red,
            'scope_violations': violations,
            'agent_report': _trim(text, 3000),
            'motivo': '' if passed else _trim(self._last_failure[card_id], 1500),
        }

    def run_validador(self, card_id, dev_result):
        queue = self._load_queue()
        card = self._card(queue, card_id)
        prompt = '\n\n'.join([
            (WORKFLOWS_DIR / '03_validador.md').read_text(encoding='utf-8'),
            f"# Card a validar: {card['id']} (card maestra {card['maestra']})",
            (self.round_dir / card['spec']).read_text(encoding='utf-8'),
            '# Informe del dev/tester\n' + dev_result.get('agent_report', ''),
            '# Gate determinista (ya verificado por el orquestador)\n' + _trim({
                'gatekeeper': dev_result.get('gatekeeper_json'), 'red_check': dev_result.get('red_check'),
            }, 3000),
        ])
        response = self._claude(prompt, [
            '--permission-mode', 'dontAsk',
            '--disallowedTools', 'Edit,Write,NotebookEdit',
            '--json-schema', json.dumps(VALIDATOR_SCHEMA),
        ], VALIDATOR_TIMEOUT_S)
        self._costs[card_id] = self._costs.get(card_id, 0) + (response.get('total_cost_usd') or 0)
        out = response.get('structured_output')
        if not out:
            return {'verdict': 'REJECT',
                    'motivo': 'el validador no devolvió un veredicto: ' + _trim(response.get('result') or '', 600)}
        if out['veredicto'] != 'APPROVE':
            return {'verdict': 'REJECT', 'motivo': out['motivo'], 'hallazgos': out['hallazgos']}

        # --- cierre determinista ---
        gates = dev_result['gatekeeper_json']['gates']
        base = json.loads(BASELINE_PATH.read_text(encoding='utf-8')) if BASELINE_PATH.is_file() else {}
        new_cov = gates['coverage']['percent']
        BASELINE_PATH.write_text(json.dumps({
            'coverage': {k: max(v, base.get('coverage', {}).get(k, 0)) for k, v in new_cov.items()},
            'bandit_medium_high': min(gates['bandit']['medium_high'],
                                      base.get('bandit_medium_high', gates['bandit']['medium_high'])),
        }, indent=2) + '\n', encoding='utf-8')

        card.update({
            'estado': 'DONE',
            'costo_usd': round(self._costs.get(card_id, 0), 2),
            'tests': gates['tests']['total'],
            'hallazgos': out['hallazgos'],
            'revisar_humano': out['revisar_humano'],
        })
        self._save_queue(queue)
        subject = f"{card['id']} ({card['maestra']}): {out['commit_subject']}"[:100]
        body = out['commit_body'].strip() + '\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>'
        self._git('add', '-A', check=True)
        self._git('commit', '-m', subject, '-m', body, check=True)
        commit = self._git('rev-parse', '--short', 'HEAD').stdout.strip()
        pushed = self._push(queue['rama'])
        return {'verdict': 'APPROVE', 'commit': commit, 'pushed': pushed, 'subject': subject,
                'revisar_humano': out['revisar_humano'], 'hallazgos': out['hallazgos']}

    def _push(self, branch):
        if not self.push or not branch.startswith('agent/'):
            return False
        return self._git('push', '-u', 'origin', branch).returncode == 0

    def on_card_failed(self, card_id, status, detail):
        """Deja el árbol limpio para la card siguiente sin perder el trabajo:
        parche en scripts/output/ + `git stash` recuperable."""
        if self._git('status', '--porcelain').stdout.strip():
            self._git('add', '-A')
            patch = self._git('diff', '--cached', 'HEAD').stdout
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            (OUTPUT_DIR / f'{card_id}_{status}_{int(time.time())}.patch').write_text(patch, encoding='utf-8')
            self._git('stash', 'push', '-u', '-m', f'{card_id} {status} (orchestrate.py)')
        queue = self._load_queue()
        card = self._card(queue, card_id)
        card.update({
            'estado': status,
            'motivo': (detail.get('motivo') or '')[:1500],
            'costo_usd': round(self._costs.get(card_id, 0), 2),
        })
        self._save_queue(queue)
        self._git('add', str(self.queue_path), str(self.round_dir / 'ESTADO.md'))
        self._git('commit', '-m', f'agente: {card_id} {status}', '-m',
                  'El trabajo parcial quedó en git stash y en scripts/output/.')
        self._push(queue['rama'])


def _jsonl_logger(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    def log_fn(entry: dict):
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'ts': time.time(), **entry}) + '\n')

    return log_fn


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-cards', type=int, default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--ronda', help='ruta a cola.json (p. ej. docs/agente/ronda4/cola.json): '
                                        'ejecuta con agente real (claude -p)')
    parser.add_argument('--model', default=DEFAULT_MODEL)
    parser.add_argument('--max-failures', type=int, default=2,
                        help='cards BLOCKED/REJECTED toleradas antes de detener la ronda')
    parser.add_argument('--no-push', action='store_true')
    args = parser.parse_args(argv)

    log_path = OUTPUT_DIR / f'orchestrator_{int(time.time())}.jsonl'
    log_fn = _jsonl_logger(log_path)

    if args.dry_run:
        runner = DryRunAgentRunner()
    elif args.ronda:
        runner = ClaudeCliRunner(args.ronda, model=args.model, push=not args.no_push)
    else:
        runner = NotWiredAgentRunner()

    try:
        outcomes = run_pipeline(runner, max_cards=args.max_cards, log_fn=log_fn,
                                max_failures=args.max_failures)
    except PreconditionError as exc:
        print(f'No se puede correr la ronda: {exc}', file=sys.stderr)
        return 2

    for outcome in outcomes:
        print(f"{outcome.card}: {outcome.status} (intentos={outcome.attempts})")
    print(f"Log: {log_path}")

    return 0 if all(o.status == 'DONE' for o in outcomes) else 1


if __name__ == '__main__':
    sys.exit(main())
