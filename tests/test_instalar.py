import tempfile
import unittest
from pathlib import Path

from tests import base
import importlib.util

spec = importlib.util.spec_from_file_location("instalar", base.RAIZ / "instalar.py")
instalar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(instalar)


class TestInstalar(unittest.TestCase):
    def test_instala_y_la_copia_funciona(self):
        with tempfile.TemporaryDirectory() as d:
            dest = instalar.instalar(Path(d) / "skills")
            self.assertTrue((dest / "SKILL.md").exists())
            self.assertTrue((dest / "scripts" / "tweets.py").exists())
            self.assertTrue((dest / "config" / "fuentes.json").exists())
            self.assertFalse(list(dest.rglob("__pycache__")))

    def test_no_pisa_una_instalacion_sin_actualizar(self):
        with tempfile.TemporaryDirectory() as d:
            instalar.instalar(Path(d) / "skills")
            with self.assertRaises(SystemExit):
                instalar.instalar(Path(d) / "skills")

    def test_actualizar_deja_un_solo_respaldo_fuera_de_skills(self):
        with tempfile.TemporaryDirectory() as d:
            skills = Path(d) / "skills"
            dest = instalar.instalar(skills)
            (dest / "marca.txt").write_text("v1", encoding="utf-8")
            instalar.instalar(skills, actualizar=True)
            respaldo = Path(d) / "skills-respaldo" / "tweets-nohuddle"
            self.assertTrue((respaldo / "marca.txt").exists())
            self.assertFalse((skills / "tweets-nohuddle" / "marca.txt").exists())
            instalar.instalar(skills, actualizar=True)  # segunda vez: reemplaza el respaldo, no acumula
            self.assertEqual([p.name for p in skills.iterdir()], ["tweets-nohuddle"], "no debe quedar nada extra dentro de skills")


if __name__ == "__main__":
    unittest.main()
