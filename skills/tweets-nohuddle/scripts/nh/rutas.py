"""Rutas y configuracion. Solo biblioteca estandar (corre en cualquier Python 3.8+)."""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# .../tweets-nohuddle/scripts/nh/rutas.py -> parents[2] = carpeta de la skill
SKILL_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = SKILL_DIR / "config"


def hoy_ar() -> date:
    """Fecha de hoy en Argentina (UTC-3), sin importar la zona horaria de la maquina."""
    return (datetime.now(timezone.utc) - timedelta(hours=3)).date()


def work_dir() -> Path:
    """Carpeta de trabajo (salidas e historial). Se puede cambiar con NH_TWEETS_DIR."""
    env = os.environ.get("NH_TWEETS_DIR")
    return Path(env).expanduser() if env else Path.home() / "NoHuddle-Tweets"


def dia_dir(fecha: str) -> Path:
    return work_dir() / "salida" / fecha


def historial_path() -> Path:
    return work_dir() / "historial.json"


def cargar_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cargar_reglas() -> dict:
    return cargar_json(CONFIG_DIR / "reglas.json")


def cargar_fuentes() -> dict:
    return cargar_json(CONFIG_DIR / "fuentes.json")


def guardar_json(path: Path, datos) -> None:
    """Escritura atomica: nunca deja un archivo a medias si algo falla."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
