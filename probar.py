# -*- coding: utf-8 -*-
"""
Evaluador de conversaciones en vivo entre DOS personas.
Cuenta tokens con los tokenizadores EXACTOS de Hugging Face (tokenizer.json).
No llama a APIs de proveedores ni pide API keys.

Uso:  python probar.py
"""
import os
import sys
import json

# Debe definirse ANTES de importar huggingface_hub
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# UTF-8 en la consola de Windows (acentos, ñ, ¿, ¡)
if os.name == "nt":
    os.system("chcp 65001 >nul")
for flujo in (sys.stdin, sys.stdout, sys.stderr):
    try:
        flujo.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

MODELOS = {
    "qwen":            "Qwen/Qwen2.5-7B-Instruct",
    "deepseek":        "deepseek-ai/DeepSeek-V3",
    "muse":            "meta-models/Muse-Spark-open-816B-A42B",
    "deepseek41":      "deepseek-ai/DeepSeek-V4.1-Flash",
    "qwen38":          "Qwen/Qwen3.8-27B",
    "mistral_medium":  "mistralai/Mistral-Medium-3.5-128B",
    "mistral_large":   "mistralai/Mistral-Large-4-1T-A52B",
    "mimo":            "XiaomiMiMo/MiMo-V2.6-Pro-RL",
    "llama4_maverick": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
    "llama4_scout":    "meta-llama/Llama-4-Scout-17B-16E-Instruct",
}

ARCHIVO = "conversacion.json"
NOTA = ("Cuenta el contenido de los mensajes; no incluye la plantilla oculta "
        "del chat ni el prompt de sistema del servicio.")

AYUDA = """Comandos:
  /a [texto]      el siguiente mensaje es de {A} (si pones texto, se envía ya)
  /b [texto]      el siguiente mensaje es de {B} (si pones texto, se envía ya)
  /multi          mensaje de varias líneas; termina con una línea que sea solo "."
  /deshacer       borra el último mensaje
  /ver            lista la conversación con los caracteres de cada mensaje
  /guardar        guarda en conversacion.json
  /fin            termina y calcula los tokens
  /fin --detalle  además muestra los tokens de cada mensaje con un modelo
                  (opcional: /fin --detalle qwen  para elegir el modelo)
  /ayuda          muestra esta ayuda
  //texto         envía un mensaje que empieza por "/" (se envía "/texto")"""


# ---------------------------------------------------------------- utilidades
def guardar(nombres, mensajes, silencioso=False):
    datos = {"personas": {"A": nombres["A"], "B": nombres["B"]},
             "mensajes": mensajes}
    tmp = ARCHIVO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ARCHIVO)
    if not silencioso:
        print(f"  ✔ Conversación guardada en {os.path.abspath(ARCHIVO)} "
              f"({len(mensajes)} mensajes)")


def cargar():
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        datos = json.load(f)
    p = datos.get("personas", {})
    nombres = {"A": p.get("A") or "Persona A", "B": p.get("B") or "Persona B"}
    mensajes = []
    for m in datos.get("mensajes", []):
        if m.get("quien") in ("A", "B") and isinstance(m.get("texto"), str):
            mensajes.append({"quien": m["quien"], "texto": m["texto"]})
    return nombres, mensajes


def preguntar_si_no(pregunta, defecto=True):
    sufijo = " [S/n]: " if defecto else " [s/N]: "
    r = input(pregunta + sufijo).strip().lower()
    if not r:
        return defecto
    return r in ("s", "si", "sí", "y", "yes")


def otro(quien):
    return "B" if quien == "A" else "A"


def leer_multilinea(nombre):
    print(f"  (Modo varias líneas para {nombre}. Escribe una línea con solo "
          f"\".\" para terminar.)")
    lineas = []
    while True:
        linea = input("  … ")
        if linea.strip() == ".":
            break
        lineas.append(linea)
    return "\n".join(lineas)


def mostrar_conversacion(nombres, mensajes):
    if not mensajes:
        print("  (La conversación está vacía.)")
        return
    print()
    total = 0
    for i, m in enumerate(mensajes, 1):
        n = len(m["texto"])
        total += n
        lineas = m["texto"].split("\n")
        print(f"  {i:>3}. {nombres[m['quien']]} [{n} caracteres]: {lineas[0]}")
        for extra in lineas[1:]:
            print(f"       {extra}")
    print(f"  --- {len(mensajes)} mensajes, {total} caracteres en total\n")


def es_error_de_red(e):
    nombre = type(e).__name__
    return any(p in nombre for p in ("Proxy", "Connection", "Timeout",
                                     "OfflineMode", "LocalEntryNotFound"))


