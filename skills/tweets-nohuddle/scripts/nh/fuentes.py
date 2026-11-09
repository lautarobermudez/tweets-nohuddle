"""Paso 1 de la corrida: junta titulares de todos los medios, filtra ruido, agrupa por historia y cuenta cuantos medios la cubren."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

from . import rss, texto


def es_ruido(titulo: str, resumen: str, palabras: List[str]) -> bool:
    t = (titulo + " " + resumen).lower()
    return any(p in t for p in palabras)


def _misma_historia(a: dict, b: dict) -> bool:
    """Dos titulares son la misma historia si comparten protagonista (un nombre propio) Y vocabulario del hecho.

    Exigir el nombre propio evita unir notas distintas que solo repiten frases genericas
    ("not ready to name starter", "trade deadline").
    """
    jac = texto.jaccard(a["titulo"], b["titulo"])
    ents = len(a["_ents"] & b["_ents"])
    toks = len(a["_toks"] & b["_toks"])
    if jac >= 0.5:
        return True
    if ents >= 1 and (jac >= 0.25 or toks >= 3):
        return True
    return ents >= 2 and jac >= 0.12


def agrupar(items: List[dict]) -> List[dict]:
    """Agrupa titulares que hablan de lo mismo (distintos medios, mismo hecho).

    Cada grupo tiene una 'semilla' (el titular mas reciente) y un titular solo se suma si se parece a la
    semilla. Asi no se forman cadenas (A se parece a B, B a C, pero A y C no tienen nada que ver).
    Es una ayuda para la regla de 'dos medios': la decision final la toma el agente.
    """
    marcados = []
    for it in items:
        m = dict(it)
        m["_ents"] = texto.entidades(it["titulo"])
        m["_toks"] = texto.tokens(it["titulo"])
        marcados.append(m)
    marcados.sort(key=lambda m: m["publicado"] or "", reverse=True)

    grupos: List[List[dict]] = []
    for m in marcados:
        mejor, mejor_score = None, 0.0
        for g in grupos:
            if _misma_historia(g[0], m):
                score = texto.jaccard(g[0]["titulo"], m["titulo"])
                if score >= mejor_score:
                    mejor, mejor_score = g, score
        if mejor is None:
            grupos.append([m])
        else:
            mejor.append(m)

    historias = []
    for miembros in grupos:
        medios = sorted({m["medio"] for m in miembros})
        historias.append({
            "titulo_guia": miembros[0]["titulo"],
            "liga": miembros[0]["liga"],
            "n_medios": len(medios),
            "medios": medios,
            "mas_reciente": miembros[0]["publicado"],
            "items": [{"medio": m["medio"], "tier": m["tier"], "titulo": m["titulo"], "link": m["link"], "publicado": m["publicado"], "resumen": m.get("resumen", "")[:300]} for m in miembros],
        })
    # Primero las cubiertas por mas medios; a igualdad, las mas recientes.
    historias.sort(key=lambda h: (h["n_medios"], h["mas_reciente"] or ""), reverse=True)
    return historias


def recolectar(
    fuentes: dict,
    reglas: dict,
    horas: int = 36,
    ahora: Optional[datetime] = None,
    fetch: Callable[[str], bytes] = rss.descargar,
) -> dict:
    """Lee todos los feeds activos y la API de ESPN. Nunca levanta por una fuente rota: la anota en 'fuentes_error'."""
    ahora = ahora or datetime.now(timezone.utc)
    desde = ahora - timedelta(hours=horas)
    ruido = [p.lower() for p in reglas.get("ruido_palabras", [])]

    ok, errores, descartados_ruido = [], [], 0
    items: List[dict] = []
    vistos = set()

    for f in fuentes.get("feeds", []):
        if not f.get("activo", True):
            continue
        try:
            for it in rss.parsear_feed(fetch(f["url"])):
                pub = it["publicado"]
                if pub is not None and pub < desde:
                    continue
                if es_ruido(it["titulo"], it["resumen"], ruido):
                    descartados_ruido += 1
                    continue
                clave = (f["medio"], texto.normalizar(it["titulo"]))
                if clave in vistos:
                    continue
                vistos.add(clave)
                items.append({
                    "medio": f["medio"], "tier": f.get("tier", "B"), "liga": f["liga"],
                    "titulo": it["titulo"], "link": it["link"], "resumen": it["resumen"],
                    "publicado": pub.isoformat() if pub else None,
                })
            ok.append(f["id"])
        except rss.FuenteError as e:
            errores.append({"id": f["id"], "medio": f["medio"], "error": str(e)})

    partidos: List[dict] = []
    for api in fuentes.get("espn_api", []):
        try:
            partidos += rss.parsear_scoreboard(fetch(api["url"]), api["liga"])
            ok.append("espn_api_" + api["liga"].lower())
        except rss.FuenteError as e:
            errores.append({"id": "espn_api_" + api["liga"].lower(), "medio": "ESPN API", "error": str(e)})

    historias = agrupar(items)
    return {
        "generado": ahora.isoformat(),
        "ventana_horas": horas,
        "fuentes_ok": ok,
        "fuentes_error": errores,
        "medios_por_busqueda": fuentes.get("medios_por_busqueda", []),
        "insiders": fuentes.get("insiders", []),
        "descartados_por_ruido": descartados_ruido,
        "total_titulares": len(items),
        "historias": historias,
        "partidos": partidos,
    }
