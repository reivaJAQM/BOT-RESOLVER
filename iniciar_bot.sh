#!/bin/bash

# 1. Navegar a la carpeta donde está este mismo archivo (por si lo ejecutas desde otro lado)
cd "$(dirname "$0")"

# 2. Ejecutar el bot usando DIRECTAMENTE el Python del entorno virtual
# (Esto usa las librerías instaladas sin tener que escribir "activate")
./venv/bin/python3 bot_main.py

# 3. Pausa final para que puedas leer errores si algo falla antes de que se cierre la ventana
echo ""
read -p "Presiona ENTER para cerrar..."