def es_error_de_acceso(e):
    if es_error_de_red(e):
        return False
    nombre = type(e).__name__
    if nombre in ("GatedRepoError", "RepositoryNotFoundError"):
        return True
    resp = getattr(e, "response", None)
    codigo = getattr(resp, "status_code", None)
    if codigo in (401, 403):
        return True
    texto = str(e)
    return any(c in texto for c in ("401", "403", "gated", "Unauthorized",
                                    "Forbidden", "restricted"))


def describir_error(e):
    txt = " ".join(str(e).split())
    return f"{type(e).__name__}: {txt[:110]}"


# ---------------------------------------------------------------- tokens
def calcular_tokens(nombres, mensajes, detalle=False, modelo_detalle=None):
    if not mensajes:
        print("\nNo hay mensajes; no hay nada que contar.")
        return

    textos = [m["texto"] for m in mensajes]
    n_a = sum(1 for m in mensajes if m["quien"] == "A")
    n_b = len(mensajes) - n_a
    print(f"\nCalculando tokens de {len(mensajes)} mensajes "
          f"({nombres['A']}: {n_a}, {nombres['B']}: {n_b})...")
    print("Descargando tokenizadores (solo la primera vez; luego usa la caché).\n")

    resultados = {}   # nombre -> dict(a, b, total, prom, por_mensaje) o dict(error)
    for nombre, repo in MODELOS.items():
        print(f"  {nombre:16} ...", end="", flush=True)
        try:
            ruta = hf_hub_download(repo, "tokenizer.json")
            tok = Tokenizer.from_file(ruta)          # una sola vez por modelo
            por_mensaje = [len(tok.encode(t, add_special_tokens=False).ids)
                           for t in textos]
            a = sum(n for n, m in zip(por_mensaje, mensajes) if m["quien"] == "A")
            b = sum(n for n, m in zip(por_mensaje, mensajes) if m["quien"] == "B")
            total = a + b
            resultados[nombre] = {"a": a, "b": b, "total": total,
                                  "prom": total / len(mensajes),
                                  "por_mensaje": por_mensaje}
            print(" ok")
        except Exception as e:
            info = {"error": describir_error(e), "acceso": es_error_de_acceso(e),
                    "red": es_error_de_red(e), "repo": repo}
            resultados[nombre] = info
            print(" falló")

    # ---- tabla
    col_a = nombres["A"][:14]
    col_b = nombres["B"][:14]
    ancho = 16 + 3 + 14 + 3 + 14 + 3 + 10 + 3 + 12
    print("\n" + "=" * ancho)
    print(f"{'Modelo':16} | {col_a:>14} | {col_b:>14} | {'Total':>10} | "
          f"{'Prom/mensaje':>12}")
    print("-" * ancho)
    for nombre, r in resultados.items():
        if "error" in r:
            print(f"{nombre:16} | FALLÓ: {r['error']}")
            if r["acceso"]:
                print(f"{'':16} |   → Inicia sesión con \"hf auth login\" o acepta "
                      f"la licencia en https://huggingface.co/{r['repo']}")
            elif r["red"]:
                print(f"{'':16} |   → Problema de red/proxy: revisa tu conexión "
                      f"a huggingface.co")
        else:
            print(f"{nombre:16} | {r['a']:>14} | {r['b']:>14} | "
                  f"{r['total']:>10} | {r['prom']:>12.1f}")
    print("=" * ancho)

    ok = {n: r for n, r in resultados.items() if "error" not in r}
    if ok:
        minimo = min(r["total"] for r in ok.values())
        maximo = max(r["total"] for r in ok.values())
        menos = [n for n, r in ok.items() if r["total"] == minimo]
        mas = [n for n, r in ok.items() if r["total"] == maximo]
        if minimo == maximo:
            print(f"Todos los modelos disponibles dan el mismo total ({minimo}).")
        else:
            print(f"Menos tokens: {', '.join(menos)} ({minimo})")
            print(f"Más tokens:   {', '.join(mas)} ({maximo})")
            if minimo:
                print(f"Diferencia:   {maximo - minimo} tokens "
                      f"({(maximo - minimo) / minimo * 100:.1f}% más que el mínimo)")
    else:
        print("Ningún modelo pudo cargarse. Revisa tu conexión a internet o "
              "inicia sesión con \"hf auth login\".")
    fallidos = len(resultados) - len(ok)
    if fallidos:
        print(f"({fallidos} modelo(s) fallaron y no se incluyen en la comparación.)")
    print(NOTA)

    # ---- detalle por mensaje
    if detalle and ok:
        if modelo_detalle and modelo_detalle not in MODELOS:
            print(f"\nEl modelo \"{modelo_detalle}\" no existe en la lista; "
                  f"uso el primero disponible.")
            modelo_detalle = None
        if modelo_detalle and modelo_detalle not in ok:
            print(f"\nEl modelo \"{modelo_detalle}\" falló; uso el primero "
                  f"disponible.")
            modelo_detalle = None
        elegido = modelo_detalle or next(iter(ok))
        por_mensaje = ok[elegido]["por_mensaje"]
        print(f"\nDetalle por mensaje con el modelo: {elegido} "
              f"({MODELOS[elegido]})")
        print("-" * ancho)
        for i, (m, n) in enumerate(zip(mensajes, por_mensaje), 1):
            primera = m["texto"].split("\n")[0]
            if len(primera) > 50 or "\n" in m["texto"]:
                primera = primera[:50] + "…"
            print(f"{i:>4}. {nombres[m['quien']][:14]:14} {n:>6} tokens "
                  f"{len(m['texto']):>6} car.  {primera}")
        print("-" * ancho)


