# Cómo elegir qué tuitear

## Qué es "importante" (puntuá cada historia del 0 al 3 en cada criterio)
| Criterio | 3 puntos | 0 puntos |
|---|---|---|
| **Impacto deportivo** | Cambia la carrera por playoffs/división, lesión o movimiento de un quarterback o figura, trade grande, récord, sanción | Rutina sin consecuencia |
| **Interés de la audiencia** | Equipos y figuras que más lee el público de No Huddle (Dallas Cowboys, Pittsburgh Steelers, San Francisco 49ers, Kansas City Chiefs, Green Bay Packers, y las estrellas de la liga) | Equipo o jugador marginal sin gancho |
| **Novedad** | Salió en las últimas 12 h | Más de 36 h |
| **Solidez** | La cubren 2+ medios de peso (o lo confirma el equipo/liga) | Un solo medio sin respaldo |
| **Aporte propio** | Se le puede sumar contexto o una lectura de No Huddle | Es solo repetir el titular |

Tomá las de mayor puntaje. **Una historia con Solidez 0 no entra** salvo como "reportado" con atribución explícita (insider conocido).

## Reglas de fuentes
- `candidatos.json` trae titulares ya agrupados por historia (`historias`) con `n_medios`. Es una ayuda: **confirmá siempre abriendo la nota** (WebFetch) antes de escribir.
- Hecho "confirmado" = al menos **2 medios distintos** (ESPN, CBS Sports, Sports Illustrated, USA Today, NFL.com, Fox Sports, The Athletic, AP, Yahoo, Pro Football Talk). Dos notas del mismo medio cuentan como una.
- Un solo medio o un insider (Schefter, Rapoport, Pelissero, Garafolo, Fowler, Russini, Thamel, Dellenger) = "reportado" y el tweet lo atribuye por su nombre.
- Los medios sin feed (Sports Illustrated, USA Today, NFL.com, Fox Sports, The Athletic, AP) se buscan con búsqueda web limitada a su dominio (`medios_por_busqueda` en el JSON).
- Ignorá: apuestas, promos, fantasy, predicciones, mock drafts de baja señal.
- Cuidado con las **fechas**: los medios reciclan notas viejas. Si la nota no es de las últimas 36 h, descartala.

## Composición del día (6 a 10 tweets + 1 o 2 hilos)
- **Mañana (08:00-10:30):** 1 resumen de lo más importante de ayer; 1 lesión/estado.
- **Mediodía (12:00-14:30):** 1 transacción o noticia fuerte; 1 college (en temporada).
- **Tarde (16:00-18:30):** 1 dato/stat con contexto; 1 pregunta o análisis corto.
- **Noche (19:00-23:00):** 1 previa del partido del día (hora de Argentina); el hilo principal.
- Deben estar **al menos uno de cada: resultado, lesión/transacción, college, previa**. Los otros formatos, a gusto.
- **Hilos:** 1 de análisis de la historia más grande del día y, si hay partido importante, 1 de previa.
- Separá las publicaciones al menos 20 minutos. Dejá aire alrededor de los kickoffs.

## Estacionalidad (ajustá al calendario real; mirá `partidos` del JSON y el scoreboard)
- **Martes-miércoles:** repaso de la fecha, lesiones, análisis, trade deadline si corresponde.
- **Jueves:** previa del Thursday Night Football.
- **Viernes-sábado:** parte médico (injury report), college del sábado, previa de la fecha.
- **Domingo:** día de partidos: previas por la mañana (hora de Argentina) y resultados/dato por la noche.
- **Lunes:** resultados del domingo y previa del Monday Night Football.
- Fuera de temporada (draft, free agency, training camp), adaptá: transacciones, contratos y draft.
- Si hay partido del día, **convertí el horario a hora de Argentina** (la fecha en `partidos` viene en UTC; Argentina = UTC-3).
