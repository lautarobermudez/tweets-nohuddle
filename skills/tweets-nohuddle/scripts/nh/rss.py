"""Lectura de feeds RSS/Atom y de la API publica de ESPN. Tolerante a fallos: un feed roto no frena la corrida."""
from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Callable, List, Optional

USER_AGENT = "Mozilla/5.0 (compatible; NoHuddleTweets/1.0)"
ATOM = "{http://www.w3.org/2005/Atom}"


class FuenteError(Exception):
    """No se pudo leer una fuente (red, HTTP o formato)."""


def descargar(url: str, timeout: int = 20, reintentos: int = 2, espera: float = 1.5) -> bytes:
    """GET con reintentos. Devuelve bytes o levanta FuenteError con un motivo legible."""
    ultimo = None
    for intento in range(reintentos + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            ultimo = f"HTTP {e.code}"
            if e.code in (400, 401, 403, 404, 410):  # no tiene sentido reintentar
                break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            ultimo = f"red: {getattr(e, 'reason', e)}"
        if intento < reintentos:
            time.sleep(espera * (intento + 1))
    raise FuenteError(ultimo or "error desconocido")


def _fecha(txt: Optional[str]) -> Optional[datetime]:
    if not txt:
        return None
    txt = txt.strip()
    try:
        d = parsedate_to_datetime(txt)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(txt.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def _limpiar(texto_html: Optional[str]) -> str:
    if not texto_html:
        return ""
    t = re.sub(r"<[^>]+>", " ", texto_html)
    t = html.unescape(t)  # &#39; -> ' ; &amp; -> & (los feeds traen entidades HTML en los titulos y resumenes)
    return re.sub(r"\s+", " ", t).strip()


def parsear_feed(contenido: bytes) -> List[dict]:
    """RSS 2.0 y Atom -> lista de {titulo, link, publicado, resumen}. Levanta FuenteError si no es XML de feed."""
    try:
        raiz = ET.fromstring(contenido)
    except ET.ParseError as e:
        raise FuenteError(f"XML invalido: {e}")
    items = []
    for it in raiz.iter("item"):
        items.append({
            "titulo": _limpiar(it.findtext("title")),
            "link": (it.findtext("link") or "").strip(),
            "publicado": _fecha(it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")),
            "resumen": _limpiar(it.findtext("description"))[:400],
        })
    for it in raiz.iter(ATOM + "entry"):
        link = ""
        for l in it.findall(ATOM + "link"):
            if l.get("rel", "alternate") == "alternate":
                link = l.get("href", "")
                break
        items.append({
            "titulo": _limpiar(it.findtext(ATOM + "title")),
            "link": link.strip(),
            "publicado": _fecha(it.findtext(ATOM + "published") or it.findtext(ATOM + "updated")),
            "resumen": _limpiar(it.findtext(ATOM + "summary"))[:400],
        })
    if not items:
        raise FuenteError("el feed no trae items")
    return [i for i in items if i["titulo"] and i["link"]]


def parsear_scoreboard(contenido: bytes, liga: str) -> List[dict]:
    """JSON del scoreboard de ESPN -> partidos con estado y marcador."""
    try:
        datos = json.loads(contenido.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise FuenteError(f"JSON invalido: {e}")
    partidos = []
    for ev in datos.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        estado = (comp.get("status") or ev.get("status") or {}).get("type", {})
        equipos = []
        for c in comp.get("competitors", []):
            equipos.append({
                "equipo": (c.get("team") or {}).get("displayName", ""),
                "local": c.get("homeAway") == "home",
                "puntos": c.get("score"),
                "ganador": c.get("winner"),
            })
        partidos.append({
            "liga": liga,
            "nombre": ev.get("name", ""),
            "fecha_utc": ev.get("date", ""),
            "estado": estado.get("description", ""),
            "terminado": bool(estado.get("completed")),
            "equipos": equipos,
        })
    return partidos


Fetcher = Callable[[str], bytes]
