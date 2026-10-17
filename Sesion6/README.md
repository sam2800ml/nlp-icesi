# Sesión 6 · NutriBot

Asistente de nutrición que responde citando 12 guías (OMS, ICBF, MinSalud), calcula el IMC y las calorías diarias y consulta una base de 54 alimentos. Usa un LLM local (Ollama), dos servidores MCP propios y un chat en Gradio.

**Video de la demo:** _pega aquí el enlace_

```
Sesion6/
├── nutribot.ipynb
├── mcp_servers/
│   ├── guias_server.py       ← MCP 1 (puerto 9082): buscar_guias (RAG)
│   └── nutricion_server.py   ← MCP 2 (puerto 9083): calcular_imc, calcular_calorias, consultar_alimento
└── datos/
    ├── guias/                ← 12 guías en Markdown
    └── alimentos.csv         ← 54 alimentos (valores por 100 g)
```

**Ejecutar en Colab:** GPU T4 → poner tu usuario y repositorio en la celda 2.2 → Ejecutar todas (10 a 15 minutos).

**Ejecutar en local:** `pip install -r requirements.txt`, tener `ollama serve` corriendo y abrir el notebook desde esta carpeta.

> Proyecto académico: no reemplaza la consulta con un profesional de la salud.
