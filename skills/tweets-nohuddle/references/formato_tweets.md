# Formato de `tweets.json`

`tweets.py preparar` lo genera con un **slot por publicación** (id, tipo, liga, categoría, hora y prioridad ya definidos). Solo hay que completar `textos` y `fuentes`.

```json
{"id": "t1", "tipo": "tweet", "categoria": "lesion", "liga": "NFL", "hora": "09:45", "prioridad": "esencial",
 "textos": ["Josh Jacobs se opera de una fractura en un dedo y no hay fecha de regreso."],
 "fuentes": [{"medio": "ESPN", "url": "https://www.espn.com/nfl/story/_/id/1"}],
 "imagen": {"sugerencia": "Foto de Jacobs", "credito": "biblioteca de No Huddle"}}
```

| Campo | Qué poner |
|---|---|
| `textos` | tweet: 1 texto. Hilo: 2 a 6 textos (el primero funciona solo) |
| `fuentes` | `[{medio, url}]` tomados del resumen; referencia interna, NO se cita en el texto |
| `imagen` | opcional: `sugerencia` y `credito` |
| `categoria`, `liga`, `hora` | se pueden cambiar. Categorías: `resultado`, `lesion`, `transaccion`, `college`, `dato`, `previa`, `analisis`, `pregunta`. Ligas: `NFL`, `College`. Hora: `HH:MM` de Argentina |
| `agenda` (opcional, arriba del archivo) | `[{"hora":"22:15","que":"Bills vs. Vikings"}]` |

Los slots que queden con `textos` vacío se descartan solos.

**Errores que bloquean el Word:** más de 280 caracteres (un link cuenta 23), `[corchetes]` sin completar, citar una fuente en el texto ("según…", "fuentes…", nombre de un insider), texto repetido de los últimos 7 días, campos faltantes.
**Avisos:** un medio nombrado junto a un verbo de atribución, tono (mayúsculas, exclamaciones, clickbait), hashtags o emojis de más, decimales con punto, parecido con un titular, horarios pegados, cantidad fuera de lo esperado.
