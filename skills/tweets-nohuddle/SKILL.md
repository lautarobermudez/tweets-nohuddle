---
name: tweets-nohuddle
description: Arma cada mañana la planilla de tweets e hilos del día para la cuenta de X de No Huddle (@nflnohuddle) sobre NFL y college football. Busca las noticias más importantes en varios medios respetables (ESPN, CBS Sports, Sports Illustrated, USA Today, Pro Football Talk, NFL.com, Fox Sports, The Athletic, AP), confirma cada dato con 2 medios, redacta con el tono de la cuenta, verifica con un subagente independiente y entrega un Word listo para copiar y programar. Usar cuando pidan "los tweets del día", "armá los tweets de No Huddle", "contenido para X de No Huddle", "la planilla de la mañana" o /tweets-nohuddle. NO publica nada.
user-invocable: true
---

# /tweets-nohuddle — Tweets del día para @nflnohuddle

**Resultado:** un Word `Tweets No Huddle - DD-MM-AAAA.docx` con 6 a 10 tweets y 1 o 2 hilos, cada uno con hora sugerida (hora de Argentina), fuentes, estado de verificación e imagen sugerida. La persona de redes lo revisa y lo programa a mano.

## Reglas que no se negocian
1. **Nunca publicar ni programar nada.** Ni tenés acceso a la cuenta ni se te pide. Publica una persona.
2. **Nada inventado.** Todo dato, cita y URL sale de una nota que leíste de verdad. Si no lo podés confirmar, no entra.
3. **Un hecho sin atribución necesita 2 medios distintos.** Con uno solo (o un insider) va "reportado" y el texto nombra a quien lo reporta.
4. **Quien verifica no es quien escribe:** la verificación la hace un subagente aparte.
5. **Es mejor entregar menos tweets que rellenar con algo dudoso.** Decilo si pasó.
6. Si algo falla (sin internet, un medio caído), **seguí con lo que haya y avisá claro**; no te trabes ni escondas el problema.

## Dónde está todo
- Esta carpeta (la que muestra "Base directory" al cargar la skill) tiene `scripts/`, `config/` y `references/`. Llamala `SKILL_DIR`.
- Los scripts se corren con Python: probá `python3`, si no existe `python`, y en Windows `py -3`. Abajo escribo `PY`. Son solo biblioteca estándar: no hay que instalar nada.
- Los archivos del día quedan en la carpeta de trabajo (por defecto `NoHuddle-Tweets` dentro de la carpeta del usuario): `salida/AAAA-MM-DD/`. El comando `doctor` te dice cuál es.

## Procedimiento

### 0. Preparación (siempre, es rápido)
```
PY SKILL_DIR/scripts/tweets.py doctor --red
```
Si algo dice `FALLA`, explicáselo al usuario en palabras simples y frená (ej. "no hay Python" o "no hay internet"). Después `PY SKILL_DIR/scripts/tweets.py hoy` imprime la **fecha de hoy en Argentina** (AAAA-MM-DD). Llamala `FECHA`.

### 1. Juntar las fuentes (script)
```
PY SKILL_DIR/scripts/tweets.py fuentes --horas 36
```
Lee los feeds de los medios y la API de ESPN, descarta apuestas/promos/viejos y **agrupa los titulares por historia contando cuántos medios la cubren**. Guarda `salida/FECHA/candidatos.json`. Mirá el resumen: si hay feeds caídos, está bien (el paso 2 los cubre con búsqueda web). Si **ninguna** fuente respondió, avisale al usuario y seguí solo con búsqueda web.

### 2. Buscar y confirmar las historias (2 subagentes EN PARALELO)
Lanzá **dos subagentes en el mismo mensaje** (herramienta Agent): uno para `NFL` y otro para `College`. A cada uno pasale el contenido de `references/prompt_buscador.md` con `{LIGA}`, `{FECHA}`, `{CANDIDATOS}` (ruta completa de `candidatos.json`) y `{SALIDA}` (`salida/FECHA/historias_nfl.json` o `historias_college.json`).
Si no tenés la herramienta de subagentes, hacé los dos pasos vos, uno después del otro, con el mismo prompt.
Cuando terminen, leé los dos JSON. Si en una liga no hay historias (fuera de temporada, por ejemplo), seguí con la otra.

