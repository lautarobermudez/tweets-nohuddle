# Formato de `tweets.json`

```json
{
  "fecha": "2026-11-10",
  "agenda": [{"hora": "22:15", "que": "Bills vs. Vikings, Monday Night Football"}],
  "items": [
    {"id": "t1", "tipo": "tweet", "categoria": "lesion", "liga": "NFL", "hora": "09:00", "prioridad": "esencial",
     "textos": ["Según ESPN, Josh Jacobs se opera de una fractura en un dedo y no hay fecha de regreso."],
     "fuentes": [{"medio": "ESPN", "url": "https://www.espn.com/nfl/story/_/id/1"}],
     "imagen": {"sugerencia": "Foto de Jacobs", "credito": "biblioteca de No Huddle"}},
    {"id": "h1", "tipo": "hilo", "categoria": "analisis", "liga": "College", "hora": "13:00", "prioridad": "opcional",
     "textos": ["Post 1 (funciona solo)", "Post 2", "Post 3"],
     "fuentes": [{"medio": "CBS Sports", "url": "https://..."}]}
  ]
}
```

| Campo | Valores |
|---|---|
| `fecha` | AAAA-MM-DD (el día en que se publica) |
| `tipo` | `tweet` (1 texto) o `hilo` (2 a 6 textos) |
| `categoria` | `resultado`, `lesion`, `transaccion`, `college`, `dato`, `previa`, `analisis`, `pregunta` |
| `liga` | `NFL` o `College` |
| `hora` | `HH:MM` en hora de Argentina |
| `prioridad` | `esencial` u `opcional` |
| `fuentes` | al menos una: `{medio, url}` con la url del digest |
| `imagen` | opcional |

No hace falta `atribucion` ni `verificacion` (son del modo estricto o con verificación).

**Errores que bloquean el Word:** más de 280 caracteres (los links cuentan 23), `[corchetes]` sin completar, texto repetido de los últimos 7 días, campos faltantes o inválidos.
**Avisos:** el texto no nombra a su fuente, tono (mayúsculas, exclamaciones, clickbait), hashtags o emojis de más, decimales con punto, parecido con un titular, horarios pegados o fuera de 08:00-23:30, cantidad fuera de lo esperado.
