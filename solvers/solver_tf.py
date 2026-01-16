from selenium.webdriver.common.by import By
import time
import bot_memory as mem # Usamos tu módulo de memoria

def resolver(driver, sel, ia_utils, contexto, wait):
    """
    Resuelve preguntas True/False (Tanto múltiples T3 como simples T5).
    """
    print("   🔍 [Solver TF] Analizando True/False...")
    
    # 1. Detectar cajas
    cajas = driver.find_elements(*sel.SELECTOR_CAJAS_TF)
    if not cajas:
        print("      ❌ No se encontraron cajas T/F.")
        return

    # --- RECOLECCIÓN DE DATOS ---
    tareas_tf = [] 
    
    for i, caja in enumerate(cajas):
        try:
            # Scroll para asegurar visibilidad
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", caja)
            
            # Intentar leer el texto (varios intentos)
            texto_afirmacion = ""
            
            # A. Span gris estándar
            try:
                texto_afirmacion = caja.find_element(By.XPATH, ".//span[contains(@class, 'text-gray-700')]").text.strip()
            except: pass
            
            # B. Párrafo
            if not texto_afirmacion:
                try:
                    texto_afirmacion = caja.find_element(By.TAG_NAME, "p").text.strip()
                except: pass

            # C. Fallback: Título de la página (si es T5 single)
            if not texto_afirmacion and len(cajas) == 1:
                try:
                    titulo = driver.find_element(*sel.SELECTOR_PREGUNTA).text.strip()
                    texto_afirmacion = titulo.replace("TRUE OR FALSE", "").strip()
                except: pass

            if texto_afirmacion:
                tareas_tf.append({"id": i, "texto": texto_afirmacion, "caja": caja})
                print(f"      Caja {i+1}: '{texto_afirmacion[:40]}...'")
            else:
                print(f"      ⚠️ Caja {i+1} sin texto legible.")

        except Exception as e:
            print(f"      Error leyendo caja {i+1}: {e}")

    # --- RESOLUCIÓN ---
    for tarea in tareas_tf:
        pregunta_txt = tarea['texto']
        clave_memoria = f"TF:{pregunta_txt}||CTX:{contexto[:50]}"
        
        # 1. MEMORIA
        respuesta = mem.buscar(clave_memoria)
        
        # 2. IA (Si no hay memoria)
        if not respuesta:
            print(f"      🧠 Consultando IA...")
            respuesta = ia_utils.obtener_true_false(contexto, pregunta_txt)
            if respuesta:
                mem.registrar(clave_memoria, respuesta)
        else:
            if isinstance(respuesta, list): respuesta = respuesta[0]
            print(f"      💾 Memoria: {respuesta}")

        # 3. CLICK
        if respuesta:
            es_true = "true" in str(respuesta).lower()
            target_str = "TRUE" if es_true else "FALSE"
            
            try:
                # Buscar botón TRUE o FALSE (insensible a mayúsculas)
                xpath_btn = f".//button[contains(translate(normalize-space(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{target_str}')]"
                btn = tarea['caja'].find_element(By.XPATH, xpath_btn)
                
                driver.execute_script("arguments[0].click();", btn)
                print(f"      ✅ Click: {target_str}")
                time.sleep(0.3)
            except Exception as e:
                print(f"      ❌ Error clickeando {target_str}: {e}")