"""Historial, Word y CLI de punta a punta, siempre en una carpeta temporal (nunca toca datos reales)."""
import contextlib
import io
import json
import os
import tempfile
import unittest
import zipfile
import xml.dom.minidom
from datetime import date
from pathlib import Path

from tests import base
import tweets as cli
from nh import historial, rutas, wordgen


class ConCarpetaTemporal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.prev = os.environ.get("NH_TWEETS_DIR")
        os.environ["NH_TWEETS_DIR"] = self.tmp.name

    def tearDown(self):
        if self.prev is None:
            os.environ.pop("NH_TWEETS_DIR", None)
        else:
            os.environ["NH_TWEETS_DIR"] = self.prev
        self.tmp.cleanup()

    def correr(self, *args):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = cli.main(list(args))
        return codigo, salida.getvalue()


class TestHistorial(ConCarpetaTemporal):
    def test_agregar_es_idempotente_por_fecha(self):
        t = base.tweets_ok()
        historial.agregar(t)
        historial.agregar(t)
        self.assertEqual(len(historial.cargar()), 5)  # 1 + 1 + 3 posts del hilo, una sola vez

    def test_recientes_excluye_hoy_y_lo_viejo(self):
        rutas.guardar_json(rutas.historial_path(), [
            {"fecha": "2026-11-10", "texto": "hoy"},
            {"fecha": "2026-11-09", "texto": "ayer"},
            {"fecha": "2026-10-01", "texto": "viejo"},
        ])
        r = historial.recientes(7, hoy=date(2026, 11, 10))
        self.assertEqual([e["texto"] for e in r], ["ayer"])

    def test_historial_danado_no_frena(self):
        rutas.historial_path().write_text("{no es json", encoding="utf-8")
        self.assertEqual(historial.cargar(), [])
        self.assertTrue(rutas.historial_path().with_suffix(".json.bak").exists())


class TestWord(ConCarpetaTemporal):
    def test_docx_valido_y_con_el_contenido(self):
        destino = Path(self.tmp.name) / "x.docx"
        wordgen.armar_docx(base.tweets_ok(), rutas.cargar_reglas(), destino, [{"id": "t2", "mensaje": "falta segunda fuente"}])
        with zipfile.ZipFile(destino) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(z.namelist()[0], "[Content_Types].xml")
            for nombre in z.namelist():
                xml.dom.minidom.parseString(z.read(nombre))  # todo XML bien formado
            doc = z.read("word/document.xml").decode("utf-8")
        for esperado in ("Josh Jacobs se opera", "Martes 10/11/2026", "2 tweets y 1 hilo ", "Post 2 de 3", "falta segunda fuente", "Fuente: ESPN"):
            self.assertIn(esperado, doc)
        # orden por hora: 09:00 antes que 19:00
        self.assertLess(doc.index("09:00 · TWEET"), doc.index("19:00 · HILO"))

    def test_escapa_caracteres_especiales(self):
        t = base.tweets_ok()
        t["items"][0]["textos"][0] = "Rojos & Azules <3 \"comillas\" y ñ"
        destino = Path(self.tmp.name) / "y.docx"
        wordgen.armar_docx(t, rutas.cargar_reglas(), destino)
        with zipfile.ZipFile(destino) as z:
            xml.dom.minidom.parseString(z.read("word/document.xml"))

    def test_python_docx_lo_abre_si_esta_instalado(self):
        try:
            import docx
        except ImportError:
            self.skipTest("python-docx no instalado (es solo una verificacion extra)")
        destino = Path(self.tmp.name) / "z.docx"
        wordgen.armar_docx(base.tweets_ok(), rutas.cargar_reglas(), destino)
        d = docx.Document(str(destino))
        self.assertTrue(any("Tweets del día" in p.text for p in d.paragraphs))


class TestCLI(ConCarpetaTemporal):
    def _guardar(self, t):
        p = Path(self.tmp.name) / "tweets.json"
        p.write_text(json.dumps(t), encoding="utf-8")
        return str(p)

    def test_flujo_completo_valido(self):
        codigo, out = self.correr("word", self._guardar(base.tweets_ok()))
        self.assertEqual(codigo, 0, out)
        self.assertTrue((rutas.dia_dir("2026-11-10") / "Tweets No Huddle - 10-11-2026.docx").exists())
        self.assertIn("Historial actualizado", out)
        self.assertEqual(len(historial.cargar()), 5)  # t1 + t2 + 3 posts del hilo h1

    def test_con_errores_no_arma_word_ni_toca_historial(self):
        t = base.tweets_ok()
        t["items"][0]["textos"][0] = "x" * 300
        codigo, out = self.correr("word", self._guardar(t))
        self.assertEqual(codigo, 1)
        self.assertIn("No armo el Word", out)
        self.assertEqual(historial.cargar(), [])

    def test_forzar_arma_igual_pero_no_registra_historial(self):
        t = base.tweets_ok()
        t["items"][0]["textos"][0] = "x" * 300
        codigo, _ = self.correr("word", self._guardar(t), "--forzar")
        self.assertEqual(codigo, 1)
        self.assertTrue((rutas.dia_dir("2026-11-10") / "Tweets No Huddle - 10-11-2026.docx").exists())
        self.assertEqual(historial.cargar(), [])

    def test_archivo_inexistente_codigo_2(self):
        self.assertEqual(self.correr("validar", "/no/existe.json")[0], 2)

    def test_doctor_sin_red(self):
        codigo, out = self.correr("doctor")
        self.assertEqual(codigo, 0, out)
        self.assertIn("Todo listo", out)


if __name__ == "__main__":
    unittest.main()
