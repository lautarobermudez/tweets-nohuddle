#!/usr/bin/env python3
"""CLI de la skill /tweets-nohuddle. Solo biblioteca estandar (Python 3.8+).

FLUJO NORMAL (son los dos unicos comandos que usa el agente):
  python tweets.py preparar [--todo-el-dia] [--nuevo]   # chequea, junta medios, arma digest y plan del dia; imprime todo lo que el agente necesita
  python tweets.py cerrar [redaccion.txt|tweets.json] [--forzar]   # valida, arma el Word, actualiza el historial e imprime el resumen final

COMANDOS SUELTOS (para depurar):
  python tweets.py doctor [--red]                      # chequea que todo este listo para correr
  python tweets.py hoy                                 # fecha de hoy en Argentina (AAAA-MM-DD)
  python tweets.py fuentes [--horas 36] [--salida X]   # junta titulares de los medios -> candidatos.json
  python tweets.py validar tweets.json [--titulares candidatos.json]
  python tweets.py word tweets.json [--forzar]         # valida y arma el Word; registra en el historial
  python tweets.py historial                           # muestra lo ya propuesto en los ultimos dias

Codigos de salida: 0 = todo bien, 1 = hay errores de validacion, 2 = problema de configuracion o de uso.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nh import fuentes as nh_fuentes  # noqa: E402
from nh import flujo, historial, rss, rutas, validar, wordgen  # noqa: E402


def _imprimir(res: dict) -> None:
    for e in res["errores"]:
        print(f"  ERROR  [{e['id']}] {e['regla']}: {e['mensaje']}")
    for a in res["avisos"]:
        print(f"  aviso  [{a['id']}] {a['regla']}: {a['mensaje']}")
    r = res["resumen"]
    print(f"Resumen: {r['tweets']} tweets, {r['hilos']} hilos, {len(res['errores'])} errores, {len(res['avisos'])} avisos")


def _titulares(path: str):
    if not path:
        return []
    datos = rutas.cargar_json(Path(path))
    return [i["titulo"] for h in datos.get("historias", []) for i in h["items"]]


def cmd_doctor(a) -> int:
    ok = True

    def linea(estado, msg):
        nonlocal ok
        ok = ok and estado
        print(("  OK    " if estado else "  FALLA ") + msg)

    print(f"Skill /tweets-nohuddle v{rutas.cargar_reglas().get('version', '?')}")
    v = sys.version_info
    linea(v >= (3, 8), f"Python {v.major}.{v.minor}.{v.micro} (se necesita 3.8 o mas)")
    for nombre, f in (("reglas.json", rutas.cargar_reglas), ("fuentes.json", rutas.cargar_fuentes)):
        try:
            f()
            linea(True, f"config/{nombre} se lee bien")
        except Exception as e:  # noqa: BLE001
            linea(False, f"config/{nombre}: {e}")
    try:
        w = rutas.work_dir()
        w.mkdir(parents=True, exist_ok=True)
        prueba = w / ".escritura_ok"
        prueba.write_text("ok", encoding="utf-8")
        prueba.unlink()
        linea(True, f"carpeta de trabajo escribible: {w}")
    except OSError as e:
        linea(False, f"no puedo escribir en {rutas.work_dir()}: {e}")
    if a.red:
        try:
            feeds = [f for f in rutas.cargar_fuentes()["feeds"] if f.get("activo", True)]
            rss.parsear_feed(rss.descargar(feeds[0]["url"], reintentos=0))
            linea(True, f"internet y lectura de feeds ({feeds[0]['medio']})")
        except Exception as e:  # noqa: BLE001
            linea(False, f"no pude leer un feed: {e}")
    print("Todo listo." if ok else "Hay que resolver lo que dice FALLA antes de correr la skill.")
    return 0 if ok else 2


def cmd_fuentes(a) -> int:
    res = nh_fuentes.recolectar(rutas.cargar_fuentes(), rutas.cargar_reglas(), horas=a.horas)
    hoy = rutas.hoy_ar().isoformat()
    salida = Path(a.salida) if a.salida else rutas.dia_dir(hoy) / "candidatos.json"
    rutas.guardar_json(salida, res)
    resumen = salida.with_name("digest.md")
    resumen.write_text(nh_fuentes.digest(res, rutas.cargar_reglas()), encoding="utf-8")
    print(f"Fuentes OK: {', '.join(res['fuentes_ok']) or 'ninguna'}")
    for e in res["fuentes_error"]:
        print(f"  no se pudo leer {e['id']} ({e['medio']}): {e['error']}")
    print(f"{res['total_titulares']} titulares en {len(res['historias'])} historias "
          f"({sum(1 for h in res['historias'] if h['n_medios'] >= 2)} cubiertas por 2+ medios); "
          f"{res['descartados_por_ruido']} descartados por ruido; {len(res['partidos'])} partidos en ESPN.")
    print(f"Resumen para redactar (leer ESTE, no el json): {resumen}  (~{len(resumen.read_text(encoding='utf-8')) // 4} tokens)")
    print(f"Datos completos (solo para consultar): {salida}")
    return 0 if res["fuentes_ok"] else 2


def cmd_validar(a) -> int:
    tweets = rutas.cargar_json(Path(a.tweets))
    reglas = rutas.cargar_reglas()
    hoy = date.fromisoformat(tweets["fecha"]) if tweets.get("fecha") else rutas.hoy_ar()
    hist = historial.recientes(reglas["historial_dias"], hoy=hoy)
    res = validar.validar(tweets, reglas, hist, _titulares(a.titulares), rutas.cargar_fuentes().get("insiders", []))
    _imprimir(res)
    return 1 if res["errores"] else 0


def cmd_word(a) -> int:
    ruta_json = Path(a.tweets)
    tweets = rutas.cargar_json(ruta_json)
    reglas = rutas.cargar_reglas()
    hoy = date.fromisoformat(tweets["fecha"]) if tweets.get("fecha") else rutas.hoy_ar()
    res = validar.validar(tweets, reglas, historial.recientes(reglas["historial_dias"], hoy=hoy), _titulares(a.titulares), rutas.cargar_fuentes().get("insiders", []))
    _imprimir(res)
    if res["errores"] and not a.forzar:
        print("No armo el Word porque hay errores. Corregilos (o usa --forzar para armarlo igual, marcando lo pendiente).")
        return 1
    avisos = res["avisos"] + [dict(e, mensaje="ERROR: " + e["mensaje"]) for e in res["errores"]]
    d = date.fromisoformat(tweets["fecha"])
    destino = Path(a.salida) if a.salida else rutas.dia_dir(tweets["fecha"]) / f"Tweets No Huddle - {d.day:02d}-{d.month:02d}-{d.year}.docx"
    wordgen.armar_docx(tweets, reglas, destino, avisos)
    if not res["errores"]:
        n = historial.agregar(tweets)
        print(f"Historial actualizado ({n} textos).")
    print(f"Word listo: {destino}")
    return 1 if res["errores"] else 0


def cmd_hoy(a) -> int:
    print(rutas.hoy_ar().isoformat())
    return 0


def cmd_preparar(a) -> int:
    try:
        r = flujo.preparar(todo_el_dia=a.todo_el_dia, nuevo=a.nuevo)
    except flujo.FlujoError as e:
        print(f"No se pudo preparar: {e}", file=sys.stderr)
        return 2
    print(r["brief"])
    if r["fuentes_error"]:
        print("\n(Medios que no respondieron: " + ", ".join(sorted({e["medio"] for e in r["fuentes_error"]})) + ")")
    return 0


def cmd_cerrar(a) -> int:
    try:
        r = flujo.cerrar(Path(a.tweets) if a.tweets else None, forzar=a.forzar)
    except flujo.FlujoError as e:
        print(f"No se pudo cerrar: {e}", file=sys.stderr)
        return 2
    if r["descartados"]:
        print(f"Slots sin completar (descartados): {', '.join(r['descartados'])}")
    if r["errores"]:
        print("ERRORES (corregilos en redaccion.txt y volve a correr: tweets.py cerrar):")
        for e in r["errores"]:
            print(f"  [{e['id']}] {e['regla']}: {e['mensaje']}")
    if r["word"] is None:
        print("No se armo el Word.")
        return 1
    print(f"WORD LISTO: {r['word']}")
    print("\nRESUMEN (hora | tipo | categoria | fuente interna):")
    for hora, tipo, cat, fuente in r["tabla"]:
        print(f"  {hora} | {tipo:<5} | {cat:<11} | {fuente}")
    if r["avisos"]:
        print("\nAVISOS (para mirar antes de publicar):")
        for x in r["avisos"]:
            print(f"  [{x['id']}] {x['regla']}: {x['mensaje']}")
    print("\nNada se publico: la persona de redes revisa y programa.")
    return 1 if r["errores"] else 0


def cmd_historial(a) -> int:
    hist = historial.recientes(a.dias, hoy=rutas.hoy_ar() if not a.hasta else date.fromisoformat(a.hasta))
    for h in hist:
        print(f"{h['fecha']}  {h.get('id', ''):>4}  {h['texto'][:100]}")
    print(f"{len(hist)} textos en los ultimos {a.dias} dias")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Herramientas de la skill /tweets-nohuddle")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("preparar"); pr.add_argument("--todo-el-dia", action="store_true", help="no saltear los horarios que ya pasaron"); pr.add_argument("--nuevo", action="store_true", help="rehacer el plan aunque ya exista el de hoy"); pr.set_defaults(f=cmd_preparar)
    ce = sub.add_parser("cerrar"); ce.add_argument("tweets", nargs="?"); ce.add_argument("--forzar", action="store_true"); ce.set_defaults(f=cmd_cerrar)
    d = sub.add_parser("doctor"); d.add_argument("--red", action="store_true"); d.set_defaults(f=cmd_doctor)
    f = sub.add_parser("fuentes"); f.add_argument("--horas", type=int, default=36); f.add_argument("--salida"); f.set_defaults(f=cmd_fuentes)
    v = sub.add_parser("validar"); v.add_argument("tweets"); v.add_argument("--titulares"); v.set_defaults(f=cmd_validar)
    w = sub.add_parser("word"); w.add_argument("tweets"); w.add_argument("--titulares"); w.add_argument("--salida"); w.add_argument("--forzar", action="store_true"); w.set_defaults(f=cmd_word)
    sub.add_parser("hoy").set_defaults(f=cmd_hoy)
    h = sub.add_parser("historial"); h.add_argument("--dias", type=int, default=7); h.add_argument("--hasta"); h.set_defaults(f=cmd_historial)
    a = p.parse_args(argv)
    try:
        return a.f(a)
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
