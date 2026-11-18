"""
Ejecución del gatekeeper como subproceso para `apps/core/tests/test_gatekeeper.py` (TOOL-08).

Vive fuera de los archivos de test a propósito: es la lógica de tope de tiempo y de
mensaje de fallo, y los tests de `test_gatekeeper_runtime` la verifican.
"""
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GATEKEEPER_PATH = BASE_DIR / 'scripts' / 'gatekeeper.py'

DEFAULT_TIMEOUT_S = 900


def resolve_timeout():
    """Tope del gate en segundos; sobrescribible con GATEKEEPER_TEST_TIMEOUT_S (entero)."""
    raw = os.environ.get('GATEKEEPER_TEST_TIMEOUT_S')
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return DEFAULT_TIMEOUT_S


GATEKEEPER_TEST_TIMEOUT_S = resolve_timeout()


def run_gatekeeper(timeout=GATEKEEPER_TEST_TIMEOUT_S):
    try:
        return subprocess.run(
            [sys.executable, str(GATEKEEPER_PATH)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"El gatekeeper no terminó en {timeout} s (suite completa con la máquina "
            "cargada). Sube el tope con la variable de entorno GATEKEEPER_TEST_TIMEOUT_S."
        ) from None
