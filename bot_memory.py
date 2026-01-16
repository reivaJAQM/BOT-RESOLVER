import json
import os

MEMORIA_FILE = "memoria_bot.json"
soluciones_correctas = {}
preguntas_ya_vistas = {} # Caché temporal de sesión

def cargar():
    """Carga la memoria del disco."""
    global soluciones_correctas
    if os.path.exists(MEMORIA_FILE):
        try:
            with open(MEMORIA_FILE, 'r', encoding='utf-8') as f:
                soluciones_correctas = json.load(f)
            print(f"✅ [Memoria] Cargada: {len(soluciones_correctas)} registros.")
        except Exception as e:
            print(f"⚠️ [Memoria] Error al cargar: {e}")
            soluciones_correctas = {}
    else:
        print("ℹ️ [Memoria] No existe archivo previo.")

def guardar():
    """Guarda la memoria en disco."""
    try:
        with open(MEMORIA_FILE, 'w', encoding='utf-8') as f:
            json.dump(soluciones_correctas, f, indent=4, ensure_ascii=False)
        print("💾 [Memoria] Guardada.")
    except Exception as e:
        print(f"❌ [Memoria] Error crítico al guardar: {e}")

def buscar(clave):
    return soluciones_correctas.get(clave)

def registrar(clave, valor):
    """Registra y guarda inmediatamente."""
    # Lógica de listas/rotación básica
    existente = soluciones_correctas.get(clave)
    
    # Si es nuevo, guardar
    if not existente:
        if not isinstance(valor, list): valor = [valor] # Estandarizar a lista
        soluciones_correctas[clave] = valor
        guardar()
    elif isinstance(existente, list) and isinstance(valor, list):
         # Si ya existe, añadir si es nuevo (para rotación)
         if valor[0] not in existente:
             existente.extend(valor)
             soluciones_correctas[clave] = existente
             guardar()

# Cargar al importar
cargar()