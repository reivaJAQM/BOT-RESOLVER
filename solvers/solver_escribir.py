from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import bot_memory as mem

def resolver(driver, sel, ia_utils, contexto, tipo_sub):
    """
    Resuelve Tipos de Escribir:
    - T10: Ordenar letras (Anagrama)
    - T11: Escribir la opción correcta (o Anagrama frases)
    - T12: Dictado
    """
    print(f"   🔍 [Solver Escribir] Analizando {tipo_sub}...")

    # Selectores comunes
    inputs = driver.find_elements(*sel.SELECTOR_INPUT_ESCRIBIR)
    if not inputs:
        print("      ❌ No se encontraron inputs para escribir.")
        return

    tareas = []
    
    # --- RECOLECCIÓN (Varía según subtipo) ---
    for i, inp in enumerate(inputs):
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inp)
        
        datos_tarea = {"input": inp, "id": i}
        
        if tipo_sub == "T10": # Letras desordenadas
            try:
                # Buscamos las letras asociadas a este input (asumiendo orden secuencial)
                letras_elems = driver.find_elements(*sel.SELECTOR_LETRAS_DESORDENADAS)
                if i < len(letras_elems):
                    datos_tarea["texto_raw"] = letras_elems[i].text.strip()
            except: pass
            
        elif tipo_sub in ["T11", "T12"]: # Frases o Dictado
            try:
                # Intentar leer la frase incompleta o contexto cercano
                frase_elem = inp.find_element(*sel.SELECTOR_FRASE_T11)
                datos_tarea["texto_raw"] = frase_elem.text.strip() + " ___"
            except: 
                datos_tarea["texto_raw"] = "Dictado/Frase desconocida ___"

        tareas.append(datos_tarea)
        print(f"      Input {i+1}: Contexto='{datos_tarea.get('texto_raw', '?')}'")

    # --- CONSULTA A MEMORIA / IA ---
    # Creamos clave única basada en los textos recolectados
    textos_clave = "|".join([t.get("texto_raw", "") for t in tareas])
    clave_memoria = f"{tipo_sub}:{textos_clave}"
    
    respuestas = mem.buscar(clave_memoria)
    
    if not respuestas:
        print(f"      🧠 Consultando IA ({tipo_sub})...")
        
        if tipo_sub == "T10":
            # Extraer solo los textos de las letras
            lista_letras = [t["texto_raw"] for t in tareas if "texto_raw" in t]
            respuestas = ia_utils.obtener_palabras_ordenadas_lote(lista_letras)
            
        elif tipo_sub == "T11":
            # T11 a veces es completar y a veces ordenar letras (híbrido raro)
            # Asumimos completar por defecto
            lista_frases = [{"frase": t["texto_raw"]} for t in tareas]
            respuestas = ia_utils.obtener_respuestas_escribir_opciones_lote(contexto, "", lista_frases)
            
        elif tipo_sub == "T12":
            # Dictado (Asumimos que IA adivina por contexto o dejamos ??? para aprender)
            print("      ⚠️ T12 Dictado: IA intentará adivinar por contexto (sin audio).")
            # Usamos lógica T11 como fallback
            lista_frases = [{"frase": t["texto_raw"]} for t in tareas]
            respuestas = ia_utils.obtener_respuestas_escribir_opciones_lote(contexto, "Dictado", lista_frases)

        if respuestas:
            mem.registrar(clave_memoria, respuestas)
            
    else:
        print(f"      💾 Memoria: {respuestas}")

    # --- EJECUCIÓN (ESCRIBIR) ---
    if respuestas and len(respuestas) == len(tareas):
        for tarea, respuesta in zip(tareas, respuestas):
            try:
                inp = tarea["input"]
                inp.clear()
                inp.send_keys(str(respuesta)) # Escribimos la respuesta
                print(f"      ✍️ Escribiendo: {respuesta}")
                time.sleep(0.2)
            except Exception as e:
                print(f"      ❌ Error escribiendo: {e}")
    else:
        print("      ⚠️ No tengo respuestas suficientes para todos los inputs.")