import json
import unittest
from datetime import datetime, timezone

from tests import base
from nh import fuentes, rss, rutas


class TestParseo(unittest.TestCase):
    def test_rss_limpia_html_y_parsea_fechas(self):
        items = rss.parsear_feed(base.fixture("feed_espn.xml"))
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["resumen"], "Josh Jacobs will have surgery.")
        self.assertEqual(items[0]["publicado"].tzinfo, timezone.utc)
        self.assertEqual(items[0]["publicado"].hour, 21)  # 16:50 EST = 21:50 UTC

    def test_atom(self):
        items = rss.parsear_feed(base.fixture("feed_atom.xml"))
        self.assertEqual(items[0]["link"], "https://example.com/a")
        self.assertEqual(items[0]["resumen"], "Indiana")

    def test_basura_levanta_fuente_error(self):
        with self.assertRaises(rss.FuenteError):
            rss.parsear_feed(b"<html><body>no soy un feed")
        with self.assertRaises(rss.FuenteError):
            rss.parsear_feed(b"<rss><channel></channel></rss>")

    def test_scoreboard(self):
        p = rss.parsear_scoreboard(base.fixture("scoreboard.json"), "NFL")
        self.assertEqual(len(p), 2)
        self.assertFalse(p[0]["terminado"])
        self.assertTrue(p[1]["terminado"])
        self.assertEqual(p[1]["equipos"][0]["puntos"], "24")


