"""Servidor MCP 1: búsqueda en las guías de nutrición (RAG)."""
import os
import re
from pathlib import Path

import numpy as np
import ollama
from mcp.server.fastmcp import FastMCP
from rank_bm25 import BM25Okapi

CARPETA_GUIAS = Path(__file__).resolve().parent.parent / "datos" / "guias"
# Buscador a usar: 'bm25', 'nomic-embed-text' o 'bge-m3' (el notebook elige el mejor y lo pasa aquí)
BUSCADOR = os.environ.get("BUSCADOR", "nomic-embed-text")

mcp = FastMCP("GuiasNutricion", host="localhost", port=9082)


def cargar_fragmentos():
    """Divide cada guía en fragmentos, uno por sección (##), guardando de dónde viene cada uno."""
    fragmentos = []
    for archivo in sorted(CARPETA_GUIAS.glob("*.md")):
        texto = archivo.read_text(encoding="utf-8")
        titulo = texto.splitlines()[0].lstrip("# ")
        for bloque in texto.split("\n## ")[1:]:
            seccion, _, contenido = bloque.partition("\n")
            fragmentos.append({
                "fuente": f"{archivo.name} › {seccion.strip()}",
                "texto": f"{titulo} > {seccion.strip()}. {' '.join(contenido.split())}",
            })
    return fragmentos


def tokenizar(texto):
    return re.findall(r"\w+", texto.lower())


def embeber(textos, es_pregunta=False):
    """Calcula embeddings con Ollama. nomic-embed-text funciona mejor con prefijos de tarea."""
    if BUSCADOR == "nomic-embed-text":
        prefijo = "search_query: " if es_pregunta else "search_document: "
        textos = [prefijo + t for t in textos]
    vectores = np.array(ollama.embed(model=BUSCADOR, input=textos)["embeddings"])
    return vectores / np.linalg.norm(vectores, axis=1, keepdims=True)


FRAGMENTOS = cargar_fragmentos()
if BUSCADOR == "bm25":
    bm25 = BM25Okapi([tokenizar(f["texto"]) for f in FRAGMENTOS])
else:
    VECTORES = embeber([f["texto"] for f in FRAGMENTOS])


@mcp.tool()
def buscar_guias(pregunta: str) -> str:
    """Busca en las guías de nutrición (OMS, ICBF, Ministerio de Salud de Colombia).

    Úsala para preguntas sobre recomendaciones de alimentación: azúcar, sal, grasas, proteína,
    frutas y verduras, agua, actividad física, IMC, sellos de advertencia, ultraprocesados o cómo
    armar comidas. Devuelve los 3 fragmentos más relevantes con su fuente entre corchetes.
    """
    if BUSCADOR == "bm25":
        puntajes = bm25.get_scores(tokenizar(pregunta))
    else:
        puntajes = VECTORES @ embeber([pregunta], es_pregunta=True)[0]
    mejores = np.argsort(puntajes)[::-1][:3]
    return "\n\n".join(f"[Fuente: {FRAGMENTOS[i]['fuente']}]\n{FRAGMENTOS[i]['texto']}" for i in mejores)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
