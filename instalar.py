#!/usr/bin/env python3
"""Instala la skill /tweets-nohuddle en Claude Code. Un solo comando, sin dependencias (Python 3.8+).

    python instalar.py            # instala en ~/.claude/skills y prepara la carpeta de trabajo
    python instalar.py --actualizar   # actualiza una instalacion existente (deja la anterior como respaldo)

Funciona igual en Windows, Mac y Linux.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ORIGEN = RAIZ / "skills" / "tweets-nohuddle"
NOMBRE = "tweets-nohuddle"


def instalar(destino_skills: Path, actualizar: bool = False) -> Path:
    """Copia la skill. Si ya existe: sin --actualizar se frena; con --actualizar deja un unico respaldo '.anterior'."""
    if not (ORIGEN / "SKILL.md").exists():
        raise SystemExit(f"No encuentro la skill en {ORIGEN}. Corre este script desde la carpeta del proyecto.")
    destino = destino_skills / NOMBRE
    if destino.exists():
        if not actualizar:
            raise SystemExit(f"Ya esta instalada en {destino}. Usa --actualizar para reemplazarla.")
        # El respaldo va FUERA de la carpeta de skills: si quedara adentro, Claude Code lo cargaria como una skill duplicada.
        respaldo = destino_skills.parent / "skills-respaldo" / NOMBRE
        if respaldo.exists():
            shutil.rmtree(respaldo)  # un solo respaldo rotativo
        respaldo.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(destino), str(respaldo))
        print(f"Version anterior guardada en {respaldo}")
    destino_skills.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ORIGEN, destino, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return destino


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Instala la skill /tweets-nohuddle")
    p.add_argument("--actualizar", action="store_true")
    p.add_argument("--destino", help="carpeta de skills (por defecto ~/.claude/skills)")
    a = p.parse_args(argv)

    destino_skills = Path(a.destino).expanduser() if a.destino else Path.home() / ".claude" / "skills"
    destino = instalar(destino_skills, a.actualizar)
    print(f"Skill instalada en {destino}")

    print("\nChequeando que todo este listo...")
    r = subprocess.run([sys.executable, str(destino / "scripts" / "tweets.py"), "doctor", "--red"])
    if r.returncode != 0:
        print("\nHay algo para resolver (mira las lineas que dicen FALLA).")
        return 2
    print("\nListo. Abri Claude Code y escribi:  /tweets-nohuddle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
