import unittest

from tests import base  # noqa: F401
from nh import texto


class TestTexto(unittest.TestCase):
    def test_url_cuenta_23(self):
        t = "Mirá esto https://www.espn.com/nfl/story/_/id/50380155/countering-peanut-punch-james-cook-skattebo ya"
        self.assertEqual(texto.largo_x(t), len("Mirá esto  ya") + 23)

    def test_emoji_cuenta_2(self):
        self.assertEqual(texto.largo_x("a🔥"), 3)

    def test_acentos_y_enie_cuentan_1(self):
        self.assertEqual(texto.largo_x("ñandú último"), 12)

    def test_hashtags_y_emojis(self):
        self.assertEqual(texto.contar_hashtags("Gran día #NFL #Cowboys"), 2)
        self.assertEqual(texto.contar_hashtags("link https://x.com/a#frag"), 0)
        self.assertEqual(texto.contar_emojis("ok 🔥🏈"), 2)

    def test_jaccard_distingue_parecidos(self):
        a = "Josh Jacobs to have surgery on fractured finger, out indefinitely"
        b = "LaFleur: Packers RB Jacobs needs surgery on finger"
        c = "Todd Monken not ready to name starter at QB for Week 10"
        self.assertGreater(texto.jaccard(a, b), texto.jaccard(a, c))
        self.assertEqual(texto.jaccard(a, a), 1.0)

    def test_gritos_ignoran_siglas(self):
        self.assertEqual(texto.palabras_en_mayusculas("La NFL y ESPN dicen NCAA"), 0)
        self.assertEqual(texto.palabras_en_mayusculas("INCREÍBLE lo de ayer, URGENTE"), 2)

    def test_decimal_con_punto(self):
        self.assertIsNotNone(texto.DECIMAL_PUNTO_RE.search("promedia 4.8 yardas"))
        self.assertIsNone(texto.DECIMAL_PUNTO_RE.search("promedia 4,8 yardas"))
        self.assertIsNone(texto.DECIMAL_PUNTO_RE.search("tiene 15.269 yardas"))
        self.assertIsNone(texto.DECIMAL_PUNTO_RE.search("mirá nfl.com/news"))


if __name__ == "__main__":
    unittest.main()
