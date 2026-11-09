# tweets-nohuddle

Skill de Claude Code que arma cada mañana la planilla (Word) de tweets e hilos del día para la cuenta de X de No Huddle (@nflnohuddle): NFL y college football, a partir de medios prestigiosos e insiders de la NFL, en una sola pasada y con pocos tokens, y nada publicado sin una persona.

- **Para quien la usa:** [INSTALAR.md](INSTALAR.md).
- **Diseño y decisiones de delegación:** [PLAN_DELEGACION.md](PLAN_DELEGACION.md).

## Cómo funciona
El `SKILL.md` es mínimo (35 líneas). **Casi todo lo hace código**; el modelo solo redacta, que es lo único que requiere criterio.

```
tweets.py preparar   (script)
   ├─ chequea Python, configuración y carpeta de trabajo
   ├─ lee los feeds de los medios + la API de ESPN, filtra ruido, agrupa por historia
   ├─ arma digest.md (~1.500 tokens; cada historia con un ID corto N1, C3... y SIN URLs) y digest_ids.json
   ├─ arma el PLAN DEL DÍA: mezcla de publicaciones y horarios (la previa se ajusta al partido del día,
   │   se saltea lo que ya pasó, separación mínima entre publicaciones)
   └─ imprime todo lo que el agente necesita: formato, plan, digest y guía de estilo

Agente (modelo)      escribe redaccion.txt: una línea por publicación   `id | historias | texto`   ← lo ÚNICO que no es código

tweets.py cerrar     (script)
   ├─ resuelve los IDs a medio y URL (referencia interna), arma tweets.json
   ├─ descarta los slots vacíos
   ├─ valida: 280 caracteres, NO citar fuentes en el texto, repetidos, tono, horarios, formato, IDs
   ├─ arma el Word y actualiza el historial
   └─ imprime el resumen final (hora | tipo | categoría | fuente interna) y los avisos
```
**Criterio editorial:** la curaduría la hacen los medios prestigiosos y los insiders de la NFL; no se re-verifica. Somos un medio, así que los tweets **no citan a nadie** ("según…", insiders): la validación lo bloquea. La fuente queda solo en el Word como referencia interna para quien publica; los rumores se redactan en condicional.

**Costo medido por corrida (~4.500 tokens):** ~555 de `SKILL.md`, ~2.560 de la salida de `preparar`, ~250 de la salida de `cerrar` y ~500 que escribe el modelo. La v1 con subagentes y verificador gastaba ~280.000.

**Modelo de skills de Claude Code que sigue (verificado contra la documentación oficial):**
- `disable-model-invocation: true`: se invoca a mano, así que **su descripción no ocupa contexto en ninguna conversación**.
- `model: sonnet` y `effort: medium`: el modelo que redacta es más barato que el de la sesión; la decisión difícil ya la tomó el código.
- `allowed-tools` con `${CLAUDE_SKILL_DIR}`: los scripts corren sin pedir permiso.
- Divulgación progresiva: `SKILL.md` corto; la guía de estilo y las instrucciones las imprime el script en el momento justo; los modos caros están en `references/opcional/`; los scripts **se ejecutan, no se cargan** en contexto.
- Solo funciona en **Claude Code** (los campos `model`, `effort` y `disable-model-invocation` no los acepta claude.ai ni la API de Skills).

**Modos opcionales** (solo a pedido, `references/opcional/`): *con verificación* (subagente independiente, ~70.000 tokens por ronda) y *profundo* (buscadores que abren las notas). Reglas estrictas en `config/reglas.json`.

## Estructura
```
skills/tweets-nohuddle/
  SKILL.md                 mínimo: 2 comandos y 3 reglas (35 líneas)
  config/fuentes.json      medios, feeds, insiders (editable)
  config/reglas.json       límites, reglas de validación y PLAN DIARIO (mezcla y horarios) (editable)
  references/              guía de estilo (la imprime `preparar`) y formato; opcional/ = prompts de verificador y buscadores
  scripts/tweets.py        CLI: preparar | cerrar (flujo normal); doctor | hoy | fuentes | validar | word | historial | fusionar (sueltos)
  scripts/nh/              un módulo por responsabilidad (solo stdlib, Python 3.8+):
                             flujo.py      orquesta preparar y cerrar
                             fuentes.py    lee y agrupa los medios         rss.py       descarga y parsea feeds
                             digest.py     resumen con IDs para el agente  plan.py      mezcla y horarios del día
                             redaccion.py  formato compacto -> tweets.json  validar.py   reglas de validación
                             wordgen.py    el Word                          historial.py memoria entre días
                             tiempo.py     hora de Argentina                texto.py     utilidades de texto
                             rutas.py      configuración y carpetas         verificacion.py modo opcional
tests/                     91 tests (unittest)
instalar.py                instalador (Windows/Mac/Linux)
```

## Decisiones de ingeniería
- **Sin dependencias:** solo la biblioteca estándar. El Word se arma a mano (un .docx es un zip de XML) para no pedirle instalar nada a quien la usa.
- **Tolerante a fallos:** un feed caído no frena la corrida; queda anotado en el digest.
- **Contrato explícito:** `references/formato_tweets.md` define el JSON entre el agente y los scripts; si no cumple, el validador lo dice con un mensaje claro.
- **Skill delgada, scripts gruesos:** la lógica determinista (fuentes, plan, validación, Word, historial) vive en código con tests; el `SKILL.md` solo dice qué dos comandos correr. Las instrucciones que necesita el agente las imprime el script en el momento justo (en vez de cargarlas todas de antemano).
- **Costo controlado:** el script resume los datos (digest de ~2.200 tokens en vez de 156 KB) y el agente no abre notas ni lanza subagentes salvo que se le pida.
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
