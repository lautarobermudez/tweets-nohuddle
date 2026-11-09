import copy
import unittest

from tests import base
from nh import rutas, validar

REGLAS = rutas.cargar_reglas()  # modo liviano (por defecto)
ESTRICTAS = dict(REGLAS, exigir_doble_fuente=True, verificacion_obligatoria=True)
INSIDERS = rutas.cargar_fuentes()["insiders"]


def v(tweets, historial=None, titulares=None, reglas=None):
    return validar.validar(tweets, reglas or REGLAS, historial, titulares, INSIDERS)


def reglas_de(res, clave="errores"):
    return [e["regla"] for e in res[clave]]


class TestValidar(unittest.TestCase):
    def setUp(self):
        self.t = base.tweets_ok()

    def test_ejemplo_valido_no_tiene_errores(self):
        res = v(self.t)
        self.assertEqual(res["errores"], [], res["errores"])
        self.assertEqual(res["resumen"], {"tweets": 2, "hilos": 1})

    def test_pasarse_de_280(self):
        self.t["items"][0]["textos"][0] = "x" * 281
        self.assertIn("largo", reglas_de(v(self.t)))

    def test_corchetes_sin_completar(self):
        self.t["items"][0]["textos"][0] = "Se lesionó [jugador] hoy"
        self.assertIn("corchetes", reglas_de(v(self.t)))

    def test_modo_liviano_no_exige_doble_fuente(self):
        self.t["items"][0]["fuentes"] = self.t["items"][0]["fuentes"][:1]
        self.assertNotIn("doble_fuente", reglas_de(v(self.t)))
        self.assertEqual(v(self.t)["errores"], [])

    def test_modo_estricto_confirmado_exige_dos_medios(self):
        self.t["items"][0]["fuentes"] = self.t["items"][0]["fuentes"][:1]
        self.assertIn("doble_fuente", reglas_de(v(self.t, reglas=ESTRICTAS)))

    def test_modo_estricto_mismo_medio_dos_veces_no_cuenta_doble(self):
        it = self.t["items"][0]
        it["fuentes"] = [{"medio": "ESPN", "url": "https://a"}, {"medio": "ESPN", "url": "https://b"}]
        self.assertIn("doble_fuente", reglas_de(v(self.t, reglas=ESTRICTAS)))

    def test_sin_atribucion_ni_verificacion_es_valido_en_modo_liviano(self):
        for it in self.t["items"]:
            it.pop("atribucion", None)
            it.pop("verificacion", None)
        res = v(self.t)
        self.assertEqual(res["errores"], [])
        self.assertNotIn("verificacion", reglas_de(res, "avisos"))  # no molesta con 'sin verificar'
        self.assertIn("verificacion", reglas_de(v(self.t, reglas=ESTRICTAS), "avisos"))

    def test_el_texto_debe_nombrar_su_fuente(self):
        it = self.t["items"][0]
        it.pop("atribucion", None)
        it["textos"] = ["Josh Jacobs se opera de un dedo y no hay fecha de regreso."]
        self.assertIn("fuente_en_texto", reglas_de(v(self.t), "avisos"))
        it["textos"] = ["Según ESPN, Josh Jacobs se opera de un dedo y no hay fecha de regreso."]
        self.assertNotIn("fuente_en_texto", [a["regla"] for a in v(self.t)["avisos"] if a["id"] == "t1"])
        it["textos"] = ["Josh Jacobs se opera. Lo adelanta Pro Football Talk."]
        self.assertNotIn("fuente_en_texto", [a["regla"] for a in v(self.t)["avisos"] if a["id"] == "t1"])
        it["textos"] = ["Schefter: Josh Jacobs se opera de un dedo."]
        self.assertNotIn("fuente_en_texto", [a["regla"] for a in v(self.t)["avisos"] if a["id"] == "t1"])

    def test_alias_de_medio_por_siglas(self):
        it = self.t["items"][0]
        it.pop("atribucion", None)
        it["fuentes"] = [{"medio": "Pro Football Talk", "url": "https://x"}]
        it["textos"] = ["Josh Jacobs se opera de un dedo, adelanta PFT."]
        self.assertNotIn("fuente_en_texto", [a["regla"] for a in v(self.t)["avisos"] if a["id"] == "t1"])

    def test_las_preguntas_no_necesitan_fuente_en_el_texto(self):
        it = self.t["items"][0]
        it.pop("atribucion", None)
        it["categoria"] = "pregunta"
        it["textos"] = ["¿Quién llega mejor a enero?"]
        self.assertNotIn("fuente_en_texto", [a["regla"] for a in v(self.t)["avisos"] if a["id"] == "t1"])

    def test_reportado_exige_atribucion_en_el_texto(self):
        self.t["items"][1]["textos"][0] = "Los Jaguars adquirieron al safety Jessie Bates III."
        self.assertIn("atribucion", reglas_de(v(self.t)))

    def test_verificador_error_bloquea_y_revisar_avisa(self):
        self.t["items"][0]["verificacion"] = {"estado": "ERROR", "detalle": "marcador mal"}
        self.assertIn("verificacion", reglas_de(v(self.t)))
        t2 = base.tweets_ok()
        self.assertIn("verificacion", reglas_de(v(t2), "avisos"))  # el t2 trae REVISAR (sigue avisando si hay verificador)

    def test_hilo_con_un_solo_post(self):
        self.t["items"][2]["textos"] = ["solo uno"]
        self.assertIn("hilo", reglas_de(v(self.t)))

    def test_tweet_con_dos_textos(self):
        self.t["items"][0]["textos"].append("otro")
        self.assertIn("estructura", reglas_de(v(self.t)))

    def test_hora_invalida_y_fuera_de_ventana(self):
        self.t["items"][0]["hora"] = "25:00"
        self.assertIn("hora", reglas_de(v(self.t)))
        t2 = base.tweets_ok()
        t2["items"][0]["hora"] = "03:00"
        self.assertIn("hora", reglas_de(v(t2), "avisos"))

    def test_horarios_pegados(self):
        self.t["items"][1]["hora"] = "09:10"
        self.assertIn("hora", reglas_de(v(self.t), "avisos"))

    def test_repetido_contra_historial(self):
        hist = [{"fecha": "2026-11-08", "id": "t9", "texto": self.t["items"][0]["textos"][0]}]
        self.assertIn("repetido", reglas_de(v(self.t, hist)))

    def test_copia_de_titular(self):
        self.t["items"][0]["textos"][0] = "Josh Jacobs to have surgery on fractured finger out indefinitely"
        res = v(self.t, titulares=["Josh Jacobs to have surgery on fractured finger, out indefinitely"])
        self.assertIn("copia", reglas_de(res, "avisos"))

    def test_tono(self):
        self.t["items"][0]["textos"][0] = "INCREÍBLE!! No vas a creer lo de Jacobs, 4.8 yardas #NFL #Packers #Cowboys 🔥🏈"
        avisos = reglas_de(v(self.t), "avisos")
        for esperado in ("tono", "hashtags", "emojis", "numeros"):
            self.assertIn(esperado, avisos)

    def test_cantidad_fuera_de_rango_avisa(self):
        self.assertIn("cantidad", reglas_de(v(self.t), "avisos"))  # 2 tweets < 6

    def test_vacio_y_ids_repetidos(self):
        self.assertIn("estructura", reglas_de(v({"fecha": "2026-11-10", "items": []})))
        self.t["items"][1]["id"] = "t1"
        self.assertIn("estructura", reglas_de(v(self.t)))

    def test_no_muta_la_entrada(self):
        antes = copy.deepcopy(self.t)
        v(self.t)
        self.assertEqual(antes, self.t)


if __name__ == "__main__":
    unittest.main()
