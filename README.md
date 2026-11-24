## Tokenizador
Este programa sirve para escribir una conversación entre dos personas y ver cuántos tokens usa cada mensaje en distintos modelos de inteligencia artificial.

## Que se necesita:
- Python 3.9 o una versión más nueva
- Internet, para descargar los tokenizadores la primera vez

## Cómo instalarlo
Escribe esto en la terminal:
```bash
pip install huggingface_hub tokenizers
```

## Cómo usarlo
Escribe esto en la terminal, dentro de la carpeta del programa:

```bash
python probar.py
```

Comandos que puedes usar:

| Comando | Qué hace |
|---|---|
| `/a` y `/b` | Cambian a quién le toca escribir |
| `/multi` | Te deja escribir varias líneas; para terminar, escribe un punto `.` solo en una línea |
| `/deshacer` | Borra el último mensaje |
| `/ver` | Muestra la conversación y cuántos caracteres tiene cada mensaje |
| `/guardar` | Guarda la conversación en un archivo llamado `conversacion.json` |
| `/fin` | Termina el programa y cuenta los tokens |
| `/fin --detalle` | Lo mismo, pero también muestra los tokens de cada mensaje |
| `/ayuda` | Muestra la lista de comandos |

## Modelos que piden permiso
Algunos modelos, como Llama y Muse, necesitan que aceptes su licencia en la página de Hugging Face. Si el programa muestra un error 401 o 403, sigue estos pasos:

1. Entra a la página del modelo y acepta la licencia.
2. En la terminal, escribe:

```bash
hf auth login
```

## Notas

- La conversación se guarda en `conversacion.json`. Ese archivo no se sube a GitHub.
- El conteo solo cuenta lo que escriben las personas. No cuenta el texto oculto que usa el chat ni las instrucciones del servicio.
