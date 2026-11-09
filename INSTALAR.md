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
2. Escribí `/tweets-nohuddle` y Enter. Tarda unos minutos: busca las noticias en varios medios, las confirma, redacta y verifica.
3. Al final te dice dónde quedó el **Word**: carpeta `NoHuddle-Tweets/salida/AAAA-MM-DD/` dentro de tu carpeta de usuario.
4. Abrí el Word, revisá cada recuadro y copialo a X. **Nada se publica solo.**

## Cómo leer el Word
- Cada publicación tiene **hora sugerida (hora de Argentina)**, tipo (tweet o hilo), la liga y la categoría.
- **Verificación:** `OK` (confirmado), `REVISAR` (mirá la nota que dice qué dudar) o `ERROR` (no debería llegar acá).
- Arriba, "Para revisar antes de publicar" junta los avisos del día.
- Los datos **"reportado"** vienen de un solo medio o insider: el tweet ya lo dice ("Según Schefter…"). No les saques la atribución.
- **Imagen sugerida:** usá primero las fotos de la biblioteca de No Huddle; si usás otra, poné el crédito y chequeá los derechos.

## Si algo no anda
| Síntoma | Qué hacer |
|---|---|
| `/tweets-nohuddle` no aparece | Cerrá y abrí Claude Code; si sigue, corré de nuevo `python instalar.py --actualizar` |
| "No hay Python" | Instalá Python (python.org) y repetí la instalación |
| Salieron pocos tweets | Es a propósito: prefiere pocos y confirmados antes que rellenar con algo dudoso |
| Un medio no se pudo leer | Es normal (a veces bloquean); la skill lo cubre con búsqueda web y te avisa |
| Querés actualizar la skill | Reemplazá la carpeta por la nueva y corré `python instalar.py --actualizar` |
