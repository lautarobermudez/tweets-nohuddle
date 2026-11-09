"""Utilidades de texto: normalizar, comparar parecidos y contar como cuenta X."""
from __future__ import annotations

import re
import unicodedata

URL_RE = re.compile(r"https?://\S+")
HASHTAG_RE = re.compile(r"(?<!\w)#\w+", re.UNICODE)
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U00002B50\U00002B55\U0001F000-\U0001F2FF\U00002190-\U000021FF]"
)
# Numeros con 1-2 decimales y punto (4.8): en este medio se escribe con coma (4,8).
DECIMAL_PUNTO_RE = re.compile(r"(?<![\w./:])\d+\.\d{1,2}(?![\d.\w])")

STOPWORDS = set(
    "a al algo and are as at by con de del el ella ellos en es esta este esto for from fue ha han has he in is it its la las le lo los me mi mas "
    "no nos o of on or para por que se si sin sobre su sus the to un una uno y ya was will with after over into their his her this that they "
    "not out have has had been being could would there when what who how why new says said week "
    "starter name ready trade deadline injury update updates news live rumors rumor tracker report reports latest grading grades game games "
    "season nfl football team teams coach coaches player players ahead against before first second another more most just".split()
)


def normalizar(texto: str) -> str:
    """Minusculas, sin acentos ni signos."""
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = URL_RE.sub(" ", t)
    return re.sub(r"[^a-z0-9\s]", " ", t)


def tokens(texto: str) -> set:
    return {w for w in normalizar(texto).split() if len(w) > 2 and w not in STOPWORDS}


def jaccard(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def entidades(texto: str) -> set:
    """Nombres propios: palabras con mayuscula inicial.

    La primera palabra de la frase solo cuenta si va seguida de otra con mayuscula (un nombre como
    "Todd Monken" o "Josh Jacobs"); si no, es solo la mayuscula de inicio de oracion.
    """
    palabras = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ'’\-]+", texto)
    out = set()
    for i, p in enumerate(palabras):
        if not p[:1].isupper() or len(p) <= 2:
            continue
        if i == 0 and not (len(palabras) > 1 and palabras[1][:1].isupper()):
            continue
        out.add(normalizar(p).strip())
    return out - {""}


def _peso(c: str) -> int:
    o = ord(c)
    # Rangos que X cuenta como 1 (config oficial de twitter-text); el resto cuenta 2.
    if o <= 4351 or 8192 <= o <= 8205 or 8208 <= o <= 8223 or 8242 <= o <= 8247:
        return 1
    return 2


def largo_x(texto: str, largo_url: int = 23) -> int:
    """Largo ponderado como lo cuenta X: cada URL vale 23; los emojis y CJK valen 2."""
    sin_urls = URL_RE.sub("", texto)
    return len(URL_RE.findall(texto)) * largo_url + sum(_peso(c) for c in sin_urls)


def contar_hashtags(texto: str) -> int:
    return len(HASHTAG_RE.findall(URL_RE.sub("", texto)))


def contar_emojis(texto: str) -> int:
    return len(EMOJI_RE.findall(texto))


SIGLAS = {"NFLPA", "NCAAF", "ACCCG", "SUPER", "BOWL"}


def palabras_en_mayusculas(texto: str) -> int:
    """Palabras GRITADAS de 5+ letras (las siglas de 2-4 letras como NFL, ESPN o NCAA no cuentan)."""
    sin = URL_RE.sub("", texto)
    return len([w for w in re.findall(r"\b[A-ZÁÉÍÓÚÑ]{5,}\b", sin) if w not in SIGLAS])