### 3. Elegir y redactar (lo hacés vos)
Leé **completas** estas tres guías antes de escribir: `references/estilo_tweets.md`, `references/criterios_seleccion.md` y `references/formato_tweets.md`.
- Armá la composición del día según `criterios_seleccion.md` (6 a 10 tweets + 1 o 2 hilos; al menos un resultado, una lesión/transacción, un college y una previa).
- Escribí `salida/FECHA/tweets.json` con el formato de `formato_tweets.md`. Cada ítem con sus fuentes reales y `atribucion` correcta.
- Los horarios, en hora de Argentina, repartidos y cerca de los partidos del día (usá `partidos_del_dia`).
- Revisá vos mismo contra la guía de estilo antes de seguir: voseo, sin emojis ni clickbait, números con coma, no copiar titulares.

### 4. Verificar (subagente independiente)
Lanzá un subagente nuevo con `references/prompt_verificador.md` (`{TWEETS}` = ruta de `tweets.json`, `{SALIDA}` = `salida/FECHA/verificacion.json`). Cuando termine:
```
PY SKILL_DIR/scripts/tweets.py fusionar salida/FECHA/tweets.json salida/FECHA/verificacion.json
```
Eso escribe el veredicto (OK / REVISAR / ERROR) en cada ítem. **Corregí una sola vez** lo que quedó en REVISAR o ERROR usando el detalle del verificador: arreglá el texto o descartá el ítem. Si corregiste algo, repetí este paso 4 completo. Lo que siga en ERROR, se descarta.

### 5. Validar y armar el Word (script)
```
PY SKILL_DIR/scripts/tweets.py word salida/FECHA/tweets.json --titulares salida/FECHA/candidatos.json
```
Valida 280 caracteres, doble fuente, atribución, repetidos de los últimos 7 días, tono y horarios. Si hay **errores**, corregilos y repetí (no se arma el Word con errores). Los **avisos** salen en el Word. Si todo sale bien, registra los textos en el historial y deja el `.docx`.

### 6. Entregar (corto)
Mostrale al usuario:
- La ruta del Word.
- Una tabla: hora · tipo · tema · verificación.
- **Qué tiene que mirar él:** ítems en REVISAR, datos "reportados", fotos con crédito a chequear.
- Cualquier problema (medios caídos, menos tweets de los esperados) y recordá: **nada se publicó**.

## Si algo sale mal
| Pasa esto | Hacé esto |
|---|---|
| `doctor` dice que no hay Python | Frená y explicá que hay que instalarlo (python.org) o pedir ayuda a quien instaló la skill |
| Un feed falla (HTTP 404, timeout) | Seguí; el buscador lo cubre con búsqueda web. Está anotado en `fuentes_error` |
| Ningún feed responde | Avisá, y que los buscadores usen solo `WebSearch`/`WebFetch` |
| `validar` marca `repetido` | Cambiá el enfoque del tweet o descartalo: ya se propuso en los últimos días |
| El verificador deja muchos REVISAR | No rellenes: entregá menos ítems y decilo |
| Se corre dos veces el mismo día | Sin problema: el historial reemplaza la corrida del día, no la duplica |

## Mantenimiento (para quien cuida la skill)
- Medios y feeds: `config/fuentes.json` (activar/apagar sin tocar código).
- Límites y reglas de validación: `config/reglas.json`.
- Tono y formatos: `references/estilo_tweets.md`. Criterios de qué elegir: `references/criterios_seleccion.md`.
- Pruebas: `python3 -m unittest discover -s tests -t .` desde la raíz del proyecto.
