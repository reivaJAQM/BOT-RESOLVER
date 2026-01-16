from selenium.webdriver.common.by import By
import time
import bot_memory as mem 

def resolver(driver, sel, ia_utils, contexto, wait):
    """
    Resuelve preguntas True/False (Tanto múltiples T3 como simples T5).
    Retorna datos para aprendizaje.
    """
    print("   🔍 [Solver TF] Analizando True/False...")
    
    # 1. Detectar cajas
    cajas = driver.find_elements(*sel.SELECTOR_CAJAS_TF)
    es_multi = True
    
    # Si no hay cajas múltiples, buscamos la estructura simple T5
    if not cajas:
        if len(driver.find_elements(*sel.SELECTOR_MARK_TF_TRUE)) > 0:
            es_multi = False
            # Simulamos una "caja" con el cuerpo de la pregunta para unificar lógica
            cajas = [driver.find_element(By.TAG_NAME, "body")] 
        else:
            print("      ❌ No se encontraron cajas T/F.")
            return None

    # --- RECOLECCIÓN DE DATOS ---
    tareas_tf = [] 
    
    for i, caja in enumerate(cajas):
        try:
            texto_afirmacion = ""
            
            if es_multi:
                # Lógica T3 (Múltiple)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", caja)
                try:
                    texto_afirmacion = caja.find_element(By.XPATH, ".//span[contains(@class, 'text-gray-700')]").text.strip()
                except: pass
            else:
                # Lógica T5 (Simple)
                # Intentamos leer el texto del span[1] de la tarjeta, o el título
                try:
                    card = driver.find_element(By.XPATH, "//div[contains(@class, 'card')]")
                    texto_afirmacion = card.find_element(By.XPATH, ".//span[1]").text.strip()
                except:
                    # Fallback al título principal si no hay texto en tarjeta
                    try: texto_afirmacion = driver.find_element(*sel.SELECTOR_PREGUNTA).text.strip()
                    except: pass

            if texto_afirmacion:
                # Limpieza básica
                texto_afirmacion = texto_afirmacion.replace("True", "").replace("False", "").strip()
                tareas_tf.append({"id": i, "texto": texto_afirmacion, "caja": caja})
                print(f"      Item {i+1}: '{texto_afirmacion[:40]}...'")
            else:
                print(f"      ⚠️ Item {i+1} sin texto legible.")

        except Exception as e:
            print(f"      Error leyendo item {i+1}: {e}")

    if not tareas_tf: return None

    # --- CLAVE DE MEMORIA ---
    # Creamos una clave única basada en todas las preguntas juntas
    textos_ordenados = "|".join(sorted([t['texto'] for t in tareas_tf]))
    clave_memoria = f"TF:{textos_ordenados}||CTX:{contexto[:30]}"

    # --- RESOLUCIÓN ---
    # 1. MEMORIA
    respuesta = mem.buscar(clave_memoria)
    
    # 2. IA
    if not respuesta:
        print(f"      🧠 Consultando IA...")
        if es_multi:
            # IA devuelve lista de respuestas ["True", "False", ...]
            lista_textos = [t['texto'] for t in tareas_tf]
            respuesta = ia_utils.obtener_true_false_lote(contexto, lista_textos)
        else:
            # IA devuelve string único "True" o "False"
            respuesta = ia_utils.obtener_true_false(contexto, tareas_tf[0]['texto'])
        
        if respuesta:
            mem.registrar(clave_memoria, respuesta)
    else:
        print(f"      💾 Memoria: {respuesta}")

    # 3. EJECUTAR CLICS
    if respuesta:
        # Unificamos formato: siempre lista para iterar fácil
        respuestas_lista = respuesta if isinstance(respuesta, list) else [respuesta]
        
        # Validación de seguridad
        if len(respuestas_lista) != len(tareas_tf):
            print("      ⚠️ Discrepancia cantidad respuestas/preguntas. Intentando asignar en orden.")
        
        for i, tarea in enumerate(tareas_tf):
            if i < len(respuestas_lista):
                resp_actual = str(respuestas_lista[i])
                es_true = "true" in resp_actual.lower()
                target_str = "True" if es_true else "False" # Selector busca Case Sensitive a veces
                
                try:
                    # Buscamos el botón dentro de la caja (o global si es T5)
                    scope = tarea['caja'] if es_multi else driver
                    
                    # Selectores específicos según tipo
                    if es_multi:
                        xpath = f".//button[contains(normalize-space(), '{target_str}') or contains(normalize-space(), '{target_str.upper()}')]"
                    else:
                        xpath = f"//button[normalize-space()='{target_str}']"

                    btn = scope.find_element(By.XPATH, xpath)
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"      ✅ Click: {target_str}")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"      ❌ Error clickeando {target_str}: {e}")

    # --- RETORNO PARA APRENDIZAJE ---
    return {
        "clave": clave_memoria,
        "items": [t['texto'] for t in tareas_tf],
        "es_multi": es_multi
    }