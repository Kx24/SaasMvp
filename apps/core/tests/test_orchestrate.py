"""
Tests de la máquina de estados del orquestador (docs/kanban_agente.md,
PILOT-03). `orchestrate.py` vive en la raíz del repo (no es una app
Django) -- se importa directo porque `manage.py test` corre con la raíz
del repo en `sys.path`.

El orquestador NO invoca un agente real acá: `run_pipeline()` recibe un
`AgentRunner` (protocolo con 3 métodos: planificador/dev_tester/validador)
y solo secuencia turnos, cuenta reintentos y decide BLOCKED/DONE/REJECTED.
Conectar un agente real (CLI de Claude Code, API) es un paso de
integración aparte -- estos tests usan un runner de prueba (`ScriptedRunner`)
que devuelve resultados prefijados, sin costo ni red.
"""
from django.test import SimpleTestCase

from orchestrate import MAX_REPAIR_ATTEMPTS, run_pipeline


class ScriptedRunner:
    """Runner de prueba: devuelve resultados prefijados en orden, sin agente real."""

    def __init__(self, planificador_plan, dev_tester_results, validador_result=None):
        self.planificador_plan = planificador_plan
        self.dev_tester_results = dev_tester_results
        self.validador_result = validador_result or {'verdict': 'APPROVE'}
        self.planificador_calls = 0
        self.dev_tester_calls = 0
        self.validador_calls = 0

    def run_planificador(self):
        self.planificador_calls += 1
        idx = min(self.planificador_calls - 1, len(self.planificador_plan) - 1)
        return self.planificador_plan[idx]

    def run_dev_tester(self, card, attempt):
        self.dev_tester_calls += 1
        idx = min(self.dev_tester_calls - 1, len(self.dev_tester_results) - 1)
        return self.dev_tester_results[idx]

    def run_validador(self, card, dev_tester_result):
        self.validador_calls += 1
        return self.validador_result


class HappyPathTestCase(SimpleTestCase):
    def test_single_card_passes_first_try_and_gets_approved(self):
        runner = ScriptedRunner(
            planificador_plan=[
                {'queue_empty': False, 'card': 'BOLT-99'},
                {'queue_empty': True},
            ],
            dev_tester_results=[{'passed': True}],
        )

        outcomes = run_pipeline(runner)

        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0].card, 'BOLT-99')
        self.assertEqual(outcomes[0].status, 'DONE')
        self.assertEqual(outcomes[0].attempts, 1)
        self.assertEqual(runner.dev_tester_calls, 1)
        self.assertEqual(runner.validador_calls, 1)


class RepairRetryTestCase(SimpleTestCase):
    def test_two_failures_then_success_reaches_done_with_three_attempts(self):
        runner = ScriptedRunner(
            planificador_plan=[
                {'queue_empty': False, 'card': 'BOLT-99'},
                {'queue_empty': True},
            ],
            dev_tester_results=[
                {'passed': False},
                {'passed': False},
                {'passed': True},
            ],
        )

        outcomes = run_pipeline(runner)

        self.assertEqual(outcomes[0].status, 'DONE')
        self.assertEqual(outcomes[0].attempts, 3)
        self.assertEqual(runner.dev_tester_calls, 3)
        self.assertEqual(runner.validador_calls, 1)


class RepairExhaustionTestCase(SimpleTestCase):
    def test_repeated_failures_block_without_a_fourth_attempt(self):
        runner = ScriptedRunner(
            planificador_plan=[
                {'queue_empty': False, 'card': 'BOLT-99'},
                {'queue_empty': True},
            ],
            # Un solo resultado, siempre fallido -- el runner lo repetiría
            # indefinidamente si el orquestador lo dejara. El límite real
            # está en run_pipeline(), no en el stub.
            dev_tester_results=[{'passed': False}],
        )

        outcomes = run_pipeline(runner)

        self.assertEqual(outcomes[0].status, 'BLOCKED')
        self.assertEqual(outcomes[0].attempts, MAX_REPAIR_ATTEMPTS)
        self.assertEqual(runner.dev_tester_calls, MAX_REPAIR_ATTEMPTS)
        # Card bloqueada: el validador nunca corre sobre un gate en rojo.
        self.assertEqual(runner.validador_calls, 0)


class QueueEmptyTestCase(SimpleTestCase):
    def test_empty_queue_produces_no_outcomes(self):
        runner = ScriptedRunner(
            planificador_plan=[{'queue_empty': True}],
            dev_tester_results=[],
        )

        outcomes = run_pipeline(runner)

        self.assertEqual(outcomes, [])
        self.assertEqual(runner.dev_tester_calls, 0)


class MaxCardsTestCase(SimpleTestCase):
    def test_max_cards_stops_the_loop_early(self):
        runner = ScriptedRunner(
            planificador_plan=[
                {'queue_empty': False, 'card': 'BOLT-01'},
                {'queue_empty': False, 'card': 'BOLT-02'},
                {'queue_empty': False, 'card': 'BOLT-03'},
            ],
            dev_tester_results=[{'passed': True}],
        )

        outcomes = run_pipeline(runner, max_cards=2)

        self.assertEqual(len(outcomes), 2)
        self.assertEqual(runner.planificador_calls, 2)
