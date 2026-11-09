"""Formato compacto de redaccion: el agente escribe una linea por publicacion y el script arma el tweets.json completo.

    # comentarios (se ignoran)
    t1 | N1,N4 | Texto del tweet
    t2@10:15 | N3 | Texto del tweet con otro horario
    h1 | N2 | Primer post del hilo
    + Segundo post
    + Tercer post
    t3 | - | Tweet que no sale de una historia del digest (resultado de un partido, por ejemplo)

Por que asi: el modelo solo escribe lo que es suyo (los textos). Los IDs de historia reemplazan las URLs, que son
tokens de salida caros y una fuente de errores. Las lineas '+' evitan separadores que choquen con las URLs.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

SLOT_RE = re.compile(r"^(?P<id>[A-Za-z]\d+)(?:@(?P<hora>([01]\d|2[0-3]):[0-5]\d))?$")
ESPN_MARCADORES = {
    "NFL": "https://www.espn.com/nfl/scoreboard",
    "College": "https://www.espn.com/college-football/scoreboard",
}


def parsear(contenido: str) -> Tuple[List[dict], List[str]]:
    """Texto -> (entradas, problemas). Una entrada: {id, hora, historias, posts, linea}."""
    entradas: List[dict] = []
    problemas: List[str] = []
    for n, crudo in enumerate(contenido.lstrip("﻿").splitlines(), 1):
        linea = crudo.strip()
        if not linea or linea.startswith("#"):
            continue
        if linea.startswith("+"):
            if not entradas:
                problemas.append(f"linea {n}: una linea '+' necesita una linea de publicacion antes")
                continue
            texto = linea[1:].strip()
            if texto:
                entradas[-1]["posts"].append(texto)
            continue
        partes = linea.split("|", 2)
        if len(partes) < 3:
            problemas.append(f"linea {n}: formato esperado 'id | historias | texto' (leí: {linea[:50]!r})")
            continue
        cabeza, historias, texto = (p.strip() for p in partes)
        m = SLOT_RE.match(cabeza)
        if not m:
            problemas.append(f"linea {n}: id de slot invalido {cabeza!r} (ej. t1, h1, t3@12:30)")
            continue
        ids = [] if historias in ("", "-") else [h.strip().upper() for h in historias.split(",") if h.strip()]
        entradas.append({"id": m.group("id").lower(), "hora": m.group("hora"), "historias": ids, "posts": [texto] if texto else [], "linea": n})
    return entradas, problemas


def aplicar(plan: dict, entradas: List[dict], indice: Dict[str, dict]) -> Tuple[dict, List[str]]:
    """Completa el plan con las entradas. Devuelve (tweets, problemas). No muta `plan`."""
    import copy

    tweets = copy.deepcopy(plan)
    por_id = {i["id"]: i for i in tweets["items"]}
    problemas: List[str] = []
    vistos = set()
    for e in entradas:
        if e["id"] in vistos:
            problemas.append(f"el slot {e['id']} aparece mas de una vez (linea {e['linea']})")
            continue
        vistos.add(e["id"])
        slot = por_id.get(e["id"])
        if slot is None:
            problemas.append(f"slot desconocido {e['id']!r} (linea {e['linea']}); los del plan son: {', '.join(por_id)}")
            continue
        slot["textos"] = e["posts"]
        if e["hora"]:
            slot["hora"] = e["hora"]
        # un tweet con varios posts es un hilo, y un hilo de un solo post es un tweet
        if len(e["posts"]) > 1 and slot["tipo"] == "tweet":
            slot["tipo"] = "hilo"
        elif len(e["posts"]) == 1 and slot["tipo"] == "hilo":
            slot["tipo"] = "tweet"
        fuentes, vistos_url = [], set()
        for h in e["historias"]:
            if h not in indice:
                problemas.append(f"{e['id']}: la historia {h} no existe en el digest de hoy")
                continue
            for f in indice[h]["fuentes"]:
                if f["url"] not in vistos_url:
                    vistos_url.add(f["url"])
                    fuentes.append(dict(f))
        if not e["historias"]:
            fuentes = [{"medio": "ESPN", "url": ESPN_MARCADORES.get(slot["liga"], ESPN_MARCADORES["NFL"])}]
        slot["fuentes"] = fuentes
    return tweets, problemas
