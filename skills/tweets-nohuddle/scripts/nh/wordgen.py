"""Genera el Word con los tweets listos para copiar. Sin dependencias: arma el .docx a mano (un .docx es un zip de XML).

Asi la skill funciona en cualquier PC con Python, sin instalar python-docx.
"""
from __future__ import annotations

import zipfile
from datetime import date
from pathlib import Path
from typing import List, Optional
from xml.sax.saxutils import escape

from . import texto

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
COLOR_ESTADO = {"OK": "2E7D32", "REVISAR": "B26A00", "ERROR": "C62828", None: "6B7280"}
CATEGORIA = {
    "resultado": "Resultado", "lesion": "Lesión", "transaccion": "Transacción", "college": "College",
    "dato": "Dato", "previa": "Previa", "analisis": "Análisis", "pregunta": "Pregunta",
}


def esc(t: str) -> str:
    return escape(t, {'"': "&quot;"})


def _run(t: str, bold=False, italic=False, size=None, color=None) -> str:
    rpr = ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "")
    rpr += f'<w:color w:val="{color}"/>' if color else ""
    rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>' if size else ""
    rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(t)}</w:t></w:r>'


def _p(runs: str, before=0, after=60, keep_next=False) -> str:
    keep = "<w:keepNext/>" if keep_next else ""
    return f'<w:p><w:pPr>{keep}<w:spacing w:before="{before}" w:after="{after}"/></w:pPr>{runs}</w:p>'


def _caja(parrafos: List[str]) -> str:
    borde = "".join(f'<w:{l} w:val="single" w:sz="6" w:space="0" w:color="9AA5B1"/>' for l in ("top", "left", "bottom", "right"))
    mar = "".join(f'<w:{l} w:w="{v}" w:type="dxa"/>' for l, v in (("top", 90), ("left", 160), ("bottom", 90), ("right", 160)))
    return (
        '<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/>'
        f"<w:tblBorders>{borde}</w:tblBorders><w:tblCellMar>{mar}</w:tblCellMar></w:tblPr>"
        '<w:tblGrid><w:gridCol w:w="9638"/></w:tblGrid>'
        '<w:tr><w:trPr><w:cantSplit/></w:trPr><w:tc><w:tcPr><w:tcW w:w="5000" w:type="pct"/>'
        '<w:shd w:val="clear" w:color="auto" w:fill="F5F7FA"/></w:tcPr>'
        + "".join(parrafos) + "</w:tc></w:tr></w:tbl>"
    )


def _fecha_larga(f: str) -> str:
    d = date.fromisoformat(f)
    return f"{DIAS[d.weekday()]} {d.day:02d}/{d.month:02d}/{d.year}"


def _cuerpo(tweets: dict, reglas: dict, avisos: Optional[List[dict]]) -> str:
    items = sorted(tweets["items"], key=lambda x: x.get("hora", "99:99"))
    n_t = sum(1 for i in items if i["tipo"] == "tweet")
    n_h = sum(1 for i in items if i["tipo"] == "hilo")
    out = [
        _p(_run("No Huddle · Tweets del día", bold=True, size=36, color="1F2937"), after=40),
        _p(_run(f"{_fecha_larga(tweets['fecha'])} · Hora de Argentina · {n_t} {'tweet' if n_t == 1 else 'tweets'} y {n_h} {'hilo' if n_h == 1 else 'hilos'}", size=22, color="6B7280"), after=200),
    ]

    agenda = tweets.get("agenda") or []
    if agenda:
        out.append(_p(_run("Agenda del día", bold=True, size=26, color="1F2937"), before=120, after=60))
        for a in agenda:
            out.append(_p(_run(f"{a.get('hora', '')}  ", bold=True, size=20) + _run(a.get("que", ""), size=20), after=30))

    pendientes = [a for a in (avisos or [])]
    if pendientes:
        out.append(_p(_run("Para revisar antes de publicar", bold=True, size=26, color="B26A00"), before=200, after=60))
        for a in pendientes:
            out.append(_p(_run(f"• {a['id']}: ", bold=True, size=19) + _run(a["mensaje"], size=19), after=20))

    out.append(_p(_run("Publicaciones", bold=True, size=26, color="1F2937"), before=240, after=80))
    for it in items:
        cat = CATEGORIA.get(it["categoria"], it["categoria"])
        prio = (it.get("prioridad") or "").upper()
        enc = f"{it['hora']} · {'HILO' if it['tipo'] == 'hilo' else 'TWEET'} · {it['liga']} · {cat}" + (f" · {prio}" if prio else "")
        out.append(_p(_run(enc, bold=True, size=20, color="1D4ED8"), before=160, after=40, keep_next=True))

        cuerpo = []
        for n, t in enumerate(it["textos"], 1):
            if it["tipo"] == "hilo":
                cuerpo.append(_p(_run(f"Post {n} de {len(it['textos'])}", bold=True, size=16, color="6B7280"), after=20))
            cuerpo.append(_p(_run(t, size=22), after=100 if n < len(it["textos"]) else 0))
        out.append(_caja(cuerpo))

        ver = it.get("verificacion") or {}
        est = ver.get("estado")
        largos = " / ".join(str(texto.largo_x(t, reglas["largo_url"])) for t in it["textos"])
        meta = _run(f"Caracteres: {largos} de {reglas['max_caracteres']}", size=16, color="6B7280")
        if est:  # solo si hubo verificacion (modo con verificacion)
            meta += _run(" · Verificación: ", size=16, color="6B7280") + _run(est, bold=True, size=16, color=COLOR_ESTADO.get(est, COLOR_ESTADO[None]))
            if ver.get("detalle"):
                meta += _run(f" ({ver['detalle']})", size=16, color="6B7280")
        out.append(_p(meta, before=40, after=20))
        for f in it.get("fuentes", []):
            out.append(_p(_run(f"Fuente interna (no citar): {f.get('medio', '')} — {f.get('url', '')}", size=16, color="6B7280"), after=10))
        if it.get("link_nota_nh"):
            out.append(_p(_run(f"Nota de No Huddle para linkear: {it['link_nota_nh']}", size=16, color="6B7280"), after=10))
        img = it.get("imagen") or {}
        if img.get("sugerencia"):
            cred = f" (crédito: {img['credito']})" if img.get("credito") else ""
            out.append(_p(_run(f"Imagen sugerida: {img['sugerencia']}{cred}", size=16, color="6B7280"), after=10))

    out.append(_p(_run("Generado con la skill /tweets-nohuddle. Nada se publica solo: revisá cada texto antes de programarlo.", italic=True, size=16, color="6B7280"), before=300))
    return "".join(out)


def armar_docx(tweets: dict, reglas: dict, ruta: Path, avisos: Optional[List[dict]] = None) -> Path:
    ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    documento = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:document {ns}><w:body>{_cuerpo(tweets, reglas, avisos)}"
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="567" w:footer="567" w:gutter="0"/>'
        "</w:sectPr></w:body></w:document>"
    )
    estilos = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:styles {ns}><w:docDefaults><w:rPrDefault><w:rPr>"
        '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri" w:eastAsia="Calibri"/>'
        '<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="es-AR"/></w:rPr></w:rPrDefault></w:docDefaults></w:styles>'
    )
    tipos = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    rels_doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        "</Relationships>"
    )
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".docx.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", tipos)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", documento)
        z.writestr("word/styles.xml", estilos)
        z.writestr("word/_rels/document.xml.rels", rels_doc)
    tmp.replace(ruta)
    return ruta
