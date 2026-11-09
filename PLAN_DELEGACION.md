# Plan de delegación: `/tweets-nohuddle` (2026-11-09, v2 liviana)

> **Cambio v2 (09/11 noche):** Lautaro pidió bajar el costo en tokens. Se confía en la curaduría de los medios prestigiosos y los insiders de la NFL: no se re-verifica ni se exige doble fuente. La v1 (2 buscadores + verificador, ~280.000 tokens por corrida) quedó como modo opcional.

**Objetivo:** cada mañana, una planilla (Word) con los tweets e hilos del día para la cuenta de X de No Huddle (@nflnohuddle) sobre NFL y college football, lista para que la persona de redes la revise y la programe.

**Problema:** uso diario (frecuencia alta, variación alta). Lo usa el compañero de redes, no solo quien la construyó. Un dato mal dicho (resultado, lesión, rumor presentado como hecho) daña la credibilidad de la cuenta. **Nunca se delega:** publicar.

**Plataforma:** Claude Code (app de escritorio del compañero). Puede leer la web, correr scripts locales y lanzar subagentes. Límites: algunos medios bloquean la lectura automática (USA Today responde 402), los feeds traen titular y resumen (no la nota completa), y las fotos de deportes tienen derechos.

| Tarea | Modo | Por qué | Control |
|---|---|---|---|
| Juntar titulares de los medios, agruparlos y resumirlos (digest) | Automatización (`tweets.py fuentes`) | Repetitivo y barato: cero tokens | Reporta fuentes caídas; tolera fallos; tests |
| Elegir las historias y redactar con el tono de la cuenta | Aumentación (1 sola pasada, leyendo solo el digest) | Es criterio y estilo | Guía de estilo corta + el compañero edita |
| Atribuir cada dato a su medio o insider | Regla de redacción + aviso del validador | La responsabilidad queda en la fuente prestigiosa | Aviso si el texto no nombra su fuente |
| Validar y armar el Word | Automatización (`word`) | Determinista | 280 caracteres, repetidos, tono, horarios |
| Verificación independiente de datos | **Opcional**, solo a pedido | Costosa y redundante con la curaduría de los medios | Modo "con verificación" |
| Revisar, ajustar y publicar | **Humano** | Publica con la voz de la cuenta | Solo el compañero |

**Descripción:** las reglas viven en `references/` y `config/` (editables sin tocar código).
**Discernimiento:** la corrida salió bien si el compañero publica la mayoría sin reescribir y ningún tweet afirma algo que el medio citado no dijo. Se revisa con una muestra semanal; si aparecen errores, se enciende el modo con verificación.
**Diligencia:** responde quien publica. Cada ítem guarda su fuente y la nombra en el texto; el historial evita repetir 7 días.
**Hoy / después:** hoy, flujo completo con Word. Después: imágenes, métricas de qué rindió, programación por API (requiere plan pago de X), y sumar medios con feed propio.
