"""Los dos pasos de la skill, como funciones: `preparar` (todo lo mecanico antes de redactar) y `cerrar` (todo lo mecanico despues).

El modelo solo interviene en el medio: completar los textos del plan.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from . import fuentes as nh_fuentes
from . import historial, plan, rss, rutas, validar, wordgen


class FlujoError(Exception):
    """Un problema que el usuario puede entender y resolver (sin Python, sin internet, archivo faltante...)."""


def chequeos() -> None:
    if sys.version_info < (3, 8):
        raise FlujoError("Hace falta Python 3.8 o mas nuevo (python.org).")
    try:
        rutas.cargar_reglas()
        rutas.cargar_fuentes()
    except Exception as e:  # noqa: BLE001
        raise FlujoError(f"No puedo leer la configuracion de la skill: {e}")
    try:
        w = rutas.work_dir()
        w.mkdir(parents=True, exist_ok=True)
        (w / ".escritura_ok").write_text("ok", encoding="utf-8")
        (w / ".escritura_ok").unlink()
    except OSError as e:
        raise FlujoError(f"No puedo escribir en la carpeta de trabajo {rutas.work_dir()}: {e}")


def preparar(
    fetch: Callable[[str], bytes] = rss.descargar,
    ahora: Optional[datetime] = None,
    todo_el_dia: bool = False,
    nuevo: bool = False,
) -> dict:
    """Chequea, junta fuentes, arma el digest y el plan del dia. Devuelve rutas y el texto del 'brief' para el agente."""
    chequeos()
    reglas = rutas.cargar_reglas()
    ahora = ahora or datetime.now(timezone.utc)
    res = nh_fuentes.recolectar(rutas.cargar_fuentes(), reglas, horas=36, ahora=ahora, fetch=fetch)
    if not res["fuentes_ok"]:
        raise FlujoError("No pude leer ningun medio (¿sin internet?). Reintenta mas tarde.")

    esqueleto = plan.armar(reglas, res["partidos"], ahora, todo_el_dia)
    fecha = esqueleto["fecha"]
    carpeta = rutas.dia_dir(fecha)
    rutas.guardar_json(carpeta / "candidatos.json", res)
    digest_txt = nh_fuentes.digest(res, reglas, ahora)
    (carpeta / "digest.md").write_text(digest_txt, encoding="utf-8")

    ruta_tweets = carpeta / "tweets.json"
    reutilizado = ruta_tweets.exists() and not nuevo
    if not reutilizado:
        rutas.guardar_json(ruta_tweets, esqueleto)
    plan_actual = rutas.cargar_json(ruta_tweets)

    estilo = (rutas.SKILL_DIR / "references" / "estilo_tweets.md").read_text(encoding="utf-8")
    brief = _brief(fecha, ruta_tweets, plan_actual, digest_txt, estilo, reglas, reutilizado)
    return {"fecha": fecha, "tweets": ruta_tweets, "digest": carpeta / "digest.md", "brief": brief,
            "fuentes_ok": res["fuentes_ok"], "fuentes_error": res["fuentes_error"], "reutilizado": reutilizado}


def _brief(fecha, ruta_tweets, plan_actual, digest_txt, estilo, reglas, reutilizado) -> str:
    L = [f"=== PREPARADO ({fecha}) ===",
         f"Archivo a completar: {ruta_tweets}" + ("  (ya existia de una corrida previa de hoy: se conserva)" if reutilizado else ""),
         "",
         "QUE HACER (solo esto):",
         "1. Abri el archivo y, para cada slot, completa `textos` (1 texto si es tweet; 2 a 6 si es hilo) y `fuentes` ([{medio, url}] tomados del digest).",
         "2. Podes cambiar `categoria`, `liga` u `hora` de un slot, y borrar los que no uses. Los slots vacios se descartan solos.",
         "3. Usa SOLO lo que dice el digest. No agregues datos, cifras ni citas.",
         "4. NO cites fuentes en el texto: nada de 'segun...', 'reporta...' ni nombres de insiders. Escribis como medio propio.",
         "   Si el digest muestra un rumor ('sources', 'report', 'could'), redactalo en condicional (\"irian por\", \"estarian cerca\") en vez de afirmarlo.",
         "5. Cuando termines, corre: tweets.py cerrar",
         "",
         "PLAN DEL DIA (hora de Argentina):"]
    for i in plan_actual["items"]:
        estado = "completo" if any(t.strip() for t in i.get("textos", [])) else "vacio"
        L.append(f"- {i['id']}  {i['hora']}  {i['tipo']:<5} {i['liga']:<7} {i['categoria']:<11} ({i['prioridad']}, {estado})")
    L += ["", "=== DIGEST ===", digest_txt, "=== ESTILO ===", estilo]
    return "\n".join(L)


def cerrar(ruta_tweets: Optional[Path] = None, forzar: bool = False) -> dict:
    """Valida lo que escribio el agente, arma el Word, actualiza el historial y devuelve el resumen para el usuario."""
    reglas = rutas.cargar_reglas()
    insiders = rutas.cargar_fuentes().get("insiders", [])
    ruta = Path(ruta_tweets) if ruta_tweets else rutas.dia_dir(rutas.hoy_ar().isoformat()) / "tweets.json"
    if not ruta.exists():
        raise FlujoError(f"No encuentro {ruta}. Primero corre: tweets.py preparar")
    tweets = rutas.cargar_json(ruta)
    tweets, descartados = plan.limpiar(tweets)
    if not tweets["items"]:
        raise FlujoError("No hay ningun texto completado: completa al menos un slot de tweets.json.")
    rutas.guardar_json(ruta, tweets)

    hoy = date.fromisoformat(tweets["fecha"])
    candidatos = ruta.with_name("candidatos.json")
    titulares = []
    if candidatos.exists():
        titulares = [i["titulo"] for h in rutas.cargar_json(candidatos).get("historias", []) for i in h["items"]]
    res = validar.validar(tweets, reglas, historial.recientes(reglas["historial_dias"], hoy=hoy), titulares, insiders)

    resultado = {"errores": res["errores"], "avisos": res["avisos"], "descartados": descartados, "word": None, "tabla": _tabla(tweets)}
    if res["errores"] and not forzar:
        return resultado
    avisos = res["avisos"] + [dict(e, mensaje="ERROR: " + e["mensaje"]) for e in res["errores"]]
    d = hoy
    destino = rutas.dia_dir(tweets["fecha"]) / f"Tweets No Huddle - {d.day:02d}-{d.month:02d}-{d.year}.docx"
    wordgen.armar_docx(tweets, reglas, destino, avisos)
    if not res["errores"]:
        historial.agregar(tweets)
    resultado["word"] = destino
    return resultado


def _tabla(tweets: dict) -> list:
    return [(i["hora"], "hilo" if i["tipo"] == "hilo" else "tweet", i["categoria"], ", ".join(sorted({f["medio"] for f in i.get("fuentes", [])})) or "-")
            for i in sorted(tweets["items"], key=lambda x: x.get("hora", ""))]
