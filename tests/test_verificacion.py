import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import base
import tweets as cli
from nh import verificacion


class TestFusionar(unittest.TestCase):
    def test_asigna_estado_por_id(self):
        t, prob = verificacion.fusionar(base.tweets_ok(), [
            {"id": "t1", "estado": "OK"}, {"id": "t2", "estado": "ERROR", "detalle": "mal"}, {"id": "h1", "estado": "REVISAR", "detalle": "x"}])
        estados = {i["id"]: i["verificacion"]["estado"] for i in t["items"]}
        self.assertEqual(estados, {"t1": "OK", "t2": "ERROR", "h1": "REVISAR"})
        self.assertEqual(prob, [])

    def test_sin_veredicto_nunca_es_ok(self):
        t, prob = verificacion.fusionar(base.tweets_ok(), [{"id": "t1", "estado": "OK"}])
        estados = {i["id"]: i["verificacion"]["estado"] for i in t["items"]}
        self.assertEqual(estados["t2"], "REVISAR")
        self.assertEqual(estados["h1"], "REVISAR")
        self.assertEqual(len(prob), 2)

    def test_estado_raro_y_id_inexistente(self):
        t, prob = verificacion.fusionar(base.tweets_ok(), [
            {"id": "t1", "estado": "TODO BIEN"}, {"id": "t2", "estado": "OK"}, {"id": "h1", "estado": "OK"}, {"id": "zzz", "estado": "OK"}, "basura"])
        self.assertEqual(t["items"][0]["verificacion"]["estado"], "REVISAR")
        self.assertTrue(any("zzz" in p for p in prob))
        self.assertTrue(any("mal formado" in p for p in prob))

    def test_cli_fusionar_escribe_el_archivo(self):
        with tempfile.TemporaryDirectory() as d:
            p, v = Path(d) / "t.json", Path(d) / "v.json"
            p.write_text(json.dumps(base.tweets_ok()), encoding="utf-8")
            v.write_text(json.dumps([{"id": "t1", "estado": "OK"}, {"id": "t2", "estado": "OK"}, {"id": "h1", "estado": "OK"}]), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(cli.main(["fusionar", str(p), str(v)]), 0)
            self.assertIn("OK=3", out.getvalue())
            self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["items"][1]["verificacion"]["estado"], "OK")


if __name__ == "__main__":
    unittest.main()
