"""Une el veredicto del verificador con la planilla de tweets, de forma determinista."""
from __future__ import annotations

from typing import List, Tuple

ESTADOS = ("OK", "REVISAR", "ERROR")


def fusionar(tweets: dict, veredictos: List[dict]) -> Tuple[dict, List[str]]:
    """Devuelve (tweets con 'verificacion' en cada item, lista de problemas).

    - Un item sin veredicto queda REVISAR (nunca se asume OK por omision).
    - Un estado desconocido se trata como REVISAR.
    - Un veredicto para un id que no existe se informa como problema.
    """
    problemas: List[str] = []
    por_id = {}
    for v in veredictos:
        if not isinstance(v, dict) or "id" not in v:
            problemas.append(f"veredicto mal formado: {v!r}")
            continue
        por_id[v["id"]] = v

    ids = {it.get("id") for it in tweets.get("items", [])}
    for extra in sorted(set(por_id) - ids):
        problemas.append(f"el verificador opino sobre un id que no existe: {extra}")

    for it in tweets.get("items", []):
        v = por_id.get(it.get("id"))
        if v is None:
            it["verificacion"] = {"estado": "REVISAR", "detalle": "el verificador no reviso este item"}
            problemas.append(f"{it.get('id')}: sin veredicto del verificador")
            continue
        estado = v.get("estado")
        if estado not in ESTADOS:
            problemas.append(f"{it.get('id')}: estado desconocido {estado!r}, se trata como REVISAR")
            estado = "REVISAR"
        it["verificacion"] = {"estado": estado, "detalle": str(v.get("detalle", ""))}
    return tweets, problemas
