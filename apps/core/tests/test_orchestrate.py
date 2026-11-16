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


class UnattendedRoundRulesTestCase(SimpleTestCase):
    """Reglas de la ronda desatendida (ronda 4): corte por fallos, aborto y hook."""

    def test_abort_skips_remaining_repair_attempts(self):
        runner = ScriptedRunner(
            planificador_plan=[{'queue_empty': False, 'card': 'BOLT-01'}, {'queue_empty': True}],
            dev_tester_results=[{'passed': False, 'abort': True, 'motivo': 'falta una decision'}],
        )

        outcomes = run_pipeline(runner)

        self.assertEqual(runner.dev_tester_calls, 1)
        self.assertEqual(outcomes[0].status, 'BLOCKED')
        self.assertEqual(runner.validador_calls, 0)

    def test_max_failures_stops_the_round(self):
        runner = ScriptedRunner(
            planificador_plan=[{'queue_empty': False, 'card': 'BOLT-01'}],
            dev_tester_results=[{'passed': False, 'abort': True}],
        )

        outcomes = run_pipeline(runner, max_failures=2)

        self.assertEqual(len(outcomes), 2)
        self.assertEqual(runner.planificador_calls, 2)

    def test_failure_hook_receives_blocked_and_rejected_cards(self):
        calls = []

        class HookRunner(ScriptedRunner):
            def on_card_failed(self, card, status, detail):
                calls.append((card, status))

        runner = HookRunner(
            planificador_plan=[
                {'queue_empty': False, 'card': 'BOLT-01'},
                {'queue_empty': False, 'card': 'BOLT-02'},
                {'queue_empty': True},
            ],
            dev_tester_results=[{'passed': False, 'abort': True}, {'passed': True}],
            validador_result={'verdict': 'REJECT'},
        )

        run_pipeline(runner)

        self.assertEqual(calls, [('BOLT-01', 'BLOCKED'), ('BOLT-02', 'REJECTED')])


class QuotaRetryTests(SimpleTestCase):
    """La cuota agotada de la cuenta no es un fallo de la card: se espera y se reintenta."""

    def _runner(self, responses):
        from orchestrate import ClaudeCliRunner

        runner = ClaudeCliRunner.__new__(ClaudeCliRunner)  # sin exigir el ejecutable `claude`
        prompts = []

        def fake_once(prompt, extra_args, timeout):
            prompts.append(prompt)
            return responses[min(len(prompts) - 1, len(responses) - 1)]

        runner._claude_once = fake_once
        return runner, prompts

    def test_quota_message_waits_and_retries_with_resume_note(self):
        from unittest import mock

        import orchestrate

        quota = {'is_error': True, 'result': "You've hit your 5-hour limit · resets 2:10pm (America/Santiago)"}
        runner, prompts = self._runner([quota, quota, {'result': 'RESULTADO: OK', 'session_id': 's1'}])

        with mock.patch.object(orchestrate.time, 'sleep') as sleep:
            payload = runner._claude('haz la card', [], 10)

        self.assertEqual(payload['session_id'], 's1')
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(len(prompts), 3)
        self.assertFalse(prompts[0].startswith(orchestrate.QUOTA_RESUME_NOTE))
        self.assertTrue(prompts[1].startswith(orchestrate.QUOTA_RESUME_NOTE))
        self.assertEqual(prompts[2].count(orchestrate.QUOTA_RESUME_NOTE), 1)

    def test_long_report_quoting_the_phrase_is_not_a_quota_error(self):
        from unittest import mock

        import orchestrate

        report = {'result': "informe " * 60 + "el log decía: You've hit your 5-hour limit"}
        runner, prompts = self._runner([report])

        with mock.patch.object(orchestrate.time, 'sleep') as sleep:
            payload = runner._claude('haz la card', [], 10)

        self.assertIs(payload, report)
        sleep.assert_not_called()
        self.assertEqual(len(prompts), 1)

    def test_gives_up_after_max_wait(self):
        from unittest import mock

        import orchestrate

        quota = {'is_error': True, 'result': "You've hit your 5-hour limit"}
        runner, prompts = self._runner([quota])

        with mock.patch.object(orchestrate.time, 'sleep'), \
                mock.patch.object(orchestrate, 'QUOTA_MAX_WAIT_S', orchestrate.QUOTA_POLL_S * 2):
            payload = runner._claude('haz la card', [], 10)

        self.assertIs(payload, quota)
        self.assertEqual(len(prompts), 3)
