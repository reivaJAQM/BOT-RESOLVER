import json
import os

MEMORIA_FILE = "memoria_bot.json"
BACKUP_FILE = "memoria_bot.backup.json"

# --- NO TOCAR ---
CLAVE_A_BORRAR = "T4:"
# --- NO TOCAR ---

if not os.path.exists(MEMORIA_FILE):
    print(f"No se encontró el archivo '{MEMORIA_FILE}'. No hay nada que limpiar.")
    exit()

print(f"Cargando memoria desde '{MEMORIA_FILE}'...")
try:
    with open(MEMORIA_FILE, 'r', encoding='utf-8') as f:
        memoria_antigua = json.load(f)
    print(f"Memoria cargada. {len(memoria_antigua)} claves encontradas.")
except Exception as e:
    print(f"Error al leer el JSON: {e}")
    exit()

# --- Crear un backup por seguridad ---
try:
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(memoria_antigua, f, indent=4, ensure_ascii=False)
    print(f"¡Backup creado con éxito en '{BACKUP_FILE}'!")
except Exception as e:
    print(f"ERROR al crear el backup: {e}")
    exit()

# --- Filtrar la memoria ---
memoria_nueva = {}
claves_borradas = 0
claves_mantenidas = 0

print(f"Filtrando claves... Se borrarán todas las que empiecen con '{CLAVE_A_BORRAR}'")
for clave, valor in memoria_antigua.items():
    if clave.startswith(CLAVE_A_BORRAR):
        claves_borradas += 1
    else:
        memoria_nueva[clave] = valor
        claves_mantenidas += 1

print("\n--- ¡Filtrado Completo! ---")
print(f"Claves Mantenidas: {claves_mantenidas}")
print(f"Claves TIPO 4 Borradas: {claves_borradas}")
print(f"Total Claves Nuevas: {len(memoria_nueva)}")

# --- Guardar la nueva memoria limpia ---
try:
    with open(MEMORIA_FILE, 'w', encoding='utf-8') as f:
        json.dump(memoria_nueva, f, indent=4, ensure_ascii=False)
    print(f"\n¡ÉXITO! Se ha limpiado y guardado la nueva memoria en '{MEMORIA_FILE}'.")
except Exception as e:
    print(f"ERROR CRÍTICO al guardar la nueva memoria: {e}")
    print("Restaura tu memoria desde el backup si es necesario.")
