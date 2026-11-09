#!/usr/bin/env python3
"""CLI de la skill /tweets-nohuddle. Solo biblioteca estandar (Python 3.8+).

  python tweets.py doctor [--red]                      # chequea que todo este listo para correr
  python tweets.py hoy                                 # fecha de hoy en Argentina (AAAA-MM-DD)
  python tweets.py fuentes [--horas 36] [--salida X]   # junta titulares de los medios -> candidatos.json
  python tweets.py fusionar tweets.json verificacion.json   # pasa el veredicto del verificador a cada tweet
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
from nh import historial, rss, rutas, validar, verificacion, wordgen  # noqa: E402


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
    print(f"Fuentes OK: {', '.join(res['fuentes_ok']) or 'ninguna'}")
    for e in res["fuentes_error"]:
        print(f"  no se pudo leer {e['id']} ({e['medio']}): {e['error']}")
    print(f"{res['total_titulares']} titulares en {len(res['historias'])} historias "
          f"({sum(1 for h in res['historias'] if h['n_medios'] >= 2)} cubiertas por 2+ medios); "
          f"{res['descartados_por_ruido']} descartados por ruido; {len(res['partidos'])} partidos en ESPN.")
    print(f"Guardado en {salida}")
    return 0 if res["fuentes_ok"] else 2


def cmd_validar(a) -> int:
    tweets = rutas.cargar_json(Path(a.tweets))
    reglas = rutas.cargar_reglas()
    hoy = date.fromisoformat(tweets["fecha"]) if tweets.get("fecha") else rutas.hoy_ar()
    hist = historial.recientes(reglas["historial_dias"], hoy=hoy)
    res = validar.validar(tweets, reglas, hist, _titulares(a.titulares))
    _imprimir(res)
    return 1 if res["errores"] else 0


def cmd_word(a) -> int:
    ruta_json = Path(a.tweets)
    tweets = rutas.cargar_json(ruta_json)
    reglas = rutas.cargar_reglas()
    hoy = date.fromisoformat(tweets["fecha"]) if tweets.get("fecha") else rutas.hoy_ar()
    res = validar.validar(tweets, reglas, historial.recientes(reglas["historial_dias"], hoy=hoy), _titulares(a.titulares))
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


def cmd_fusionar(a) -> int:
    ruta = Path(a.tweets)
    tweets = rutas.cargar_json(ruta)
    veredictos = rutas.cargar_json(Path(a.verificacion))
    if not isinstance(veredictos, list):
        raise ValueError("el archivo de verificacion debe ser una lista")
    tweets, problemas = verificacion.fusionar(tweets, veredictos)
    rutas.guardar_json(ruta, tweets)
    cuentas = {}
    for it in tweets["items"]:
        e = it["verificacion"]["estado"]
        cuentas[e] = cuentas.get(e, 0) + 1
    print("Verificacion fusionada: " + ", ".join(f"{k}={v}" for k, v in sorted(cuentas.items())))
    for p in problemas:
        print("  aviso:", p)
    return 0


def cmd_hoy(a) -> int:
    print(rutas.hoy_ar().isoformat())
    return 0


def cmd_historial(a) -> int:
    hist = historial.recientes(a.dias, hoy=rutas.hoy_ar() if not a.hasta else date.fromisoformat(a.hasta))
    for h in hist:
        print(f"{h['fecha']}  {h.get('id', ''):>4}  {h['texto'][:100]}")
    print(f"{len(hist)} textos en los ultimos {a.dias} dias")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Herramientas de la skill /tweets-nohuddle")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doctor"); d.add_argument("--red", action="store_true"); d.set_defaults(f=cmd_doctor)
    f = sub.add_parser("fuentes"); f.add_argument("--horas", type=int, default=36); f.add_argument("--salida"); f.set_defaults(f=cmd_fuentes)
    v = sub.add_parser("validar"); v.add_argument("tweets"); v.add_argument("--titulares"); v.set_defaults(f=cmd_validar)
    w = sub.add_parser("word"); w.add_argument("tweets"); w.add_argument("--titulares"); w.add_argument("--salida"); w.add_argument("--forzar", action="store_true"); w.set_defaults(f=cmd_word)
    sub.add_parser("hoy").set_defaults(f=cmd_hoy)
    m = sub.add_parser("fusionar"); m.add_argument("tweets"); m.add_argument("verificacion"); m.set_defaults(f=cmd_fusionar)
    h = sub.add_parser("historial"); h.add_argument("--dias", type=int, default=7); h.add_argument("--hasta"); h.set_defaults(f=cmd_historial)
    a = p.parse_args(argv)
    try:
        return a.f(a)
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
