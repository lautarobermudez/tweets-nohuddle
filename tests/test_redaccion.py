import unittest

from tests import base  # noqa: F401
from nh import redaccion, tiempo
from datetime import datetime, timezone

PLAN = {"fecha": "2026-11-09", "items": [
    {"id": "t1", "tipo": "tweet", "liga": "NFL", "categoria": "lesion", "hora": "09:00", "textos": [], "fuentes": []},
    {"id": "t2", "tipo": "tweet", "liga": "College", "categoria": "college", "hora": "10:00", "textos": [], "fuentes": []},
    {"id": "h1", "tipo": "hilo", "liga": "NFL", "categoria": "analisis", "hora": "11:00", "textos": [], "fuentes": []}]}
INDICE = {"N1": {"fuentes": [{"medio": "ESPN", "url": "https://espn/1"}, {"medio": "CBS Sports", "url": "https://cbs/1"}]},
          "N2": {"fuentes": [{"medio": "ESPN", "url": "https://espn/1"}]},
          "C1": {"fuentes": [{"medio": "ESPN", "url": "https://espn/c1"}]}}


class TestParser(unittest.TestCase):
    def test_lineas_hilos_comentarios_y_horario(self):
        e, p = redaccion.parsear("﻿# nota\n\nt1 | N1,n2 | Texto uno | con barra\nt2@12:30 | - | Texto dos\nh1 | N1 | Post 1 con https://x.com/a\n+ Post 2\n+   \n+ Post 3\n")
        self.assertEqual(p, [])
        self.assertEqual([x["id"] for x in e], ["t1", "t2", "h1"])
        self.assertEqual(e[0]["historias"], ["N1", "N2"])
        self.assertEqual(e[0]["posts"], ["Texto uno | con barra"])  # solo se parte en las 2 primeras barras
        self.assertEqual((e[1]["hora"], e[1]["historias"]), ("12:30", []))
        self.assertEqual(e[2]["posts"], ["Post 1 con https://x.com/a", "Post 2", "Post 3"])  # las URLs no rompen nada

    def test_problemas_con_numero_de_linea(self):
        _, p = redaccion.parsear("+ huerfana\nsin barras\n!!@25:99 | - | x\n")
        self.assertEqual(len(p), 3)
        self.assertIn("linea 1", p[0])
        self.assertIn("linea 2", p[1])
        self.assertIn("invalido", p[2])


class TestAplicar(unittest.TestCase):
    def test_resuelve_fuentes_sin_duplicar_y_no_muta_el_plan(self):
        e, _ = redaccion.parsear("t1 | N1,N2 | Texto.\nt2 | - | Otro.")
        t, p = redaccion.aplicar(PLAN, e, INDICE)
        self.assertEqual(p, [])
        self.assertEqual([f["url"] for f in t["items"][0]["fuentes"]], ["https://espn/1", "https://cbs/1"])  # espn/1 no se repite
        self.assertEqual(t["items"][1]["fuentes"][0]["url"], "https://www.espn.com/college-football/scoreboard")
        self.assertEqual(PLAN["items"][0]["textos"], [])  # el plan original no se toca

    def test_tweet_con_varios_posts_pasa_a_hilo_y_viceversa(self):
        e, _ = redaccion.parsear("t1 | N1 | a\n+ b\nh1 | N1 | solo uno")
        t, _ = redaccion.aplicar(PLAN, e, INDICE)
        self.assertEqual(t["items"][0]["tipo"], "hilo")
        self.assertEqual(t["items"][2]["tipo"], "tweet")

    def test_problemas_de_ids(self):
        e, _ = redaccion.parsear("t1 | N77 | a\nt99 | - | b\nt2 | - | c\nt2 | - | d")
        _, p = redaccion.aplicar(PLAN, e, INDICE)
        texto = " ".join(p)
        self.assertIn("N77", texto)
        self.assertIn("slot desconocido", texto)
        self.assertIn("mas de una vez", texto)

    def test_cambia_el_horario(self):
        e, _ = redaccion.parsear("t1@14:45 | N1 | a")
        t, _ = redaccion.aplicar(PLAN, e, INDICE)
        self.assertEqual(t["items"][0]["hora"], "14:45")


class TestTiempo(unittest.TestCase):
    def test_hoy_ar_usa_utc_menos_3(self):
        self.assertEqual(tiempo.hoy_ar(datetime(2026, 11, 10, 2, 59, tzinfo=timezone.utc)).isoformat(), "2026-11-09")
        self.assertEqual(tiempo.hoy_ar(datetime(2026, 11, 10, 3, 0, tzinfo=timezone.utc)).isoformat(), "2026-11-10")

    def test_hora_ar(self):
        d = tiempo.hora_ar("2026-11-10T01:15Z")
        self.assertEqual((d.day, d.hour, d.minute), (9, 22, 15))
        self.assertIsNone(tiempo.hora_ar("basura"))


if __name__ == "__main__":
    unittest.main()
