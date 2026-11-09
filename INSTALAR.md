# Cómo instalar y usar `/tweets-nohuddle` (guía para quien maneja las redes)

Es una vez y lleva 5 minutos. Después, cada mañana es un solo comando.

## Qué necesitás
1. **Claude Code** en la app de Claude (pestaña **Code**), con la sesión iniciada.
2. **Python 3.8 o más nuevo.** Para saber si lo tenés, abrí una terminal (en Windows: PowerShell) y escribí `python --version`. Si dice "Python 3.algo", está listo. Si no, instalalo desde python.org (tildá "Add Python to PATH").
3. La carpeta `tweets-nohuddle` que te pasaron (descomprimila donde quieras).

## Instalar (una sola vez)
1. Abrí una terminal **dentro de la carpeta `tweets-nohuddle`**.
2. Escribí:
   ```
   python instalar.py
   ```
3. Tiene que terminar con **"Listo. Abrí Claude Code y escribí: /tweets-nohuddle"**. Si dice `FALLA` en algún renglón, copiale ese renglón a quien te lo pasó.

## Usar (todos los días)
1. Abrí Claude Code.
2. Escribí `/tweets-nohuddle` y Enter. Tarda un par de minutos: lee los medios, elige lo más importante y redacta (usa pocos tokens).
3. Al final te dice dónde quedó el **Word**: carpeta `NoHuddle-Tweets/salida/AAAA-MM-DD/` dentro de tu carpeta de usuario.
4. Abrí el Word, revisá cada recuadro y copialo a X. **Nada se publica solo.**

## Cómo leer el Word
- Cada publicación tiene **hora sugerida (hora de Argentina)**, tipo (tweet o hilo), la liga y la categoría.
- Cada tweet **nombra su fuente** ("según ESPN", "Schefter reporta") y trae el link de la nota. Los medios y los insiders son los que respaldan el dato: no se vuelve a verificar.
- Arriba, "Para revisar antes de publicar" junta los avisos del día (por ejemplo, un texto que no nombra su fuente).
- **Imagen sugerida:** usá primero las fotos de la biblioteca de No Huddle; si usás otra, poné el crédito y chequeá los derechos.
- Si alguna vez querés que se **verifiquen los datos a fondo**, pedilo así: `/tweets-nohuddle con verificación` (gasta bastantes más tokens).

## Si algo no anda
| Síntoma | Qué hacer |
|---|---|
| `/tweets-nohuddle` no aparece | Cerrá y abrí Claude Code; si sigue, corré de nuevo `python instalar.py --actualizar` |
| "No hay Python" | Instalá Python (python.org) y repetí la instalación |
| Salieron pocos tweets | Puede pasar si ese día hubo poca novedad en los medios; prefiere pocos antes que rellenar |
| Un medio no se pudo leer | Es normal (a veces bloquean); la skill sigue con los demás y te avisa cuál faltó |
| Querés actualizar la skill | Reemplazá la carpeta por la nueva y corré `python instalar.py --actualizar` |
