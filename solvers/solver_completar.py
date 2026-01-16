from selenium.webdriver.common.by import By
import time
import bot_memory as mem

def resolver(driver, sel, ia_utils, contexto):
    """
    Resuelve TIPO 2: Completar frases (Clic en botones dentro de la línea).
    Retorna datos para aprendizaje.
    """
    print("   🔍 [Solver Completar] Analizando líneas...")
    
    lineas = driver.find_elements(*sel.SELECTOR_LINEAS_COMPLETAR)
    if not lineas:
        print("      ❌ No se encontraron líneas de completar.")
        return None

    tareas = []
    
    # 1. Recolectar Tareas
    for i, linea in enumerate(lineas):
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", linea)
        
        # Extraer fragmentos de texto para reconstruir la frase con "___"
        spans = linea.find_elements(By.XPATH, "./div/span[@class='inline-block']")
        botones = linea.find_elements(*sel.SELECTOR_BOTONES_OPCION_COMPLETAR)
        opciones = [b.text.strip() for b in botones if b.text.strip()]
        
        if not opciones: continue
        
        frase_reconstruida = ""
        placeholder_puesto = False
        
        # Reconstrucción inteligente de la frase
        for span in spans:
            # Si el span NO tiene botones, es texto
            if not span.find_elements(*sel.SELECTOR_BOTONES_OPCION_COMPLETAR):
                frase_reconstruida += span.text.strip() + " "
            # Si tiene botones y aun no ponemos el hueco
            elif not placeholder_puesto:
                frase_reconstruida += "___ "
                placeholder_puesto = True
        
        if not placeholder_puesto: frase_reconstruida += "___"
        
        frase_limpia = ' '.join(frase_reconstruida.split())
        print(f"      Línea {i+1}: '{frase_limpia}' | Ops: {opciones}")
        
        tareas.append({
            "frase": frase_limpia, 
            "opciones": opciones, 
            "botones": botones
        })
    
    if not tareas: return None

    # --- CLAVE DE MEMORIA ---
    frases_clave = sorted([t['frase'] for t in tareas])
    clave_memoria = f"T2_BATCH:||CTX:{contexto[:30]}||FRASES:{'|'.join(frases_clave)}"
    
    # --- RESOLUCIÓN ---
    # 1. MEMORIA (Dict {frase: respuesta})
    solucion_dict = mem.buscar(clave_memoria)
    
    # 2. IA
    if not solucion_dict:
        print("      🧠 Consultando IA (Lote Completar)...")
        respuestas_lista = ia_utils.obtener_palabras_correctas_lote(contexto, tareas)
        
        if respuestas_lista and len(respuestas_lista) == len(tareas):
            # Convertimos a dict para guardar en memoria: {frase: respuesta}
            solucion_dict = {t["frase"]: r for t, r in zip(tareas, respuestas_lista)}
            mem.registrar(clave_memoria, solucion_dict)
    else:
        print(f"      💾 Memoria: {len(solucion_dict)} respuestas recuperadas.")

    # 3. CLICK
    if solucion_dict:
        for tarea in tareas:
            frase = tarea["frase"]
            if frase in solucion_dict:
                respuesta = solucion_dict[frase]
                # Buscar el botón que coincida con la respuesta
                btn_click = None
                for b in tarea["botones"]:
                    if b.text.strip().lower() == respuesta.lower():
                        btn_click = b
                        break
                
                if btn_click:
                    driver.execute_script("arguments[0].click();", btn_click)
                    print(f"      ✅ Click: '{respuesta}'")
                    time.sleep(0.3)
                else:
                    print(f"      ❌ Botón '{respuesta}' no encontrado en opciones.")
            else:
                print(f"      ⚠️ Sin respuesta para: '{frase}'")

    # --- RETORNO PARA APRENDIZAJE ---
    # Para T2 devolvemos dicts con frase y opciones para que el extractor sepa qué buscar
    return {
        "clave": clave_memoria,
        "items": [{"frase": t["frase"], "opciones": t["opciones"]} for t in tareas]
    }