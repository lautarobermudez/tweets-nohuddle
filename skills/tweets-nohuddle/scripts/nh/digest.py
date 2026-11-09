"""Resumen compacto para el agente. Cada historia lleva un ID corto (N1, C3...): el agente cita el ID y el script resuelve medio y URL.

Asi el modelo no escribe URLs (tokens de salida caros) y no puede equivocarse ni inventarlas.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from . import tiempo

PREFIJO = {"NFL": "N", "College": "C"}
MEDIOS_POR_ID = 2  # cuantos medios distintos se guardan como referencia interna de cada historia


def _corto(txt: str, n: int) -> str:
    txt = " ".join((txt or "").split())
    return txt if len(txt) <= n else txt[: n - 1].rstrip() + "…"


def _fuentes_de(historia: dict) -> List[dict]:
    """Hasta MEDIOS_POR_ID medios distintos (tier A primero) con su URL."""
    orden = sorted(historia["items"], key=lambda i: (i["tier"] != "A", not i.get("resumen"), -len(i.get("resumen", ""))))
    out, vistos = [], set()
    for it in orden:
        if it["medio"] not in vistos:
            vistos.add(it["medio"])
            out.append({"medio": it["medio"], "url": it["link"]})
        if len(out) == MEDIOS_POR_ID:
            break
    return out


def construir(res: dict, reglas: dict, ahora: Optional[datetime] = None) -> Tuple[str, Dict[str, dict]]:
    """Devuelve (markdown del digest, indice {id: {titulo, medios, fuentes}})."""
    cfg = reglas["digest"]
    ahora = ahora or datetime.now(timezone.utc)
    ar = tiempo.ahora_ar(ahora)
    indice: Dict[str, dict] = {}
    medios_leidos = sorted({i["medio"] for h in res["historias"] for i in h["items"]})
    L = [f"# Digest {ar:%Y-%m-%d} ({tiempo.DIAS_ES[ar.weekday()]}) - hora de Argentina",
         f"Medios leidos: {', '.join(medios_leidos) or 'ninguno'}."]
    if res["fuentes_error"]:
        L.append("No respondieron: " + ", ".join(sorted({e["medio"] for e in res["fuentes_error"]})) + ".")
    L.append("Cada historia tiene un ID (N=NFL, C=College); [n] = cuantos medios la cubren (mas = mas importante).")

    for liga, tope in (("NFL", cfg["max_historias_nfl"]), ("College", cfg["max_historias_college"])):
        L.append(f"\n## {liga}")
        for n, h in enumerate([h for h in res["historias"] if h["liga"] == liga][:tope], 1):
            id_ = f"{PREFIJO[liga]}{n}"
            fuentes = _fuentes_de(h)
            mejor = max(h["items"], key=lambda i: len(i.get("resumen", "")))
            resumen = _corto(mejor.get("resumen", ""), cfg["max_resumen_chars"])
            if resumen.lower().startswith(h["titulo_guia"].lower()[:40]):
                resumen = ""
            indice[id_] = {"titulo": h["titulo_guia"], "medios": h["medios"], "fuentes": fuentes}
            L.append(f"{id_} [{h['n_medios']}] {_corto(h['titulo_guia'], 140)}" + (f" - {resumen}" if resumen else ""))

    L.append("\n## Partidos (hora de Argentina)")
    horas = cfg["horas_partidos"]
    for liga in ("NFL", "College"):
        proximos, terminados = [], []
        for p in res["partidos"]:
            if p["liga"] != liga:
                continue
            d = tiempo.hora_ar(p["fecha_utc"])
            if d is None:
                continue
            delta = (d - ar).total_seconds() / 3600
            if p["terminado"] and -horas <= delta <= 0:
                marc = " vs ".join(f"{e['equipo']} {e['puntos']}" for e in p["equipos"])
                terminados.append((d, f"{liga}: {marc} (final, {tiempo.DIAS_ES[d.weekday()]} {d:%d/%m})"))
            elif not p["terminado"] and 0 <= delta <= horas:
                proximos.append((d, f"{liga}: {p['nombre']} ({tiempo.DIAS_ES[d.weekday()]} {d:%d/%m} {d:%H:%M})"))
        proximos.sort(key=lambda x: x[0])
        terminados.sort(key=lambda x: x[0], reverse=True)  # los mas recientes primero
        cupo = max(cfg["max_partidos_por_liga"] - len(proximos), 6)  # los proximos van siempre
        L += [f"- {t}" for _, t in (proximos + terminados[:cupo])[: cfg["max_partidos_por_liga"] + 6]]
    return "\n".join(L) + "\n", indice
