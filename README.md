# tweets-nohuddle

Skill de Claude Code que arma cada mañana la planilla (Word) de tweets e hilos del día para la cuenta de X de No Huddle (@nflnohuddle): NFL y college football, varios medios respetables, doble fuente, verificación independiente y nada publicado sin una persona.

- **Para quien la usa:** [INSTALAR.md](INSTALAR.md).
- **Diseño y decisiones de delegación:** [PLAN_DELEGACION.md](PLAN_DELEGACION.md).

## Cómo funciona
```
tweets.py fuentes ──► candidatos.json (titulares agrupados por historia, partidos de ESPN)
        │
2 subagentes buscadores (NFL y College, en paralelo) ──► historias_*.json (confirmadas con 2+ medios)
        │
Agente principal redacta (estilo + criterios) ──► tweets.json
        │
Subagente VERIFICADOR independiente ──► verificacion.json ──► tweets.py fusionar
        │
tweets.py word ──► valida (280, doble fuente, repetidos, tono, horarios) ──► Word + historial
```
Los pasos mecánicos son **scripts** (rápidos, repetibles, con tests); lo que requiere criterio lo hacen el agente y los subagentes, con control determinista alrededor.

## Estructura
```
skills/tweets-nohuddle/
  SKILL.md                 procedimiento que sigue el agente
  config/fuentes.json      medios, feeds, insiders (editable)
  config/reglas.json       límites y reglas de validación (editable)
  references/              estilo, criterios, formato JSON, prompts de los subagentes
  scripts/tweets.py        CLI: doctor | hoy | fuentes | fusionar | validar | word | historial
  scripts/nh/              módulos (solo biblioteca estándar, Python 3.8+)
tests/                     54 tests (unittest)
instalar.py                instalador (Windows/Mac/Linux)
```

## Decisiones de ingeniería
- **Sin dependencias:** solo la biblioteca estándar. El Word se arma a mano (un .docx es un zip de XML) para no pedirle instalar nada a quien la usa.
- **Tolerante a fallos:** un feed caído no frena la corrida; queda anotado y el buscador lo cubre con búsqueda web.
- **Contrato explícito:** `references/formato_tweets.md` define el JSON entre el agente y los scripts; si no cumple, el validador lo dice con un mensaje claro.
- **Quien escribe no verifica:** el verificador es un subagente aparte; el veredicto se fusiona por script, y lo que no se verificó nunca queda como OK.
- **Idempotente:** correr dos veces el mismo día reemplaza la corrida en el historial, no la duplica. Escrituras atómicas.
- **Determinista donde se puede:** conteo de caracteres como lo cuenta X (links = 23, emojis = 2), doble fuente, repetidos, tono y horarios los chequea código, no el modelo.
- **Datos fuera del código:** medios y reglas en `config/`; tono y criterios en `references/`.

## Pruebas
```
python3 -m unittest discover -s tests -t .
```
Los tests usan datos de muestra (sin red) y una carpeta temporal: nunca tocan datos reales.

## Pendiente / ideas
- USA Today y Sports Illustrated no tienen feed accesible hoy: se cubren con búsqueda web por dominio. Si aparece un feed estable, se suma en `config/fuentes.json`.
- Imágenes propias, métricas de qué tweets rindieron, programación por API de X (plan pago).
