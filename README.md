# Contador de tokens para conversaciones

Este programa sirve para escribir una conversación entre dos personas y ver cuántos tokens usa cada mensaje en distintos modelos de inteligencia artificial.
Esto con el objetivo de poder configurar los modelos de acuerdo al gasto detokens aproximado por conversación. 
**Este script solamente calcula los tokens por peticion enviada, ya sea por la persona o el modelo de IA. No calcula los tokens cuando el modelo de IA realiza una consulta a una herramienta (ejemp. un endpoint)**

## Qué es un token?

Los tokens son los pedacitos en que un modelo divide un texto para poder leerlo. Un mismo texto puede tener más tokens en un modelo que en otro, porque cada modelo usa su propio tokenizador. Este programa usa los tokenizadores oficiales de Hugging Face, así que los números son exactos, no una estimación.

## Lo que necesitas

- Python 3.10 o una versión más nueva descargada en la computadora que vaya a utilizar el script
- Internet, para descargar los tokenizadores la primera vez
- Una cuenta en Hugging Face (solo si vas a usar modelos con licencia, ver más abajo)

## Cómo instalarlo

Escribe esto en la terminal:

```bash
pip install huggingface_hub tokenizers
```

Solo tienes que hacerlo una vez en cada computadora.

## Cómo usarlo

Entra a la carpeta del programa y escribe:

```bash
python probar.py
```

El programa te pedirá el nombre de las dos personas. Si dejas el campo vacío, se llamarán "Persona A" y "Persona B".

Después escribe los mensajes uno por uno. Los turnos se alternan solos: A, B, A, B...

### Ejemplo

```
[1] Ana > Hola, ¿cómo estás?
[2] Luis > Muy bien, ¿y tú?
[3] Ana > También. ¿Vamos al cine?
[4] Ana > /fin
```

Con `/fin`, el programa cuenta los tokens de cada mensaje y muestra una tabla.

## Comandos

| Comando | Qué hace |
|---|---|
| `/a` y `/b` | Cambian a quién le toca escribir |
| `/multi` | Te deja escribir varias líneas; para terminar, escribe un punto `.` solo en una línea |
| `/deshacer` | Borra el último mensaje |
| `/ver` | Muestra la conversación y cuántos caracteres tiene cada mensaje |
| `/guardar` | Guarda la conversación en `conversacion.json` |
| `/fin` | Termina el programa y cuenta los tokens |
| `/fin --detalle` | Lo mismo, pero también muestra los tokens de cada mensaje |
| `/ayuda` | Muestra la lista de comandos |


Si quieres un mensaje que empiece con `/`, escribe dos: `//texto` se envía como `/texto`.

## Cómo leer la tabla

- **Persona A y Persona B** muestran cuántos tokens usó cada persona.
- **Total** es la suma de los dos.
- **Prom/mensaje** es el promedio de tokens por mensaje.
- Al final, el programa dice qué modelo usa menos tokens y cuál usa más.

## Si cierras el programa sin usar /fin

Presiona `Ctrl + C`. El programa guarda la conversación en `conversacion.json`. La próxima vez que lo ejecutes, te preguntará si quieres continuarla.

## Licencias de algunos modelos

Algunos modelos, como **Llama** y **Muse**, tienen una licencia que hay que aceptar antes de poder descargar su tokenizador. Si no lo haces, el programa muestra un error 401 o 403 en la fila de ese modelo. Los demás modelos se calculan igual.

Sigue estos pasos una sola vez para cada modelo que lo pida:

### Paso 1: Crea una cuenta en Hugging Face

Entra a https://huggingface.co y regístrate. Es gratis.

### Paso 2: Acepta la licencia del modelo

1. Entra a la página del modelo. Por ejemplo:
   - https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct
   - https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct
   - https://huggingface.co/meta-models/Muse-Spark-open-816B-A42B
2. Busca el botón que dice algo como **"Agree and access repository"** o **"Accept license"**.
3. Haz clic y acepta. Algunas licencias se aprueban al instante; otras pueden tardar un poco.

### Paso 3: Crea un token de acceso

1. Entra a https://huggingface.co/settings/tokens.
2. Haz clic en **New token**.
3. Ponle un nombre, por ejemplo `tokenizers`, y elige el tipo **Read** (solo lectura).
4. Copia el token que aparece. Solo se muestra una vez.
Esto con la finalidad de autenticar aplicaciones, scripts o cuadernos y descargar o leer modelos, conjuntos de datos y repositorios a los que se tiene permiso

### Paso 4: Inicia sesión desde la terminal

Escribe:

```bash
hf auth login
```

Cuando te pida el token, pégalo y presiona Enter. La terminal no muestra lo que escribes, así que es normal que no veas nada.

**Importante:** no compartas tu token con nadie, no lo subas a GitHub y no lo pegues en chats. Si alguien lo consigue, puede usar tu cuenta. Si crees que se filtró, bórralo en la página de tokens y crea uno nuevo.

### Paso 5: Vuelve a ejecutar el programa

```bash
python probar.py
```

Si el modelo ya tiene su licencia aceptada, ahora aparecerá con su número de tokens.

## Problemas comunes

- **`ModuleNotFoundError: No module named 'huggingface_hub'`**: falta instalar la librería. Ejecuta el comando de instalación de arriba.
- **`can't open file 'probar.py'`**: estás en otra carpeta. Usa `cd` para entrar a la carpeta donde está el archivo.
- **Error 401 o 403 en Llama o Muse**: no has aceptado la licencia o no has iniciado sesión. Revisa los pasos de licencias.
- **Todos los modelos fallan**: revisa tu conexión a internet.

## Archivos del proyecto

- `probar.py`: el programa principal.
- `.gitignore`: lista los archivos que no se suben a GitHub.
- `README.md`: este archivo.

El archivo `conversacion.json` se crea solo cuando guardas, y no se sube al repositorio.

## Notas

- El conteo solo cuenta el contenido de los mensajes. No incluye el texto oculto que usa el chat ni las instrucciones del servicio.
- Este programa no llama a ninguna API de IA y no pide claves de acceso para contar tokens, ya que son modelos de pesos abiertos (algunos con aprobación de su uso mediante licencia). El token de Hugging Face solo sirve para descargar tokenizadores con licencia del servicio.
