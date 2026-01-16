from selenium.webdriver.common.by import By
import time
import bot_memory as mem

def resolver(driver, sel, ia_utils, contexto, tipo_sub):
    """
    Resuelve Tipos de Escribir:
    - T10: Anagrama (Letras desordenadas)
    - T11: Escribir la opción correcta
    - T12: Dictado
    Retorna datos para aprendizaje.
    """
    print(f"   🔍 [Solver Escribir] Analizando {tipo_sub}...")

    # 1. Detectar inputs
    inputs = driver.find_elements(*sel.SELECTOR_INPUT_ESCRIBIR)
    if not inputs:
        print("      ❌ No se encontraron inputs para escribir.")
        return None

    tareas = []
    
    # --- RECOLECCIÓN DE DATOS ---
    for i, inp in enumerate(inputs):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inp)
            datos_tarea = {"input": inp, "id": i}
            
            if tipo_sub == "T10": # Anagrama
                try:
                    letras_elems = driver.find_elements(*sel.SELECTOR_LETRAS_DESORDENADAS)
                    if i < len(letras_elems):
                        datos_tarea["texto_raw"] = letras_elems[i].text.strip()
                except: pass
                
            elif tipo_sub in ["T11", "T12"]: # Frases o Dictado
                try:
                    # Buscamos el texto guía cerca del input
                    frase_elem = inp.find_element(*sel.SELECTOR_FRASE_T11)
                    datos_tarea["texto_raw"] = frase_elem.text.strip()
                except: 
                    datos_tarea["texto_raw"] = "Contexto desconocido"

            if "texto_raw" not in datos_tarea:
                datos_tarea["texto_raw"] = f"input_{i}"

            tareas.append(datos_tarea)
            print(f"      Item {i+1}: '{datos_tarea['texto_raw'][:40]}...'")
        except: pass

    if not tareas: return None

    # --- CLAVE DE MEMORIA ---
    textos_clave = "|".join([t["texto_raw"] for t in tareas])
    clave_memoria = f"{tipo_sub}:{textos_clave}"
    
    # --- RESOLUCIÓN ---
    # 1. MEMORIA
    respuestas = mem.buscar(clave_memoria)
    
    # 2. IA
    if not respuestas:
        print(f"      🧠 Consultando IA...")
        if tipo_sub == "T10":
            lista_letras = [t["texto_raw"] for t in tareas]
            respuestas = ia_utils.obtener_palabras_ordenadas_lote(lista_letras)
        elif tipo_sub == "T11":
            lista_frases = [{"frase": t["texto_raw"]} for t in tareas]
            # Verificamos si el título indica que es un anagrama aunque sea T11
            try:
                titulo = driver.find_element(*sel.SELECTOR_PREGUNTA).text.lower()
                if "order the letters" in titulo or "put in order" in titulo:
                    respuestas = ia_utils.obtener_palabras_ordenadas_lote([t["texto_raw"] for t in tareas])
                else:
                    respuestas = ia_utils.obtener_respuestas_escribir_opciones_lote(contexto, titulo, lista_frases)
            except:
                respuestas = ia_utils.obtener_respuestas_escribir_opciones_lote(contexto, "", lista_frases)
        elif tipo_sub == "T12":
            # Dictado: Si no hay memoria, escribimos temporalmente '???' para forzar aprendizaje
            respuestas = ["???"] * len(tareas)
            print("      ⚠️ T12 Dictado: Sin memoria, se escribirá '???' para aprender de la corrección.")

        if respuestas:
            mem.registrar(clave_memoria, respuestas)
    else:
        print(f"      💾 Memoria: {respuestas}")

    # 3. ESCRIBIR
    if respuestas and len(respuestas) == len(tareas):
        for tarea, resp in zip(tareas, respuestas):
            try:
                inp = tarea["input"]
                inp.clear()
                inp.send_keys(str(resp))
                print(f"      ✍️ Escribiendo: {resp}")
                time.sleep(0.2)
            except: pass

    # --- RETORNO PARA APRENDIZAJE ---
    # Es vital indicar si es anagrama para que el main use el extractor correcto
    es_anagrama = (tipo_sub == "T10")
    if tipo_sub == "T11":
        try:
            titulo = driver.find_element(*sel.SELECTOR_PREGUNTA).text.lower()
            if "order" in titulo or "letters" in titulo: es_anagrama = True
        except: pass

    return {
        "clave": clave_memoria,
        "items": [t["texto_raw"] for t in tareas],
        "es_anagrama": es_anagrama
    }