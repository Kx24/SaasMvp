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
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / 'scripts' / 'output'
MAX_REPAIR_ATTEMPTS = 3


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


def run_pipeline(runner: AgentRunner, max_cards: Optional[int] = None, log_fn=None) -> list:
    outcomes = []

    while max_cards is None or len(outcomes) < max_cards:
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
            if dev_result.get('passed'):
                break

        if not dev_result.get('passed'):
            outcomes.append(CardOutcome(card=card, status='BLOCKED', attempts=attempt, detail=dev_result))
            if log_fn:
                log_fn({'turn': 'orchestrator', 'card': card, 'status': 'BLOCKED', 'attempts': attempt})
            continue

        verdict = runner.run_validador(card, dev_result)
        if log_fn:
            log_fn({'turn': 'validador', 'card': card, **verdict})

        status = 'DONE' if verdict.get('verdict') == 'APPROVE' else 'REJECTED'
        outcomes.append(CardOutcome(card=card, status=status, attempts=attempt, detail=verdict))

    return outcomes


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
    args = parser.parse_args(argv)

    log_path = OUTPUT_DIR / f'orchestrator_{int(time.time())}.jsonl'
    log_fn = _jsonl_logger(log_path)

    runner = DryRunAgentRunner() if args.dry_run else NotWiredAgentRunner()

    outcomes = run_pipeline(runner, max_cards=args.max_cards, log_fn=log_fn)

    for outcome in outcomes:
        print(f"{outcome.card}: {outcome.status} (intentos={outcome.attempts})")
    print(f"Log: {log_path}")

    return 0 if all(o.status == 'DONE' for o in outcomes) else 1


if __name__ == '__main__':
    sys.exit(main())
