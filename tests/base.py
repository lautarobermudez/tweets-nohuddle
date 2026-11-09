"""Configuracion comun de los tests: rutas a la skill y a los fixtures."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SKILL = RAIZ / "skills" / "tweets-nohuddle"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SKILL / "scripts"))


def fixture(nombre: str) -> bytes:
    return (FIXTURES / nombre).read_bytes()


def tweets_ok() -> dict:
    return json.loads((FIXTURES / "tweets_ok.json").read_text(encoding="utf-8"))
