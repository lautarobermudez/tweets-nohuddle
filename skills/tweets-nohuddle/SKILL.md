---
name: tweets-nohuddle
description: Arma los tweets e hilos del día para la cuenta de X de No Huddle (NFL y college football) y deja un Word listo para copiar. Invocar a mano con /tweets-nohuddle.
argument-hint: "[con verificación | modo profundo]"
disable-model-invocation: true
model: sonnet
effort: low
allowed-tools:
  - Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/tweets.py *)
  - Bash(python ${CLAUDE_SKILL_DIR}/scripts/tweets.py *)
  - Bash(py -3 ${CLAUDE_SKILL_DIR}/scripts/tweets.py *)
---

# /tweets-nohuddle

Los scripts hacen casi todo; vos solo redactás. Se corren con `python3` (si no existe: `python`; en Windows: `py -3`).

## Pasos

1. **Preparar:** `python3 ${CLAUDE_SKILL_DIR}/scripts/tweets.py preparar`
   Chequea el entorno, lee los medios y arma el plan del día. Imprime **todo lo que necesitás**: el formato de redacción, el plan (horarios y mezcla ya decididos), el resumen de noticias y la guía de estilo. Si falla, el mensaje dice por qué: explicáselo al usuario en palabras simples y frená.
2. **Redactar:** escribí el archivo que indica la salida, una línea por publicación (`id | historias | texto`). Nada más.
3. **Cerrar:** `python3 ${CLAUDE_SKILL_DIR}/scripts/tweets.py cerrar`
   Valida, arma el Word y actualiza el historial. Si marca **errores**, corregí la redacción y repetí `cerrar`.
4. **Entregar:** mostrale al usuario la ruta del Word y el resumen que imprimió `cerrar`. Nada se publica: lo revisa y programa una persona.

## Reglas
- Escribís como **medio propio**: **nunca cites** fuentes en el texto (nada de "según…", "reporta…" ni nombres de insiders). La fuente se indica con los IDs de `historias`.
- Usá solo lo que dice el resumen. No inventes datos, cifras ni citas.
- No publiques ni programes nada.

## Opcionales
Pedido del usuario: $ARGUMENTS

Solo si pidió **"con verificación"**: un subagente independiente chequea los datos (`${CLAUDE_SKILL_DIR}/references/opcional/prompt_verificador.md`; el veredicto se une con `tweets.py fusionar tweets.json verificacion.json`). Si pidió **"modo profundo"**: buscadores que abren las notas (`${CLAUDE_SKILL_DIR}/references/opcional/prompt_buscador.md`). Ambos gastan decenas de miles de tokens.
