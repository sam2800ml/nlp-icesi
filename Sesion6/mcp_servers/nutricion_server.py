"""Servidor MCP 2: cálculos de salud y base de datos de alimentos."""
import csv
import unicodedata
from pathlib import Path

from mcp.server.fastmcp import FastMCP

RUTA_ALIMENTOS = Path(__file__).resolve().parent.parent / "datos" / "alimentos.csv"
mcp = FastMCP("Nutricion", host="localhost", port=9083)


def normalizar(texto):
    """Minúsculas y sin tildes, para que 'fríjol' y 'frijol' coincidan."""
    texto = unicodedata.normalize("NFKD", texto.lower().strip())
    return "".join(c for c in texto if not unicodedata.combining(c))


with open(RUTA_ALIMENTOS, encoding="utf-8") as f:
    ALIMENTOS = list(csv.DictReader(f))


@mcp.tool()
def calcular_imc(peso_kg: float, estatura_m: float) -> str:
    """Calcula el índice de masa corporal (IMC) y su clasificación según la OMS.

    peso_kg: peso en kilogramos. estatura_m: estatura en metros (por ejemplo 1.70).
    """
    if estatura_m > 3:  # los modelos pequeños a veces envían la estatura en centímetros
        estatura_m = estatura_m / 100
    imc = peso_kg / estatura_m ** 2
    if imc < 18.5:
        categoria = "bajo peso"
    elif imc < 25:
        categoria = "peso normal"
    elif imc < 30:
        categoria = "sobrepeso"
    else:
        categoria = "obesidad"
    return f"IMC = {imc:.1f} kg/m². Clasificación OMS: {categoria}."


@mcp.tool()
def calcular_calorias(peso_kg: float, estatura_cm: float, edad: int, sexo: str, actividad: str = "moderada") -> str:
    """Estima las calorías diarias de un adulto con la ecuación de Mifflin-St Jeor.

    sexo: 'hombre' o 'mujer'. actividad: 'sedentaria', 'ligera', 'moderada' o 'intensa'.
    """
    factores = {"sedentaria": 1.2, "ligera": 1.375, "moderada": 1.55, "intensa": 1.725}
    es_mujer = normalizar(sexo) in ("mujer", "femenino", "f")
    ajuste = -161 if es_mujer else 5
    tmb = 10 * peso_kg + 6.25 * estatura_cm - 5 * edad + ajuste
    factor = factores.get(normalizar(actividad), 1.55)
    return (f"Metabolismo basal: {tmb:.0f} kcal/día. Con actividad {actividad} (factor {factor}): "
            f"{tmb * factor:.0f} kcal/día.")


@mcp.tool()
def consultar_alimento(nombre: str, gramos: float = 100) -> str:
    """Consulta calorías, proteína, carbohidratos, grasa, fibra, azúcar y sodio de un alimento.

    nombre: alimento a buscar (por ejemplo 'pollo', 'banano', 'fríjol'). gramos: cantidad, 100 por defecto.
    """
    buscado = normalizar(nombre)
    singular = buscado[:-2] if buscado.endswith("es") else buscado.rstrip("s")  # 'fríjoles' -> 'frijol'
    for fila in ALIMENTOS:
        alimento = normalizar(fila["alimento"])
        if buscado in alimento or singular in alimento or alimento in buscado:
            f = gramos / 100
            return (f"{fila['alimento']} ({gramos:g} g): {float(fila['kcal']) * f:.1f} kcal, "
                    f"proteína {float(fila['proteina_g']) * f:.1f} g, carbohidratos {float(fila['carbohidratos_g']) * f:.1f} g, "
                    f"grasa {float(fila['grasa_g']) * f:.1f} g, fibra {float(fila['fibra_g']) * f:.1f} g, "
                    f"azúcar {float(fila['azucar_g']) * f:.1f} g, sodio {float(fila['sodio_mg']) * f:.0f} mg.")
    return f"No encontré '{nombre}' en la base de alimentos."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