# ---------------------------------------------------------------- principal
def main():
    print("=== Evaluador de conversaciones entre dos personas ===\n")

    nombres, mensajes = None, []
    if os.path.exists(ARCHIVO):
        try:
            n_prev, m_prev = cargar()
            print(f"Se encontró {ARCHIVO}: {n_prev['A']} y {n_prev['B']}, "
                  f"{len(m_prev)} mensajes.")
            if preguntar_si_no("¿Quieres continuar esa conversación?"):
                nombres, mensajes = n_prev, m_prev
            else:
                print("Se empezará una nueva (el archivo se sobrescribirá al "
                      "guardar).")
        except Exception as e:
            print(f"No se pudo leer {ARCHIVO} ({describir_error(e)}). "
                  f"Se empezará una nueva.")

    if nombres is None:
        a = input("Nombre de la primera persona [Persona A]: ").strip() or "Persona A"
        b = input("Nombre de la segunda persona [Persona B]: ").strip() or "Persona B"
        if b == a:
            b = b + " (2)"
        nombres = {"A": a, "B": b}

    turno = otro(mensajes[-1]["quien"]) if mensajes else "A"
    print("\n" + AYUDA.format(A=nombres["A"], B=nombres["B"]) + "\n")
    if mensajes:
        mostrar_conversacion(nombres, mensajes)

    try:
        while True:
            linea = input(f"[{len(mensajes) + 1}] {nombres[turno]} > ")
            entrada = linea.strip()
            if not entrada:
                continue

            texto = None
            if entrada.startswith("//"):
                texto = linea.lstrip()[1:]
            elif entrada.startswith("/"):
                partes = entrada.split(maxsplit=1)
                cmd = partes[0].lower()
                resto = partes[1] if len(partes) > 1 else ""

                if cmd in ("/a", "/b"):
                    turno = cmd[1].upper()
                    if resto:
                        texto = resto
                    else:
                        continue
                elif cmd == "/multi":
                    texto = leer_multilinea(nombres[turno])
                    if not texto.strip():
                        print("  (Mensaje vacío; no se agregó.)")
                        continue
                elif cmd == "/deshacer":
                    if mensajes:
                        quitado = mensajes.pop()
                        turno = quitado["quien"]
                        vista = quitado["texto"].split("\n")[0][:60]
                        print(f"  ✖ Borrado el mensaje de {nombres[quitado['quien']]}: "
                              f"{vista!r}")
                    else:
                        print("  (No hay mensajes que borrar.)")
                    continue
                elif cmd == "/ver":
                    mostrar_conversacion(nombres, mensajes)
                    continue
                elif cmd == "/guardar":
                    guardar(nombres, mensajes)
                    continue
                elif cmd == "/fin":
                    opciones = resto.split()
                    detalle = "--detalle" in opciones
                    otros = [o for o in opciones if o != "--detalle"]
                    modelo_det = otros[0].lower() if otros else None
                    if mensajes:
                        guardar(nombres, mensajes)
                    calcular_tokens(nombres, mensajes, detalle, modelo_det)
                    return
                elif cmd in ("/ayuda", "/help", "/?"):
                    print(AYUDA.format(A=nombres["A"], B=nombres["B"]))
                    continue
                else:
                    print(f"  Comando desconocido: {cmd}. Escribe /ayuda. "
                          f"(Para enviar un texto que empiece por \"/\", usa \"//\".)")
                    continue
            else:
                texto = linea

            mensajes.append({"quien": turno, "texto": texto})
            turno = otro(turno)

    except (KeyboardInterrupt, EOFError):
        print("\n\nInterrumpido antes de /fin.")
        if mensajes:
            guardar(nombres, mensajes)
            print("  La próxima vez que ejecutes el programa podrás continuarla.")
        else:
            print("  No había mensajes que guardar.")


if __name__ == "__main__":
    main()
    
