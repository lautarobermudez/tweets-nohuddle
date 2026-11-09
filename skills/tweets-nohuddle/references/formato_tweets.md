# Formato de la redacción

`tweets.py preparar` imprime este formato y el plan del día. El agente escribe `redaccion.txt` (una línea por publicación) y `tweets.py cerrar` arma el resto.

```
# comentarios (se ignoran)
t1 | N1,N4 | Texto del tweet.
t2@12:30 | C2 | Otro tweet (el @hora es opcional: cambia el horario).
h1 | N3 | Primer post de un hilo.
+ Segundo post del hilo.
+ Tercer post del hilo.
t3 | - | Tweet que no sale de una historia del digest (un resultado, una previa).
```

- **`id`**: el slot del plan (t1, h1...). Los que no se usan se omiten y se descartan solos. Un tweet con líneas `+` pasa a ser un hilo.
- **`historias`**: IDs del digest (N = NFL, C = College) de donde sale el dato. El script resuelve medio y URL como **referencia interna** (aparece en el Word, no en el tweet). `-` si no sale de una historia (se usa el marcador de ESPN).
- **Texto**: solo lo que dice el digest. No se cita a nadie. Los rumores, en condicional.

## Qué valida `cerrar`
**Errores (bloquean el Word):** más de 280 caracteres (un link cuenta 23), `[corchetes]` sin completar, citar una fuente en el texto ("según…", "fuentes…", nombre de un insider), texto repetido de los últimos 7 días, línea mal formada, slot o historia inexistente.
**Avisos:** un medio nombrado junto a un verbo de atribución, tono (mayúsculas, exclamaciones, clickbait), hashtags o emojis de más, decimales con punto, parecido con un titular, horarios pegados, cantidad fuera de lo esperado.

## Modo manual (avanzado)
Si no hay `redaccion.txt`, `cerrar` acepta un `tweets.json` ya completo (`tweets.py cerrar ruta/tweets.json`).
