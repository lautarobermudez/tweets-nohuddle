---
name: tweets-nohuddle
description: Arma cada mañana la planilla de tweets e hilos del día para la cuenta de X de No Huddle (@nflnohuddle) sobre NFL y college football, a partir de los medios prestigiosos y los insiders de la NFL (ESPN, CBS Sports, Pro Football Talk, Yahoo, SI, USA Today, Schefter, Rapoport...). Modo liviano: pocos tokens, una sola pasada, sin subagentes. Deja un Word listo para copiar y programar. Usar cuando pidan "los tweets del día", "armá los tweets de No Huddle", "contenido para X de No Huddle", "la planilla de la mañana" o /tweets-nohuddle. NO publica nada.
user-invocable: true
---

# /tweets-nohuddle — Tweets del día para @nflnohuddle (modo liviano)

**Resultado:** un Word `Tweets No Huddle - DD-MM-AAAA.docx` con 6 a 10 tweets y 1 o 2 hilos, con hora sugerida (hora de Argentina), fuente e imagen sugerida. La persona de redes lo revisa y lo programa a mano.

**Idea:** la curaduría ya la hacen ESPN, CBS, Pro Football Talk, los insiders y demás. Acá no se re-verifica: se **resume lo que ellos publicaron y se les atribuye**. Eso cuesta pocos tokens.

## Reglas
1. **Nunca publicar ni programar.** Publica una persona.
2. **Solo lo que dice el digest** (titular y resumen de los medios) o una nota que abriste. No agregues datos, cifras ni citas de tu cosecha.
3. **Nombrá la fuente en el texto** ("según ESPN", "Adam Schefter reporta", "CBS Sports informa"). La responsabilidad es del medio.
4. Si algo falla, seguí con lo que haya y avisá claro.

## Dónde está todo
`SKILL_DIR` = la carpeta que muestra "Base directory" al cargar la skill. Los scripts se corren con Python (`python3`; si no existe, `python`; en Windows, `py -3`): abajo escribo `PY`. No hay que instalar nada. Los archivos del día van a `NoHuddle-Tweets/salida/AAAA-MM-DD/` en la carpeta del usuario.

## Procedimiento (4 pasos)

### 1. Preparar y juntar las fuentes
```
PY SKILL_DIR/scripts/tweets.py doctor
PY SKILL_DIR/scripts/tweets.py hoy
PY SKILL_DIR/scripts/tweets.py fuentes
```
Si `doctor` marca `FALLA`, explicalo en palabras simples y frená. `hoy` da la fecha en Argentina (`FECHA`). `fuentes` lee los medios y escribe **`digest.md`**: un resumen de ~2.000 tokens con las historias más importantes (ordenadas por cuántos medios las cubren), los partidos en hora de Argentina y qué medios no respondieron.
**Leé solo `digest.md`. No abras `candidatos.json`** (es enorme, solo para consultar un dato puntual).

### 2. Redactar
Leé `references/estilo_tweets.md` (una página). Con el digest armá **6 a 10 tweets y 1 o 2 hilos**:
- Mezcla: al menos un resultado, una lesión o transacción, un college y una previa; el resto, a gusto. Más medios cubriendo = más importante.
- Horarios en hora de Argentina entre 08:00 y 23:30, separados al menos 20 min, cerca de los partidos del día.
- Solo si el resumen no alcanza para un dato clave, abrí **como máximo 3 notas** con WebFetch. Por defecto, ninguna.

### 3. Guardar
Escribí `salida/FECHA/tweets.json` con el formato mínimo de `references/formato_tweets.md` (cada ítem lleva su fuente: medio + url del digest).

### 4. Armar el Word
```
PY SKILL_DIR/scripts/tweets.py word salida/FECHA/tweets.json
```
Chequea 280 caracteres, repetidos de los últimos 7 días, tono, horarios y que el texto nombre su fuente. Si hay **errores**, corregilos y repetí. Los **avisos** salen en el Word. Si todo sale bien, registra los textos en el historial y deja el `.docx`.

## Entregar (corto)
Mostrá la ruta del Word, una tabla hora · tipo · tema · fuente, y los avisos que valga la pena mirar. Recordá que **nada se publicó**.

## Si algo sale mal
| Pasa esto | Hacé esto |
|---|---|
| No hay Python | Frená; hay que instalarlo (python.org) |
| Un medio no respondió | Seguí; el digest lo avisa |
| Ningún medio respondió | Avisá y pedí reintentar más tarde |
| `repetido` | Cambiá el enfoque o descartalo |
| Corrés dos veces el mismo día | Sin problema: el historial reemplaza la corrida del día |

## Modos opcionales (solo si te los piden)
- **"Con verificación":** un subagente independiente chequea los datos contra las fuentes. Instrucciones en `references/opcional/prompt_verificador.md`; el veredicto se une con `PY SKILL_DIR/scripts/tweets.py fusionar tweets.json verificacion.json`. Cuesta ~70.000 tokens por ronda.
- **"Modo profundo":** dos subagentes buscadores (NFL y College) que abren las notas y buscan otros medios: `references/opcional/prompt_buscador.md`. Cuesta ~80.000 tokens cada uno.
- **Modo estricto de reglas:** en `config/reglas.json`, `exigir_doble_fuente` y `verificacion_obligatoria` en `true`.

## Mantenimiento
Medios e insiders: `config/fuentes.json`. Límites y reglas: `config/reglas.json`. Tests: `python3 -m unittest discover -s tests -t .` desde la raíz del proyecto.
