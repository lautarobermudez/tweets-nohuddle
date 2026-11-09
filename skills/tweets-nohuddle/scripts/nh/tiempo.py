"""Fechas y horas de Argentina (UTC-3) en un solo lugar."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

OFFSET_AR = timedelta(hours=-3)
DIAS_ES = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def ahora_ar(ahora_utc: Optional[datetime] = None) -> datetime:
    return (ahora_utc or datetime.now(timezone.utc)) + OFFSET_AR


def hoy_ar(ahora_utc: Optional[datetime] = None) -> date:
    """Fecha de hoy en Argentina, sin importar la zona horaria de la maquina."""
    return ahora_ar(ahora_utc).date()


def hora_ar(iso_utc: str) -> Optional[datetime]:
    """'2026-11-10T01:15Z' -> datetime en hora de Argentina (o None si no se puede leer)."""
    try:
        d = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d + OFFSET_AR
