"""Validacion determinista de la planilla de tweets: todo lo que se puede chequear sin IA se chequea aca.

Cada hallazgo es un ERROR (bloquea el Word) o un AVISO (se muestra pero no bloquea).
"""
from __future__ import annotations

import re
from typing import List, Optional

from . import texto

HORA_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _min(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _oraciones(t: str) -> List[str]:
    return [o for o in re.split(r"(?<=[.!?])\s+", t) if o.strip()]


def _cita_fuentes(textos: List[str], reglas: dict, insiders: List[str], medios: List[str]) -> tuple:
    """Detecta si el texto cita a un medio o insider. Devuelve (errores, avisos) como listas de mensajes.

    - ERROR: 'segun...', 'de acuerdo con...', 'fuentes...' o el nombre de un insider (somos un medio: no citamos).
    - AVISO: un medio nombrado junto a un verbo de atribucion ('ESPN informa...'); puede ser un falso positivo
      (por ejemplo, un directivo de ESPN que habla), por eso no bloquea.
    """
    errores, avisos = [], []
    unido = " ".join(textos)
    bajo = unido.lower()
    for p in reglas["palabras_cita"]:
        if re.search(r"\b" + re.escape(p) + r"\b", bajo):
            errores.append(f"cita una fuente ('{p}'): no se cita a nadie, se escribe como medio propio")
            break
    for ins in insiders:
        ultimo = ins.split()[-1]
        if re.search(r"\b" + re.escape(ins) + r"\b", unido, re.I) or re.search(r"\b" + re.escape(ultimo) + r"\b", unido):
            errores.append(f"nombra a un insider ({ins}): no se cita a nadie")
            break
    nombres = {m for m in medios if m}
    for o in _oraciones(unido):
        ob = o.lower()
        for m in nombres:
            if re.search(r"\b" + re.escape(m.lower()) + r"\b", ob) and any(re.search(r"\b" + v + r"\b", ob) for v in reglas["verbos_atribucion"]):
                avisos.append(f"parece citar a {m} ('{o.strip()[:70]}'): revisar")
                break
    return errores, avisos


def validar(
    tweets: dict,
    reglas: dict,
    historial: Optional[List[dict]] = None,
    titulares: Optional[List[str]] = None,
    insiders: Optional[List[str]] = None,
) -> dict:
    errores: List[dict] = []
    avisos: List[dict] = []

    def err(i, regla, msg):
        errores.append({"id": i, "regla": regla, "mensaje": msg})

    def avi(i, regla, msg):
        avisos.append({"id": i, "regla": regla, "mensaje": msg})

    historial = historial or []
    titulares = titulares or []
    insiders = insiders or []

    # ---- estructura general
    if not FECHA_RE.match(str(tweets.get("fecha", ""))):
        err("-", "estructura", "Falta 'fecha' con formato AAAA-MM-DD")
    items = tweets.get("items")
    if not isinstance(items, list) or not items:
        err("-", "estructura", "No hay 'items' (la lista de tweets e hilos esta vacia)")
        return {"errores": errores, "avisos": avisos, "resumen": {"tweets": 0, "hilos": 0}}

    ids_vistos = set()
    n_tweets = n_hilos = 0
    for k, it in enumerate(items):
        i = it.get("id") or f"#{k + 1}"
        if i in ids_vistos:
            err(i, "estructura", "id repetido")
        ids_vistos.add(i)

        tipo = it.get("tipo")
        if tipo not in ("tweet", "hilo"):
            err(i, "estructura", "'tipo' debe ser 'tweet' o 'hilo'")
            continue
        n_tweets += tipo == "tweet"
        n_hilos += tipo == "hilo"

        if it.get("liga") not in reglas["ligas"]:
            err(i, "estructura", f"'liga' debe ser una de {reglas['ligas']}")
        if it.get("categoria") not in reglas["categorias"]:
            err(i, "estructura", f"'categoria' debe ser una de {reglas['categorias']}")

        textos = it.get("textos")
        if not isinstance(textos, list) or not textos or not all(isinstance(t, str) and t.strip() for t in textos):
            err(i, "estructura", "'textos' debe ser una lista de textos no vacios")
            continue
        if tipo == "tweet" and len(textos) != 1:
            err(i, "estructura", "un 'tweet' tiene exactamente 1 texto (si son varios, es un 'hilo')")
        c = reglas["cantidad"]
        if tipo == "hilo" and not (c["posts_por_hilo_min"] <= len(textos) <= c["posts_por_hilo_max"]):
            err(i, "hilo", f"un hilo lleva entre {c['posts_por_hilo_min']} y {c['posts_por_hilo_max']} posts (tiene {len(textos)})")

        # ---- hora
        hora = it.get("hora", "")
        if not HORA_RE.match(str(hora)):
            err(i, "hora", "'hora' debe ser HH:MM (hora de Argentina)")
        else:
            v = reglas["ventana_horaria"]
            if not (_min(v["desde"]) <= _min(hora) <= _min(v["hasta"])):
                avi(i, "hora", f"{hora} esta fuera de la ventana {v['desde']}-{v['hasta']}")

        # ---- cada post
        for n, t in enumerate(textos, 1):
            et = f"{i} post {n}" if tipo == "hilo" else i
            largo = texto.largo_x(t, reglas["largo_url"])
            if largo > reglas["max_caracteres"]:
                err(et, "largo", f"{largo} caracteres (maximo {reglas['max_caracteres']})")
            if "[" in t and "]" in t:
                err(et, "corchetes", "tiene [corchetes] sin completar")
            if texto.contar_hashtags(t) > reglas["max_hashtags"]:
                avi(et, "hashtags", f"mas de {reglas['max_hashtags']} hashtags")
            if texto.contar_emojis(t) > reglas["max_emojis"]:
                avi(et, "emojis", f"mas de {reglas['max_emojis']} emoji")
            if t.count("!") > reglas["max_exclamaciones"]:
                avi(et, "tono", "demasiadas exclamaciones")
            if texto.palabras_en_mayusculas(t) > reglas["max_palabras_en_mayusculas"]:
                avi(et, "tono", "palabras GRITADAS en mayusculas")
            bajo = t.lower()
            for cb in reglas["palabras_clickbait"]:
                if cb in bajo:
                    avi(et, "tono", f"suena a clickbait: '{cb}'")
                    break
            if texto.DECIMAL_PUNTO_RE.search(t):
                avi(et, "numeros", "decimal con punto: en No Huddle se escribe con coma (4,8)")

            # ---- copia de titular
            for tit in titulares:
                if texto.jaccard(t, tit) >= reglas["umbral_copia_titular"]:
                    avi(et, "copia", f"es casi igual al titular de un medio: '{tit[:70]}'")
                    break
            # ---- repetido contra dias anteriores
            for h in historial:
                if texto.jaccard(t, h.get("texto", "")) >= reglas["umbral_repetido"]:
                    err(et, "repetido", f"parecido a lo propuesto el {h.get('fecha')}: '{h.get('texto', '')[:60]}'")
                    break

        # ---- fuentes (referencia interna: van en el Word, no en el texto)
        fuentes = it.get("fuentes")
        if not isinstance(fuentes, list) or not fuentes:
            err(i, "fuentes", "falta al menos una fuente (medio + url) para la referencia interna")
            fuentes = []
        else:
            for f in fuentes:
                if not (isinstance(f, dict) and f.get("medio") and str(f.get("url", "")).startswith("http")):
                    err(i, "fuentes", "cada fuente necesita 'medio' y 'url' (http...)")
                    break
        medios = [f.get("medio") for f in fuentes if isinstance(f, dict)]

        # ---- no citar fuentes en el texto (somos un medio)
        e_cita, a_cita = _cita_fuentes(textos, reglas, insiders, medios)
        for m in e_cita:
            err(i, "cita_en_texto", m)
        for m in a_cita:
            avi(i, "cita_en_texto", m)

    # ---- cantidad total
    c = reglas["cantidad"]
    if not (c["tweets_min"] <= n_tweets <= c["tweets_max"]):
        avi("-", "cantidad", f"{n_tweets} tweets (lo esperado es {c['tweets_min']}-{c['tweets_max']})")
    if not (c["hilos_min"] <= n_hilos <= c["hilos_max"]):
        avi("-", "cantidad", f"{n_hilos} hilos (lo esperado es {c['hilos_min']}-{c['hilos_max']})")

    # ---- separacion entre horarios
    horas = sorted(_min(it["hora"]) for it in items if isinstance(it.get("hora"), str) and HORA_RE.match(it["hora"]))
    for a, b in zip(horas, horas[1:]):
        if b - a < reglas["separacion_minima_minutos"]:
            avi("-", "hora", f"hay dos publicaciones con menos de {reglas['separacion_minima_minutos']} min de diferencia ({a // 60:02d}:{a % 60:02d} y {b // 60:02d}:{b % 60:02d})")

    return {"errores": errores, "avisos": avisos, "resumen": {"tweets": n_tweets, "hilos": n_hilos}}
