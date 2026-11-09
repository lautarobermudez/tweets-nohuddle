"""Plan del dia: la mezcla de publicaciones y sus horarios, decididos por codigo (no por el modelo).

El agente solo completa los textos. Asi la estructura es siempre la misma y no consume tokens de razonamiento.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from . import fuentes as nh_fuentes

AR = timedelta(hours=-3)


def _min(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _hhmm(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def partidos_de_hoy(partidos: List[dict], hoy: date, liga: str = "NFL") -> List[int]:
    """Minutos del dia (hora de Argentina) de los partidos de `liga` que se juegan hoy y todavia no terminaron."""
    out = []
    for p in partidos:
        if p.get("liga") != liga or p.get("terminado"):
            continue
        d = nh_fuentes._hora_ar(p.get("fecha_utc", ""))
        if d is not None and d.date() == hoy:
            out.append(d.hour * 60 + d.minute)
    return sorted(out)


def _separar(horas: List[int], separacion: int, tope: int) -> List[int]:
    """Garantiza `separacion` minutos entre publicaciones consecutivas (empuja hacia adelante, sin pasarse del tope)."""
    orden = sorted(range(len(horas)), key=lambda i: horas[i])
    out = list(horas)
    previo = None
    for i in orden:
        if previo is not None and out[i] - previo < separacion:
            out[i] = previo + separacion
        out[i] = min(out[i], tope)
        previo = out[i]
    return out


def armar(reglas: dict, partidos: List[dict], ahora_utc: Optional[datetime] = None, todo_el_dia: bool = False) -> dict:
    """Devuelve el esqueleto de tweets.json: un slot por publicacion, con textos y fuentes vacios para completar.

    - La primera 'previa' de la NFL se mueve a `minutos_antes_del_partido` antes del primer partido de hoy.
    - Los slots cuya hora ya paso se saltean (salvo todo_el_dia=True).
    - Se respeta la separacion minima entre publicaciones y la ventana horaria.
    """
    cfg = reglas["plan_diario"]
    ahora_utc = ahora_utc or datetime.now(timezone.utc)
    ar = ahora_utc + AR
    hoy = ar.date()
    ventana = reglas["ventana_horaria"]
    tope = _min(ventana["hasta"])
    slots = [dict(s) for s in cfg["slots"]]
    horas = [_min(s["hora"]) for s in slots]

    juegos = partidos_de_hoy(partidos, hoy, "NFL")
    if juegos:
        for i, s in enumerate(slots):
            if s["categoria"] == "previa" and s["liga"] == "NFL":
                horas[i] = max(juegos[0] - cfg["minutos_antes_del_partido"], _min(cfg["hora_minima_previa"]))
                break

    horas = _separar(horas, reglas["separacion_minima_minutos"], tope)
    ahora_min = ar.hour * 60 + ar.minute + reglas["separacion_minima_minutos"]

    items = []
    n_t = n_h = 0
    for s, h in sorted(zip(slots, horas), key=lambda x: x[1]):
        if not todo_el_dia and h < ahora_min:
            continue
        if s["tipo"] == "hilo":
            n_h += 1
            id_ = f"h{n_h}"
        else:
            n_t += 1
            id_ = f"t{n_t}"
        items.append({
            "id": id_, "tipo": s["tipo"], "categoria": s["categoria"], "liga": s["liga"], "hora": _hhmm(h),
            "prioridad": s.get("prioridad", "opcional"), "textos": [], "fuentes": [],
        })
    return {"fecha": hoy.isoformat(), "agenda": [], "items": items}


def limpiar(tweets: dict) -> tuple:
    """Saca los slots que el agente no completo. Devuelve (tweets, ids_descartados)."""
    descartados = [i.get("id", "?") for i in tweets.get("items", []) if not any((t or "").strip() for t in i.get("textos", []))]
    tweets["items"] = [i for i in tweets.get("items", []) if i.get("id") not in descartados]
    return tweets, descartados
