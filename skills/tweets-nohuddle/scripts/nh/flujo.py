"""Los dos pasos de la skill, como funciones: `preparar` (todo lo mecanico antes de redactar) y `cerrar` (todo lo mecanico despues).

El modelo solo interviene en el medio: completar los textos del plan.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from . import digest as nh_digest
from . import fuentes as nh_fuentes
from . import historial, plan, redaccion, rss, rutas, validar, wordgen


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
    ruta_red = carpeta / "redaccion.txt"
    if nuevo:  # empezar de cero: se borra lo de hoy
        for nombre in ("redaccion.txt", "tweets.json", "plan.json"):
            (carpeta / nombre).unlink(missing_ok=True)
    rutas.guardar_json(carpeta / "candidatos.json", res)
    digest_txt, indice = nh_digest.construir(res, reglas, ahora)
    (carpeta / "digest.md").write_text(digest_txt, encoding="utf-8")
    rutas.guardar_json(carpeta / "digest_ids.json", indice)

    reutilizado = ruta_red.exists() and (carpeta / "plan.json").exists()
    if not reutilizado:  # el plan solo se rehace si no hay una redaccion en curso que dependa de el
        rutas.guardar_json(carpeta / "plan.json", esqueleto)
    plan_actual = rutas.cargar_json(carpeta / "plan.json")
    rutas.guardar_json(rutas.ultimo_plan_path(), {"fecha": fecha})  # para que `cerrar` encuentre este plan aunque pase la medianoche

    estilo = (rutas.SKILL_DIR / "references" / "estilo_tweets.md").read_text(encoding="utf-8")
    brief = _brief(fecha, ruta_red, plan_actual, digest_txt, estilo, reutilizado)
    return {"fecha": fecha, "redaccion": ruta_red, "digest": carpeta / "digest.md", "brief": brief,
            "fuentes_ok": res["fuentes_ok"], "fuentes_error": res["fuentes_error"], "reutilizado": reutilizado}


def _brief(fecha, ruta_red, plan_actual, digest_txt, estilo, reutilizado) -> str:
    ids = [i["id"] for i in plan_actual["items"]]
    ej1, ej2 = (ids + ["t1", "t2"])[:2]
    L = [f"=== PREPARADO ({fecha}) ===",
         f"Escribi este archivo: {ruta_red}" + ("   (YA EXISTE de una corrida previa de hoy: para rehacerlo desde cero corre `preparar --nuevo`; o leelo y editalo)" if reutilizado else ""),
         "",
         "QUE HACER (solo esto): una linea por publicacion, con este formato",
         "    id | historias | texto",
         f"    {ej1} | N1,N4 | Texto del tweet.",
         f"    {ej2}@12:30 | C2 | Otro tweet (el @hora es opcional: cambia el horario).",
         "    h1 | N3 | Primer post de un hilo.",
         "    + Segundo post del hilo.",
         "    + Tercer post del hilo.",
         "  - `historias`: IDs del digest de donde sale el dato (N1, C2...). Si no sale de una historia (un resultado, una previa), pone `-`.",
         "  - Slots que no uses: omitilos (se descartan solos). Un tweet con varias lineas `+` pasa a ser un hilo.",
         "  - Usa SOLO lo que dice el digest. No agregues datos, cifras ni citas.",
         "  - NO cites fuentes en el texto: nada de 'segun...', 'reporta...' ni nombres de insiders. Escribis como medio propio.",
         "    Si el digest muestra un rumor ('sources', 'report', 'could', 'likely'), redactalo en condicional (\"irian por\", \"estarian cerca\").",
         "  - Cuando termines, corre: tweets.py cerrar",
         "",
         "PLAN DEL DIA (hora de Argentina):"]
    for i in plan_actual["items"]:
        L.append(f"- {i['id']}  {i['hora']}  {i['tipo']:<5} {i['liga']:<7} {i['categoria']:<11} ({i['prioridad']})")
    L += ["", "=== DIGEST ===", digest_txt, "=== ESTILO ===", estilo]
    return "\n".join(L)


def cerrar(ruta: Optional[Path] = None, forzar: bool = False) -> dict:
    """Valida lo que escribio el agente, arma el Word, actualiza el historial y devuelve el resumen para el usuario.

    Lee `redaccion.txt` (formato compacto) del dia; si no existe, usa un `tweets.json` ya completo (modo manual).
    """
    reglas = rutas.cargar_reglas()
    insiders = rutas.cargar_fuentes().get("insiders", [])
    ruta = Path(ruta) if ruta else rutas.dia_dir(_fecha_a_cerrar()) / "redaccion.txt"
    carpeta = ruta.parent
    problemas = []
    if ruta.suffix == ".txt" and ruta.exists():
        plan_json, ids_json = carpeta / "plan.json", carpeta / "digest_ids.json"
        if not plan_json.exists() or not ids_json.exists():
            raise FlujoError("Falta el plan del dia: primero corre tweets.py preparar.")
        entradas, problemas = redaccion.parsear(ruta.read_text(encoding="utf-8"))
        tweets, p2 = redaccion.aplicar(rutas.cargar_json(plan_json), entradas, rutas.cargar_json(ids_json))
        problemas += p2
        rutas.guardar_json(carpeta / "tweets.json", tweets)
    elif (carpeta / "tweets.json").exists() or ruta.suffix == ".json":
        tweets = rutas.cargar_json(ruta if ruta.suffix == ".json" else carpeta / "tweets.json")
    else:
        raise FlujoError(f"No encuentro {ruta}. Escribi la redaccion (ver tweets.py preparar) antes de cerrar.")
    tweets, descartados = plan.limpiar(tweets)
    if not tweets["items"]:
        raise FlujoError("No hay ningun texto completado: escribi al menos una linea en redaccion.txt.")
    rutas.guardar_json(carpeta / "tweets.json", tweets)

    hoy = date.fromisoformat(tweets["fecha"])
    candidatos = carpeta / "candidatos.json"
    titulares = []
    if candidatos.exists():
        titulares = [i["titulo"] for h in rutas.cargar_json(candidatos).get("historias", []) for i in h["items"]]
    res = validar.validar(tweets, reglas, historial.recientes(reglas["historial_dias"], hoy=hoy), titulares, insiders)
    res["errores"] = [{"id": "-", "regla": "redaccion", "mensaje": m} for m in problemas] + res["errores"]

    resultado = {"errores": res["errores"], "avisos": res["avisos"], "descartados": descartados, "word": None, "tabla": _tabla(tweets)}
    if res["errores"] and not forzar:
        return resultado
    avisos = res["avisos"] + [dict(e, mensaje="ERROR: " + e["mensaje"]) for e in res["errores"]]
    destino = rutas.dia_dir(tweets["fecha"]) / f"Tweets No Huddle - {hoy.day:02d}-{hoy.month:02d}-{hoy.year}.docx"
    wordgen.armar_docx(tweets, reglas, destino, avisos)
    if not res["errores"]:
        historial.agregar(tweets)
    resultado["word"] = destino
    return resultado


def _fecha_a_cerrar() -> str:
    """La fecha del ultimo plan preparado (si es de hoy o de ayer); si no, hoy.

    Asi, si se prepara a las 23:50 y se cierra a las 00:10, `cerrar` sigue encontrando la redaccion.
    """
    hoy = rutas.hoy_ar()
    try:
        fecha = date.fromisoformat(rutas.cargar_json(rutas.ultimo_plan_path())["fecha"])
    except (OSError, ValueError, KeyError, TypeError):
        return hoy.isoformat()
    return fecha.isoformat() if 0 <= (hoy - fecha).days <= 1 else hoy.isoformat()


def _tabla(tweets: dict) -> list:
    return [(i["hora"], "hilo" if i["tipo"] == "hilo" else "tweet", i["categoria"], ", ".join(sorted({f["medio"] for f in i.get("fuentes", [])})) or "-")
            for i in sorted(tweets["items"], key=lambda x: x.get("hora", ""))]
