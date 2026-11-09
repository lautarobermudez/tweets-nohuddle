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


_GENERICAS = {"sports", "news", "talk", "football", "pro", "the", "illustrated"}


def _nombra_fuente(texto_completo: str, medios, insiders, palabras_atribucion) -> bool:
    """True si el texto menciona a un medio de sus fuentes (nombre, una palabra distintiva o siglas), a un insider o usa 'segun...'."""
    bajo = texto_completo.lower()
    if any(p in bajo for p in palabras_atribucion):
        return True
    for medio in medios:
        palabras = [w for w in re.findall(r"[A-Za-z0-9]+", medio)]
        candidatos = {medio.lower()} | {w.lower() for w in palabras if len(w) >= 3 and w.lower() not in _GENERICAS}
        if len(palabras) > 1:
            candidatos.add("".join(w[0] for w in palabras).lower())  # "Pro Football Talk" -> pft
        if any(re.search(r"\b" + re.escape(c) + r"\b", bajo) for c in candidatos if c):
            return True
    for ins in insiders:
        if ins.lower() in bajo or ins.split()[-1].lower() in bajo:
            return True
    return False


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

        # ---- fuentes y atribucion
        fuentes = it.get("fuentes")
        if not isinstance(fuentes, list) or not fuentes:
            err(i, "fuentes", "falta al menos una fuente (medio + url)")
            fuentes = []
        else:
            for f in fuentes:
                if not (isinstance(f, dict) and f.get("medio") and str(f.get("url", "")).startswith("http")):
                    err(i, "fuentes", "cada fuente necesita 'medio' y 'url' (http...)")
                    break
        medios = {f.get("medio") for f in fuentes if isinstance(f, dict) and f.get("medio")}
        atr = it.get("atribucion")  # opcional en modo liviano
        if atr is not None and atr not in ("confirmado", "reportado"):
            err(i, "atribucion", "'atribucion' (opcional) debe ser 'confirmado' o 'reportado'")
        elif atr == "confirmado" and reglas.get("exigir_doble_fuente") and len(medios) < reglas["min_medios_confirmado"]:
            err(i, "doble_fuente", f"modo estricto: un hecho 'confirmado' necesita {reglas['min_medios_confirmado']} medios distintos (tiene {len(medios)})")
        elif atr == "reportado" and not any(p in " ".join(textos).lower() for p in reglas["palabras_atribucion"]):
            err(i, "atribucion", "es un dato 'reportado' pero el texto no nombra a quien lo reporta (segun / reporta / informo...)")

        # En modo liviano la responsabilidad queda en el medio o insider: el texto tiene que nombrarlo.
        if reglas.get("exigir_fuente_en_texto") and it.get("categoria") not in ("pregunta",):
            if not _nombra_fuente(" ".join(textos), medios, insiders, reglas["palabras_atribucion"]):
                avi(i, "fuente_en_texto", "el texto no nombra a su fuente (ESPN, CBS, Schefter, 'segun...'): agregarla")

        # ---- verificacion (opcional salvo modo estricto)
        ver = it.get("verificacion")
        if ver is not None:
            est = ver.get("estado") if isinstance(ver, dict) else None
            if est not in reglas["estados_verificacion"]:
                err(i, "verificacion", f"'verificacion.estado' debe ser uno de {reglas['estados_verificacion']}")
            elif est == "ERROR":
                err(i, "verificacion", "el verificador marco un ERROR de dato: corregir o descartar")
            elif est == "REVISAR":
                avi(i, "verificacion", "el verificador pide revisar: " + str(ver.get("detalle", ""))[:120])
        elif reglas.get("verificacion_obligatoria"):
            avi(i, "verificacion", "sin verificar")

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
