"""Memoria entre dias: guarda lo ya propuesto para no repetir y lo devuelve para comparar."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import List

from . import rutas


def cargar(path: Path = None) -> List[dict]:
    path = path or rutas.historial_path()
    if not path.exists():
        return []
    try:
        datos = rutas.cargar_json(path)
    except (ValueError, OSError):
        # Historial danado: no frenamos la corrida, pero lo dejamos asentado en un .bak.
        path.replace(path.with_suffix(".json.bak"))
        return []
    return datos if isinstance(datos, list) else []


def agregar(tweets: dict, path: Path = None) -> int:
    """Registra los textos de una corrida. Si ya habia una corrida de la misma fecha, la reemplaza (idempotente)."""
    path = path or rutas.historial_path()
    fecha = tweets["fecha"]
    existentes = [e for e in cargar(path) if e.get("fecha") != fecha]
    nuevos = []
    for it in tweets.get("items", []):
        for i, t in enumerate(it.get("textos", [])):
            nuevos.append({"fecha": fecha, "id": it.get("id", ""), "post": i + 1, "texto": t})
    rutas.guardar_json(path, existentes + nuevos)
    return len(nuevos)


def recientes(dias: int, hoy: date = None, path: Path = None) -> List[dict]:
    """Entradas de los ultimos `dias` dias, SIN contar la fecha de hoy (para poder re-correr el mismo dia)."""
    hoy = hoy or rutas.hoy_ar()
    desde = (hoy - timedelta(days=dias)).isoformat()
    hoy_s = hoy.isoformat()
    return [e for e in cargar(path) if desde <= e.get("fecha", "") < hoy_s]
