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
    def test_genera_digest_plan_y_brief(self):
        r = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA)
        self.assertTrue(r["digest"].exists())
        self.assertTrue(r["tweets"].exists())
        plan_json = json.loads(r["tweets"].read_text(encoding="utf-8"))
        self.assertTrue(plan_json["items"])
        for esperado in ("PLAN DEL DIA", "=== DIGEST ===", "=== ESTILO ===", "NO cites fuentes", "tweets.py cerrar", "Jacobs"):
            self.assertIn(esperado, r["brief"])

    def test_no_pisa_lo_ya_completado_el_mismo_dia(self):
        r = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA)
        d = json.loads(r["tweets"].read_text(encoding="utf-8"))
        d["items"][0]["textos"] = ["texto ya escrito"]
        r["tweets"].write_text(json.dumps(d), encoding="utf-8")
        r2 = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA)
        self.assertTrue(r2["reutilizado"])
        self.assertEqual(json.loads(r2["tweets"].read_text(encoding="utf-8"))["items"][0]["textos"], ["texto ya escrito"])
        r3 = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA, nuevo=True)
        self.assertFalse(r3["reutilizado"])
        self.assertEqual(json.loads(r3["tweets"].read_text(encoding="utf-8"))["items"][0]["textos"], [])

    def test_sin_ningun_medio_da_un_mensaje_claro(self):
        def caido(url):
            raise rss.FuenteError("sin internet")
        with self.assertRaises(flujo.FlujoError) as cm:
            flujo.preparar(fetch=caido, ahora=self.AHORA)
        self.assertIn("ningun medio", str(cm.exception))


class TestCerrar(ConCarpeta):
    def _completar(self, r, textos):
        d = json.loads(r["tweets"].read_text(encoding="utf-8"))
        for i, (txt, fuente) in zip(d["items"], textos):
            i["textos"] = [txt] if i["tipo"] == "tweet" else [txt, txt + " Segundo post distinto del hilo."]
            i["fuentes"] = [{"medio": fuente, "url": "https://www.espn.com/nfl/story/_/id/1"}]
        r["tweets"].write_text(json.dumps(d), encoding="utf-8")

    def test_flujo_completo(self):
        r = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA, todo_el_dia=True)
        self._completar(r, [("Josh Jacobs se opera de un dedo y no hay fecha de regreso.", "ESPN"),
                            ("Todd Monken no define el quarterback de los Browns para la Semana 10.", "Pro Football Talk")])
        out = flujo.cerrar(r["tweets"])
        self.assertEqual(out["errores"], [])
        self.assertTrue(out["word"].exists())
        self.assertEqual(len(out["tabla"]), 2)
        self.assertEqual(len(out["descartados"]), len(REGLAS["plan_diario"]["slots"]) - 2)
        self.assertEqual(out["tabla"][0][1:], ("tweet", "resultado", "ESPN"))

    def test_si_cita_una_fuente_no_arma_el_word(self):
        r = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA, todo_el_dia=True)
        self._completar(r, [("Según ESPN, Josh Jacobs se opera de un dedo.", "ESPN")])
        out = flujo.cerrar(r["tweets"])
        self.assertIn("cita_en_texto", [e["regla"] for e in out["errores"]])
        self.assertIsNone(out["word"])

    def test_sin_nada_completado_da_un_mensaje_claro(self):
        r = flujo.preparar(fetch=fetch_falso, ahora=self.AHORA)
        with self.assertRaises(flujo.FlujoError):
            flujo.cerrar(r["tweets"])

    def test_sin_preparar_antes(self):
        with self.assertRaises(flujo.FlujoError):
            flujo.cerrar(Path(self.tmp.name) / "no_existe.json")


if __name__ == "__main__":
    unittest.main()
