# Plan de delegación: `/tweets-nohuddle` (2026-11-09, v4)

> **Cambio v4 (09/11 noche):** auditoría contra la documentación oficial de skills. La skill se invoca a mano (`disable-model-invocation`), fija `model: sonnet` y `effort: low`, y el modelo escribe un formato compacto (`id | historias | texto`) en vez de un JSON con URLs: los IDs de historia los resuelve el script. Costo medido ~4.500 tokens por corrida.
>
> **Cambio v3 (09/11 noche):** (1) los tweets **no citan fuentes** en el texto (somos un medio); (2) la lógica pasa a scripts: el `SKILL.md` queda en 2 comandos (`preparar`, `cerrar`) y el plan del día (mezcla y horarios) lo decide código.
>
> **Cambio v2 (09/11 noche):** Lautaro pidió bajar el costo en tokens. Se confía en la curaduría de los medios prestigiosos y los insiders de la NFL: no se re-verifica ni se exige doble fuente. La v1 (2 buscadores + verificador, ~280.000 tokens por corrida) quedó como modo opcional.

**Objetivo:** cada mañana, una planilla (Word) con los tweets e hilos del día para la cuenta de X de No Huddle (@nflnohuddle) sobre NFL y college football, lista para que la persona de redes la revise y la programe.

**Problema:** uso diario (frecuencia alta, variación alta). Lo usa el compañero de redes, no solo quien la construyó. Un dato mal dicho (resultado, lesión, rumor presentado como hecho) daña la credibilidad de la cuenta. **Nunca se delega:** publicar.

**Plataforma:** Claude Code (app de escritorio del compañero). Puede leer la web, correr scripts locales y lanzar subagentes. Límites: algunos medios bloquean la lectura automática (USA Today responde 402), los feeds traen titular y resumen (no la nota completa), y las fotos de deportes tienen derechos.

| Tarea | Modo | Por qué | Control |
|---|---|---|---|
| Chequear entorno, juntar medios, agrupar, resumir (digest) | Automatización (`tweets.py preparar`) | Repetitivo: cero tokens | Reporta medios caídos; tolera fallos; tests |
| Decidir la mezcla del día y los horarios | Automatización (plan en `reglas.json`, ajustado al partido) | Determinista y siempre igual | Composición mínima y separación entre publicaciones con tests |
| Redactar cada tweet/hilo con el tono de la cuenta | Aumentación (única parte con el modelo; 1 pasada, ~500 tokens de salida, leyendo solo el digest) | Es criterio y estilo | Guía de estilo corta + el compañero edita |
| No citar fuentes; rumores en condicional | Regla de redacción + **error de validación** | Somos un medio | `según…`, `fuentes…` e insiders bloquean el Word |
| Validar, armar el Word, historial, resumen final | Automatización (`tweets.py cerrar`) | Determinista | 280 caracteres, repetidos, tono, horarios |
| Verificación independiente de datos | **Opcional**, solo a pedido | Costosa y redundante con la curaduría de los medios | Modo "con verificación" |
| Revisar, ajustar y publicar | **Humano** | Publica con la voz de la cuenta | Solo el compañero |

**Descripción:** las reglas viven en `references/` y `config/` (editables sin tocar código).
**Discernimiento:** la corrida salió bien si el compañero publica la mayoría sin reescribir y ningún tweet afirma algo que el medio citado no dijo. Se revisa con una muestra semanal; si aparecen errores, se enciende el modo con verificación.
**Diligencia:** responde quien publica. Cada ítem guarda su fuente como referencia interna (aparece en el Word, no en el tweet) y los rumores van en condicional; el historial evita repetir 7 días. **Riesgo asumido por Lautaro:** al no citar ni verificar, un dato mal resumido o un rumor afirmado sale con la voz del medio; por eso el compañero es la última barrera.
**Hoy / después:** hoy, flujo completo con Word. Después: imágenes, métricas de qué rindió, programación por API (requiere plan pago de X), y sumar medios con feed propio.
