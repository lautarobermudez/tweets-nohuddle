# Formato de `tweets.json` (el contrato entre el agente y los scripts)

El agente escribe este archivo; `scripts/tweets.py validar` y `word` lo leen. Si el formato falla, los scripts lo dicen con un mensaje claro.

```json
{
  "fecha": "2026-11-10",
  "zona_horaria": "America/Argentina/Buenos_Aires",
  "agenda": [{"hora": "22:15", "que": "Bills vs. Vikings, Monday Night Football"}],
  "items": [
    {
      "id": "t1",
      "tipo": "tweet",
      "categoria": "lesion",
      "liga": "NFL",
      "hora": "09:00",
      "prioridad": "esencial",
      "textos": ["Texto del tweet, listo para pegar."],
      "fuentes": [
        {"medio": "ESPN", "url": "https://..."},
        {"medio": "Pro Football Talk", "url": "https://..."}
      ],
      "atribucion": "confirmado",
      "link_nota_nh": "",
      "imagen": {"sugerencia": "Foto de Josh Jacobs en acción", "credito": "AP"}
    },
    {
      "id": "h1",
      "tipo": "hilo",
      "categoria": "previa",
      "liga": "NFL",
      "hora": "19:00",
      "prioridad": "esencial",
      "textos": ["Post 1 (funciona solo)", "Post 2", "Post 3"],
      "fuentes": [{"medio": "ESPN", "url": "https://..."}, {"medio": "CBS Sports", "url": "https://..."}],
      "atribucion": "confirmado"
    }
  ]
}
```

## Campos
| Campo | Valores |
|---|---|
| `fecha` | `AAAA-MM-DD` (hoy, hora de Argentina) |
| `tipo` | `tweet` (exactamente 1 texto) o `hilo` (2 a 6 textos) |
| `categoria` | `resultado`, `lesion`, `transaccion`, `college`, `dato`, `previa`, `analisis`, `pregunta` |
| `liga` | `NFL` o `College` |
| `hora` | `HH:MM`, hora de Argentina, entre 08:00 y 23:30 |
| `prioridad` | `esencial` u `opcional` |
| `atribucion` | `confirmado` (2+ medios distintos en `fuentes`) o `reportado` (1 medio o insider; el texto lo nombra: "Según...", "reporta...") |
| `fuentes` | lista de `{medio, url}`; la url de la nota real que leíste, nunca inventada |
| `imagen` | opcional: `sugerencia` y `credito` |
| `verificacion` | **no lo escribe el redactor**: lo agrega `tweets.py fusionar` con lo que dijo el verificador |

## Lo que valida el script (y por qué)
Errores (bloquean el Word): más de 280 caracteres (los links cuentan 23), `[corchetes]` sin completar, `confirmado` con menos de 2 medios, `reportado` sin atribución en el texto, texto repetido de los últimos 7 días, verificación en ERROR, campos faltantes.
Avisos (se muestran en el Word): hashtags/emojis de más, tono (mayúsculas, exclamaciones, clickbait), decimales con punto, parecido con un titular, horarios pegados o fuera de ventana, cantidad fuera de lo esperado, sin verificar.
