# Plan de delegación: `/tweets-nohuddle` (2026-11-09)

**Objetivo:** cada mañana, una planilla (Word) con los tweets e hilos del día para la cuenta de X de No Huddle (@nflnohuddle) sobre NFL y college football, lista para que la persona de redes la revise y la programe.

**Problema:** uso diario (frecuencia alta, variación alta). Lo usa el compañero de redes, no solo quien la construyó. Un dato mal dicho (resultado, lesión, rumor presentado como hecho) daña la credibilidad de la cuenta. **Nunca se delega:** publicar.

**Plataforma:** Claude Code (app de escritorio del compañero). Puede leer la web, correr scripts locales y lanzar subagentes. Límites: el verificador no encuentra todo, algunos medios bloquean lectura automática (USA Today responde 402), y las fotos de deportes tienen derechos.

| Tarea | Modo | Por qué | Control |
|---|---|---|---|
| Juntar titulares de los medios y agruparlos por historia | Automatización (`tweets.py fuentes`) | Repetitivo y verificable | Reporta fuentes caídas; tolera fallos; 54 tests |
| Elegir y confirmar las historias de cada liga | Agencia acotada: 2 subagentes buscadores en paralelo | Abierto y variable | Regla de 2 medios; cada dato con URL leída |
| Redactar los tweets con el tono de la cuenta | Aumentación | Es criterio y estilo | Guía de estilo + el compañero edita |
| Verificar cifras, fechas, citas y atribución | Agencia con control: subagente independiente | Quien escribe no verifica | Veredicto OK/REVISAR/ERROR por ítem, fusionado por script |
| Validar y armar el Word | Automatización (`validar`, `word`) | Determinista | 280 caracteres, doble fuente, repetidos, tono; bloquea con errores |
| Revisar, ajustar y publicar | **Humano** | Publica con la voz de la cuenta | Solo el compañero |

**Descripción:** las reglas viven en `references/` y `config/` (editables sin tocar código).
**Discernimiento:** la corrida salió bien si el compañero publica la mayoría sin reescribir y el verificador no deja pasar un dato incorrecto. Se revisa con una muestra semanal.
**Diligencia:** responde quien publica. Cada ítem guarda sus fuentes; el historial evita repetir 7 días.
**Hoy / después:** hoy, flujo completo con Word. Después: imágenes, métricas de qué rindió, programación por API (requiere plan pago de X), y sumar medios con feed propio.
