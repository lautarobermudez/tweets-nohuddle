"""Plan del dia y los dos pasos del flujo (preparar / cerrar), con datos de muestra y carpeta temporal."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests import base
import tweets as cli
from nh import flujo, plan, rss, rutas

REGLAS = rutas.cargar_reglas()


def fetch_falso(url):
    mapa = {"https://www.espn.com/espn/rss/nfl/news": "feed_espn.xml", "https://www.nbcsports.com/profootballtalk.rss": "feed_pft.xml",
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard": "scoreboard.json"}
    if url not in mapa:
        raise rss.FuenteError("HTTP 404")
    return base.fixture(mapa[url])


def horas(esq):
    return [i["hora"] for i in esq["items"]]


class TestPlan(unittest.TestCase):
    MANANA = datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc)  # 07:00 en Argentina

    def test_estructura_por_defecto(self):
        esq = plan.armar(REGLAS, [], self.MANANA)
        self.assertEqual(esq["fecha"], "2026-11-09")
        self.assertEqual(len(esq["items"]), len(REGLAS["plan_diario"]["slots"]))
        self.assertEqual([i["id"] for i in esq["items"] if i["tipo"] == "hilo"], ["h1", "h2"])
        for i in esq["items"]:
            self.assertEqual(i["textos"], [])
            self.assertEqual(i["fuentes"], [])

    def test_cumple_la_composicion_minima_de_las_reglas(self):
        esq = plan.armar(REGLAS, [], self.MANANA)
        cats = {i["categoria"] for i in esq["items"]}
        for c in ("resultado", "lesion", "transaccion", "college", "previa"):
            self.assertIn(c, cats)
        c = REGLAS["cantidad"]
        n_h = sum(1 for i in esq["items"] if i["tipo"] == "hilo")
        n_t = len(esq["items"]) - n_h
        self.assertTrue(c["tweets_min"] <= n_t <= c["tweets_max"])
        self.assertTrue(c["hilos_min"] <= n_h <= c["hilos_max"])

    def test_la_previa_se_mueve_al_partido_del_dia(self):
        partido = [{"liga": "NFL", "terminado": False, "fecha_utc": "2026-11-10T01:15Z", "nombre": "Bills at Vikings", "equipos": []}]  # 22:15 ART del 09/11
        esq = plan.armar(REGLAS, partido, self.MANANA)
        previa = [i for i in esq["items"] if i["categoria"] == "previa" and i["liga"] == "NFL"][0]
        self.assertEqual(previa["hora"], "20:45")  # 22:15 - 90 min

    def test_la_previa_no_se_mueve_antes_de_la_hora_minima(self):
        partido = [{"liga": "NFL", "terminado": False, "fecha_utc": "2026-11-09T14:00Z", "nombre": "Early", "equipos": []}]  # 11:00 ART
        esq = plan.armar(REGLAS, partido, self.MANANA)
        previa = [i for i in esq["items"] if i["categoria"] == "previa" and i["liga"] == "NFL"][0]
        self.assertGreaterEqual(previa["hora"], REGLAS["plan_diario"]["hora_minima_previa"])

    def test_un_partido_de_otro_dia_no_mueve_la_previa(self):
        partido = [{"liga": "NFL", "terminado": False, "fecha_utc": "2026-11-12T01:15Z", "nombre": "Jueves", "equipos": []}]
        base_ = plan.armar(REGLAS, [], self.MANANA)
        con = plan.armar(REGLAS, partido, self.MANANA)
        self.assertEqual(horas(base_), horas(con))

    def test_respeta_la_separacion_minima_y_la_ventana(self):
        partido = [{"liga": "NFL", "terminado": False, "fecha_utc": "2026-11-09T22:00Z", "nombre": "Tarde", "equipos": []}]  # 19:00 ART
        esq = plan.armar(REGLAS, partido, self.MANANA)
        hs = sorted(int(h[:2]) * 60 + int(h[3:]) for h in horas(esq))
        for a, b in zip(hs, hs[1:]):
            self.assertGreaterEqual(b - a, REGLAS["separacion_minima_minutos"])
        self.assertLessEqual(hs[-1], 23 * 60 + 30)

    def test_saltea_los_horarios_que_ya_pasaron(self):
        tarde = datetime(2026, 11, 9, 19, 0, tzinfo=timezone.utc)  # 16:00 ART
        esq = plan.armar(REGLAS, [], tarde)
        self.assertTrue(all(h >= "16:20" for h in horas(esq)))
        self.assertEqual(len(plan.armar(REGLAS, [], tarde, todo_el_dia=True)["items"]), len(REGLAS["plan_diario"]["slots"]))

    def test_limpiar_descarta_los_slots_vacios(self):
        t = {"items": [{"id": "t1", "textos": ["algo"]}, {"id": "t2", "textos": []}, {"id": "t3", "textos": ["  "]}]}
        t, desc = plan.limpiar(t)
        self.assertEqual([i["id"] for i in t["items"]], ["t1"])
        self.assertEqual(desc, ["t2", "t3"])


class ConCarpeta(unittest.TestCase):
    AHORA = datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.prev = os.environ.get("NH_TWEETS_DIR")
        os.environ["NH_TWEETS_DIR"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("NH_TWEETS_DIR", None) if self.prev is None else os.environ.update(NH_TWEETS_DIR=self.prev)
        self.tmp.cleanup()


class TestPreparar(ConCarpeta):
    def test_genera_digest_ids_plan_y_brief(self):
        r = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA)
        carpeta = r["digest"].parent
        for nombre in ("digest.md", "digest_ids.json", "plan.json", "candidatos.json"):
            self.assertTrue((carpeta / nombre).exists(), nombre)
        self.assertFalse(r["redaccion"].exists())  # lo escribe el agente (si existiera, Write exigiria leerlo antes)
        for esperado in ("PLAN DEL DIA", "=== DIGEST ===", "=== ESTILO ===", "id | historias | texto", "NO cites fuentes", "tweets.py cerrar", "Jacobs", "N1"):
            self.assertIn(esperado, r["brief"])
        self.assertNotIn("http", r["digest"].read_text(encoding="utf-8"))

    def test_no_pisa_el_plan_si_ya_hay_una_redaccion_del_dia(self):
        r = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA)
        r["redaccion"].write_text("t1 | N1 | Texto ya escrito.", encoding="utf-8")
        plan_antes = (r["digest"].parent / "plan.json").read_text(encoding="utf-8")
        mas_tarde = datetime(2026, 11, 9, 19, 0, tzinfo=timezone.utc)  # el plan nuevo saltearia horarios: no debe pasar
        r2 = flujo.preparar(fetch=fetch_falso, ahora=mas_tarde)
        self.assertTrue(r2["reutilizado"])
        self.assertEqual((r["digest"].parent / "plan.json").read_text(encoding="utf-8"), plan_antes)
        r3 = flujo.preparar(fetch=fetch_falso, ahora=mas_tarde, nuevo=True)
        self.assertFalse(r3["reutilizado"])
        self.assertFalse(r3["redaccion"].exists())

    def test_sin_ningun_medio_da_un_mensaje_claro(self):
        def caido(url):
            raise rss.FuenteError("sin internet")
        with self.assertRaises(flujo.FlujoError) as cm:
            flujo.preparar(fetch=caido, ahora=self.AHORA)
        self.assertIn("ningun medio", str(cm.exception))


class TestCerrar(ConCarpeta):
    def _preparado(self, redaccion_txt):
        r = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA, todo_el_dia=True)
        r["redaccion"].write_text(redaccion_txt, encoding="utf-8")
        return r

    def test_flujo_completo_con_ids_resueltos_por_el_script(self):
        r = self._preparado("# mi redaccion\nt1 | - | Dallas Cowboys le ganó 27-23 a Indianapolis Colts.\n"
                            "t2 | N1 | Josh Jacobs necesita una cirugía en un dedo y no hay fecha de regreso.\n"
                            "h1 | N1,N2 | Los Jaguars se mueven fuerte antes del deadline.\n+ Primero, el safety Jessie Bates III.\n+ Después, Jordan Davis.\n")
        out = flujo.cerrar()
        self.assertEqual(out["errores"], [])
        self.assertTrue(out["word"].exists())
        self.assertEqual(len(out["tabla"]), 3)
        tweets = json.loads((r["digest"].parent / "tweets.json").read_text(encoding="utf-8"))
        t2 = [i for i in tweets["items"] if i["id"] == "t2"][0]
        self.assertTrue(all(f["url"].startswith("http") for f in t2["fuentes"]))  # las URLs las puso el script
        t1 = [i for i in tweets["items"] if i["id"] == "t1"][0]
        self.assertEqual(t1["fuentes"][0]["medio"], "ESPN")  # sin historia: marcador de ESPN
        h1 = [i for i in tweets["items"] if i["id"] == "h1"][0]
        self.assertEqual((h1["tipo"], len(h1["textos"])), ("hilo", 3))
        self.assertEqual(len(out["descartados"]), len(REGLAS["plan_diario"]["slots"]) - 3)

    def test_si_cita_una_fuente_no_arma_el_word(self):
        self._preparado("t1 | N1 | Según ESPN, Josh Jacobs se opera de un dedo.")
        out = flujo.cerrar()
        self.assertIn("cita_en_texto", [e["regla"] for e in out["errores"]])
        self.assertIsNone(out["word"])

    def test_errores_de_formato_y_de_ids_bloquean_con_mensaje_claro(self):
        self._preparado("t1 | N99 | Texto con una historia inexistente.\nt99 | - | Slot que no existe.\nesto no tiene el formato")
        out = flujo.cerrar()
        mensajes = " ".join(e["mensaje"] for e in out["errores"])
        self.assertIn("N99", mensajes)
        self.assertIn("slot desconocido", mensajes)
        self.assertIn("formato esperado", mensajes)
        self.assertIsNone(out["word"])

    def test_se_puede_corregir_y_volver_a_cerrar(self):
        r = self._preparado("t1 | N1 | Según ESPN, Jacobs se opera.")
        self.assertIsNone(flujo.cerrar()["word"])
        r["redaccion"].write_text("t1 | N1 | Josh Jacobs se opera de un dedo y no hay fecha de regreso.", encoding="utf-8")
        self.assertIsNotNone(flujo.cerrar()["word"])

    def test_modo_manual_con_tweets_json_completo(self):
        r = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA, todo_el_dia=True)
        d = json.loads((r["digest"].parent / "plan.json").read_text(encoding="utf-8"))
        d["items"][0]["textos"] = ["Dallas Cowboys le ganó 27-23 a Indianapolis Colts."]
        d["items"][0]["fuentes"] = [{"medio": "ESPN", "url": "https://www.espn.com/nfl/scoreboard"}]
        ruta = r["digest"].parent / "tweets.json"
        ruta.write_text(json.dumps(d), encoding="utf-8")
        out = flujo.cerrar(ruta)
        self.assertEqual(out["errores"], [])
        self.assertTrue(out["word"].exists())

    def test_sin_nada_completado_da_un_mensaje_claro(self):
        self._preparado("# solo comentarios\n")
        with self.assertRaises(flujo.FlujoError):
            flujo.cerrar()

    def test_sin_preparar_antes(self):
        with self.assertRaises(flujo.FlujoError):
            flujo.cerrar()


if __name__ == "__main__":
    unittest.main()