class TestRecolectar(unittest.TestCase):
    AHORA = datetime(2026, 11, 9, 23, 0, tzinfo=timezone.utc)

    def _fuentes(self):
        return {
            "feeds": [
                {"id": "espn", "medio": "ESPN", "tier": "A", "liga": "NFL", "url": "u/espn", "activo": True},
                {"id": "pft", "medio": "Pro Football Talk", "tier": "A", "liga": "NFL", "url": "u/pft", "activo": True},
                {"id": "roto", "medio": "Roto", "tier": "A", "liga": "NFL", "url": "u/roto", "activo": True},
                {"id": "apagado", "medio": "Apagado", "tier": "A", "liga": "NFL", "url": "u/apagado", "activo": False},
            ],
            "espn_api": [{"liga": "NFL", "url": "u/sb"}],
        }

    def _fetch(self, url):
        mapa = {"u/espn": "feed_espn.xml", "u/pft": "feed_pft.xml", "u/sb": "scoreboard.json"}
        if url not in mapa:
            raise rss.FuenteError("HTTP 404")
        return base.fixture(mapa[url])

    def test_un_feed_roto_no_frena_la_corrida(self):
        r = fuentes.recolectar(self._fuentes(), rutas.cargar_reglas(), ahora=self.AHORA, fetch=self._fetch)
        self.assertIn("espn", r["fuentes_ok"])
        self.assertEqual([e["id"] for e in r["fuentes_error"]], ["roto"])
        self.assertNotIn("apagado", r["fuentes_ok"])

    def test_filtra_ruido_y_viejos(self):
        r = fuentes.recolectar(self._fuentes(), rutas.cargar_reglas(), ahora=self.AHORA, fetch=self._fetch)
        titulos = [i["titulo"] for h in r["historias"] for i in h["items"]]
        self.assertFalse(any("BetMGM" in t for t in titulos))
        self.assertFalse(any("Old story" in t for t in titulos))
        self.assertEqual(r["descartados_por_ruido"], 1)

    def test_agrupa_la_misma_historia_de_dos_medios(self):
        r = fuentes.recolectar(self._fuentes(), rutas.cargar_reglas(), ahora=self.AHORA, fetch=self._fetch)
        top = r["historias"][0]
        self.assertEqual(top["n_medios"], 2)
        self.assertEqual(top["medios"], ["ESPN", "Pro Football Talk"])
        self.assertIn("Jacobs", top["titulo_guia"])
        self.assertEqual(len(r["partidos"]), 2)

    @staticmethod
    def _it(medio, titulo, liga="NFL"):
        return {"medio": medio, "tier": "A", "liga": liga, "titulo": titulo, "link": "https://x/" + titulo[:8], "publicado": "2026-11-09T20:00:00+00:00"}

    def test_regresion_no_encadena_historias_distintas(self):
        """Con datos reales: dos quarterbacks 'sin definir' de equipos distintos no son la misma historia."""
        items = [
            self._it("ESPN", "Hoosier QB? Cignetti not ready to name starter vs. USC", "College"),
            self._it("Pro Football Talk", "Todd Monken not ready to name starter at QB for Week 10"),
            self._it("CBS Sports", "Browns QB update: Todd Monken hasn't decided between Deshaun Watson and Shedeur Sanders"),
        ]
        h = fuentes.agrupar(items)
        indiana = [x for x in h if "Cignetti" in x["titulo_guia"]][0]
        self.assertEqual(indiana["n_medios"], 1)
        browns = [x for x in h if "Monken" in x["titulo_guia"]][0]
        self.assertEqual(browns["n_medios"], 2)

    def test_regresion_trades_distintos_no_se_unen_por_la_frase_generica(self):
        items = [
            self._it("ESPN", "Jets trade safety Cisco to injury-plagued Lions for draft pick"),
            self._it("Pro Football Talk", "Lions agree to acquire S Andre Cisco from Jets"),
            self._it("Yahoo Sports", "NFL trade deadline 2026: Denver Broncos latest news and rumors"),
        ]
        h = fuentes.agrupar(items)
        juntos = [x for x in h if x["n_medios"] > 1]
        self.assertEqual(len(juntos), 1)
        self.assertEqual(juntos[0]["medios"], ["ESPN", "Pro Football Talk"])
        self.assertTrue(any("Broncos" in x["titulo_guia"] and x["n_medios"] == 1 for x in h))

    def test_mismo_medio_con_varias_notas_cuenta_una_vez(self):
        items = [self._it("Yahoo Sports", "Josh Jacobs to have surgery on finger"), self._it("Yahoo Sports", "Josh Jacobs to have surgery on fractured finger")]
        h = fuentes.agrupar(items)
        self.assertEqual(len(h), 1)
        self.assertEqual(h[0]["n_medios"], 1)

    def test_todo_caido_devuelve_resultado_sin_levantar(self):
        def caido(url):
            raise rss.FuenteError("sin internet")
        r = fuentes.recolectar(self._fuentes(), rutas.cargar_reglas(), ahora=self.AHORA, fetch=caido)
        self.assertEqual(r["fuentes_ok"], [])
        self.assertEqual(r["historias"], [])
        json.dumps(r)  # tiene que ser serializable

    def test_digest_es_compacto_y_trae_lo_esencial(self):
        reglas = rutas.cargar_reglas()
        r = fuentes.recolectar(self._fuentes(), reglas, ahora=self.AHORA, fetch=self._fetch)
        d = fuentes.digest(r, reglas, ahora=self.AHORA)
        self.assertIn("## NFL", d)
        self.assertIn("## College", d)
        self.assertIn("[2]", d)  # la historia de Jacobs, cubierta por 2 medios
        self.assertIn("Jacobs", d)
        self.assertIn("Buffalo Bills at Minnesota Vikings (lun 09/11 22:15)", d)  # 01:15Z -> 22:15 hora de Argentina
        self.assertIn("Philadelphia Eagles 24", d)
        self.assertNotIn("BetMGM", d)
        self.assertLess(len(d), 3000)  # unos pocos cientos de tokens con datos de muestra

    def test_digest_incluye_siempre_los_proximos_aunque_haya_muchos_terminados(self):
        reglas = rutas.cargar_reglas()
        partidos = [{"liga": "NFL", "nombre": f"Terminado {i}", "fecha_utc": f"2026-11-08T{10 + i % 10}:00Z", "estado": "Final", "terminado": True,
                     "equipos": [{"equipo": f"A{i}", "puntos": "1"}, {"equipo": f"B{i}", "puntos": "2"}]} for i in range(30)]
        partidos.append({"liga": "NFL", "nombre": "Bills at Vikings", "fecha_utc": "2026-11-10T01:15Z", "estado": "Scheduled", "terminado": False, "equipos": []})
        res = {"historias": [], "fuentes_error": [{"medio": "USA Today"}, {"medio": "USA Today"}], "partidos": partidos}
        d = fuentes.digest(res, reglas, ahora=self.AHORA)
        self.assertIn("Bills at Vikings (lun 09/11 22:15)", d)
        self.assertEqual(d.count("USA Today"), 1)
        self.assertLessEqual(sum(1 for l in d.splitlines() if l.startswith("- NFL")), reglas["digest"]["max_partidos_por_liga"] + 6)

    def test_digest_respeta_los_topes(self):
        reglas = rutas.cargar_reglas()
        def nom(i):  # nombres solo con letras (el agrupador ignora los numeros) y todos distintos
            return chr(65 + i % 26) + chr(97 + i // 26) * 3 + chr(97 + (i * 7) % 26) * 2

        items = [{"medio": f"M{i}", "tier": "A", "liga": "NFL", "titulo": f"Eq{nom(i)} Ju{nom(i + 3)} firma contrato con Cl{nom(i + 9)}", "link": f"https://x/{i}",
                  "resumen": "r" * 500, "publicado": "2026-11-09T20:00:00+00:00"} for i in range(40)]
        res = {"historias": fuentes.agrupar(items), "fuentes_error": [], "partidos": []}
        d = fuentes.digest(res, reglas, ahora=self.AHORA)
        self.assertEqual(sum(1 for l in d.splitlines() if l[:3].strip().rstrip(".").isdigit()), reglas["digest"]["max_historias_nfl"])
        self.assertNotIn("r" * 200, d)  # los resumenes se cortan

    def test_config_real_es_valida(self):
        f = rutas.cargar_fuentes()
        ids = [x["id"] for x in f["feeds"]]
        self.assertEqual(len(ids), len(set(ids)), "ids de feed repetidos")
        for x in f["feeds"]:
            self.assertTrue(x["url"].startswith("https://"))
            self.assertIn(x["liga"], ("NFL", "College"))


if __name__ == "__main__":
    unittest.main()
