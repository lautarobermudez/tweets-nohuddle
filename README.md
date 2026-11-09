# tweets-nohuddle

Skill de Claude Code que arma cada mañana la planilla (Word) de tweets e hilos del día para la cuenta de X de No Huddle (@nflnohuddle): NFL y college football, a partir de medios prestigiosos e insiders de la NFL, en una sola pasada y con pocos tokens, y nada publicado sin una persona.

- **Para quien la usa:** [INSTALAR.md](INSTALAR.md).
- **Diseño y decisiones de delegación:** [PLAN_DELEGACION.md](PLAN_DELEGACION.md).

## Cómo funciona (modo liviano, por defecto)
```
tweets.py fuentes ──► digest.md  (~2.000 tokens: historias ordenadas por cuántos medios las cubren + partidos en hora de Argentina)
        │                 └─ candidatos.json (datos completos; no se lee, solo se consulta)
Agente redacta en UNA pasada leyendo solo el digest ──► tweets.json
        │
tweets.py word ──► valida (280, repetidos, tono, horarios, fuente nombrada) ──► Word + historial
```
**Criterio:** la curaduría ya la hacen los medios prestigiosos y los insiders de la NFL, así que no se re-verifica: se resume lo que publicaron y **se les atribuye en el texto** ("según ESPN", "Schefter reporta"). El costo por corrida es de ~8.000 a 10.000 tokens.

**Modos opcionales** (solo si se piden, ver `references/opcional/`): *con verificación* (subagente independiente, ~70.000 tokens por ronda) y *profundo* (2 subagentes buscadores que abren las notas, ~80.000 tokens cada uno). Las reglas estrictas (`exigir_doble_fuente`, `verificacion_obligatoria`) se encienden en `config/reglas.json`.

Los pasos mecánicos son **scripts** (rápidos, repetibles, con tests); el modelo solo hace lo que requiere criterio: elegir y redactar.

## Estructura
```
skills/tweets-nohuddle/
  SKILL.md                 procedimiento que sigue el agente
  config/fuentes.json      medios, feeds, insiders (editable)
  config/reglas.json       límites y reglas de validación (editable)
  references/              estilo y formato JSON (cortos); opcional/ = prompts de verificador y buscadores
  scripts/tweets.py        CLI: doctor | hoy | fuentes | validar | word | historial | fusionar (modo con verificación)
  scripts/nh/              módulos (solo biblioteca estándar, Python 3.8+)
tests/                     62 tests (unittest)
instalar.py                instalador (Windows/Mac/Linux)
```

## Decisiones de ingeniería
- **Sin dependencias:** solo la biblioteca estándar. El Word se arma a mano (un .docx es un zip de XML) para no pedirle instalar nada a quien la usa.
- **Tolerante a fallos:** un feed caído no frena la corrida; queda anotado en el digest.
- **Contrato explícito:** `references/formato_tweets.md` define el JSON entre el agente y los scripts; si no cumple, el validador lo dice con un mensaje claro.
- **Costo controlado:** el script resume los datos (digest de ~2.000 tokens en vez de 156 KB) y el agente no abre notas ni lanza subagentes salvo que se le pida. En los modos opcionales, quien escribe no verifica y lo no verificado nunca queda como OK.
- **Idempotente:** correr dos veces el mismo día reemplaza la corrida en el historial, no la duplica. Escrituras atómicas.
- **Determinista donde se puede:** conteo de caracteres como lo cuenta X (links = 23, emojis = 2), repetidos, tono, horarios y que el texto nombre su fuente los chequea código, no el modelo.
- **Datos fuera del código:** medios y reglas en `config/`; tono y criterios en `references/`.

## Pruebas
```
python3 -m unittest discover -s tests -t .
```
Los tests usan datos de muestra (sin red) y una carpeta temporal: nunca tocan datos reales.

## Pendiente / ideas
- USA Today y Sports Illustrated no tienen feed accesible hoy: se cubren con búsqueda web por dominio. Si aparece un feed estable, se suma en `config/fuentes.json`.
- Imágenes propias, métricas de qué tweets rindieron, programación por API de X (plan pago).
