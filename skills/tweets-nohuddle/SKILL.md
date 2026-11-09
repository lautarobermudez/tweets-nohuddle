---
name: tweets-nohuddle
description: Arma cada mañana los tweets e hilos del día para la cuenta de X de No Huddle (@nflnohuddle) sobre NFL y college football, a partir de los medios prestigiosos. Un script junta las fuentes y arma el plan del día; vos solo redactás los textos; otro script valida y deja un Word listo para copiar. Usar cuando pidan "los tweets del día", "armá los tweets de No Huddle", "contenido para X de No Huddle" o /tweets-nohuddle. NO publica nada.
user-invocable: true
---

# /tweets-nohuddle

Casi todo lo hacen los scripts. Vos solo redactás. Los scripts se corren con Python (`python3`; si no existe, `python`; en Windows, `py -3`). `SKILL_DIR` es la carpeta que muestra "Base directory" al cargar esta skill.

## Pasos

**1. Preparar**
```
PY SKILL_DIR/scripts/tweets.py preparar
```
Chequea todo, lee los medios y arma el plan del día. Imprime **todo lo que necesitás**: qué hacer, el plan (horarios y mezcla ya decididos), el resumen de noticias y la guía de estilo. Si falla, el mensaje dice por qué: explicáselo al usuario en palabras simples y frená.

**2. Redactar**
Abrí el archivo que indica la salida (`tweets.json`) y completá `textos` y `fuentes` de cada slot, como dice la salida. Nada más.

**3. Cerrar**
```
PY SKILL_DIR/scripts/tweets.py cerrar
```
Valida, arma el Word y actualiza el historial. Si marca **errores**, corregilos en `tweets.json` y repetí `cerrar`.

**4. Entregar**
Mostrale al usuario la ruta del Word y el resumen que imprimió `cerrar`. Nada se publica: lo revisa y programa una persona.

## Reglas
- Escribís como **medio propio**: **nunca cites** fuentes en el texto (nada de "según…", "reporta…" ni nombres de insiders). La fuente va solo en el campo `fuentes`.
- Usá solo lo que dice el resumen. No inventes datos, cifras ni citas.
- No publiques ni programes nada.

## Opcionales (solo si te los piden)
- **"Con verificación":** un subagente independiente chequea los datos (`references/opcional/prompt_verificador.md`; el veredicto se une con `tweets.py fusionar tweets.json verificacion.json`). Gasta ~70.000 tokens.
- **"Modo profundo":** buscadores que abren las notas (`references/opcional/prompt_buscador.md`). Gasta ~80.000 tokens cada uno.
