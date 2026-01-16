from selenium.webdriver.common.by import By
import time
import bot_memory as mem

def resolver(driver, sel, ia_utils, contexto, tipo):
    """
    Maneja preguntas de selección:
    - T6: Relacionar Idea con Párrafo (Botones 1, 2, 3...)
    - T7: Preguntas de comprensión / Selección Múltiple
    Retorna datos para aprendizaje.
    """
    print(f"   🔍 [Solver Selección] Analizando {tipo}...")

    tareas = []
    
    # --- RECOLECCIÓN DE DATOS ---
    if tipo == "T6":
        # TIPO 6: Párrafos (Idea -> Número)
        cajas = driver.find_elements(*sel.SELECTOR_PARAGRAPH_CAJAS)
        for i, caja in enumerate(cajas):
            try:
                txt = caja.find_element(*sel.SELECTOR_PARAGRAPH_IDEA_TEXT).text.strip()
                # Filtramos solo botones numéricos
                btns = [b for b in caja.find_elements(By.TAG_NAME, "button") if b.text.strip().isdigit()]
                
                if txt and btns:
                    tareas.append({
                        "id": i, "texto": txt, 
                        "opciones": [b.text for b in btns], "elementos_btn": btns
                    })
                    print(f"      Idea {i+1}: '{txt[:30]}...'")
            except: pass

    elif tipo == "T7":
        # TIPO 7: Selección Múltiple (Cajas)
        cajas = driver.find_elements(*sel.SELECTOR_ANSWER_Q_CAJAS)
        for i, caja in enumerate(cajas):
            try:
                txt = caja.find_element(*sel.SELECTOR_ANSWER_Q_TEXTO).text.strip()
                btns = caja.find_elements(*sel.SELECTOR_ANSWER_Q_BOTONES)
                btns = [b for b in btns if b.text.strip()]
                
                if txt and btns:
                    tareas.append({
                        "id": i, "texto": txt, 
                        "opciones": [b.text for b in btns], "elementos_btn": btns
                    })
                    print(f"      Pregunta {i+1}: '{txt[:30]}...'")
            except: pass

    if not tareas:
        print("      ❌ No se encontraron preguntas legibles.")
        return None

    # --- CLAVE DE MEMORIA ---
    preguntas_str = "|".join([t['texto'] for t in tareas])
    clave_memoria = f"{tipo}:{preguntas_str}"

    # --- RESOLUCIÓN ---
    for tarea in tareas:
        pregunta = tarea['texto']
        opciones = tarea['opciones']
        # Clave específica por pregunta para la memoria
        clave_item = f"{tipo}:{pregunta}||OPTS:{'|'.join(opciones)}"
        
        # 1. Memoria
        respuesta = mem.buscar(clave_item)
        
        # 2. IA
        if not respuesta:
            print(f"      🧠 Consultando IA ({tipo})...")
            prompt = f"""
            Task: Select the correct option.
            Context: {contexto[:1000]}...
            Question/Idea: "{pregunta}"
            Options: {opciones}
            Reply ONLY with the exact text of the correct option.
            """
            respuesta = ia_utils.obtener_texto_de_respuesta(
                ia_utils.model.generate_content(prompt)
            )
            if respuesta:
                mem.registrar(clave_item, respuesta)
        else:
            if isinstance(respuesta, list): respuesta = respuesta[0]
            print(f"      💾 Memoria: {respuesta}")

        # 3. Click
        if respuesta:
            click_hecho = False
            resp_norm = str(respuesta).lower().strip()
            
            for btn in tarea['elementos_btn']:
                btn_txt = btn.text.lower().strip()
                # Comparación flexible
                if btn_txt == resp_norm or btn_txt in resp_norm or resp_norm in btn_txt:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"      ✅ Click: {btn.text}")
                        click_hecho = True
                        time.sleep(0.5)
                        break
                    except: pass
            
            if not click_hecho:
                print(f"      ⚠️ No encontré botón para: {respuesta}")

    # --- RETORNO PARA APRENDIZAJE ---
    return {
        "clave": clave_memoria, # (Nota: En aprendizaje T6/T7 se suele usar la lista de preguntas para re-extraer)
        "items": [t['texto'] for t in tareas] 
    }