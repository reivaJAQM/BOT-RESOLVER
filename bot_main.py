# bot_main.py
# Script principal que orquesta el bot.
# ¡Refactorizado con "Plan Maestro" y "Plan S"!
# Doble chequeo de indentación TIPO 3 vs CHECK.
# --- ¡ACTUALIZADO CON TIPO 8 (EMPAREJAR IMAGEN)! ---

import time
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, JavascriptException
from selenium.webdriver.common.action_chains import ActionChains

# --- ¡NUESTROS MÓDULOS! ---
import config
import bot_selectors as sel
import ia_utils
# -----------------------------

# Configuración Selenium
print("Iniciando Navegador...");
try:
    service = EdgeService(executable_path=config.DRIVER_PATH)
    driver = webdriver.Edge(service=service)
    
    # --- ¡MEJORA: MAXIMIZAR VENTANA! ---
    print("Maximizando ventana...")
    driver.maximize_window()
    # --- FIN DE LA MEJORA ---

    wait_short = WebDriverWait(driver, 5)
    wait_long = WebDriverWait(driver, 15)
    wait_extra_long = WebDriverWait(driver, 25)
    print("Navegador Listo!")
except Exception as e:
    print(f"Error iniciando navegador: {e}"); exit()

# --- INICIO DE LA MEMORIA DEL BOT ---
preguntas_ya_vistas = {}
opciones_ya_vistas = {}
soluciones_correctas = {} # --- MEMORIA PARA RESPUESTAS APRENDIDAS ---
MEMORIA_FILE = "memoria_bot.json"

# --- ¡NUEVA LÓGICA DE PERSISTENCIA! ---
try:
    # Use 4 spaces for indentation
    with open(MEMORIA_FILE, 'r', encoding='utf-8') as f:
        soluciones_correctas = json.load(f)
    print(f"¡Memoria cargada! {len(soluciones_correctas)} soluciones conocidas.")
except FileNotFoundError:
    print("No se encontró memoria previa (memoria_bot.json). Empezando de cero.")
except json.JSONDecodeError:
    print("Error al leer la memoria. Empezando de cero.")

def guardar_memoria_en_disco():
    """Guarda el diccionario 'soluciones_correctas' en el archivo JSON."""
    try:
        # Use 4 spaces for indentation
        with open(MEMORIA_FILE, 'w', encoding='utf-8') as f:
            json.dump(soluciones_correctas, f, indent=4, ensure_ascii=False)
        print("      ¡Memoria actualizada en disco!")
    except Exception as e:
        print(f"      ERROR CRÍTICO al guardar memoria: {e}")
# --- FIN DE LA MEMORIA DEL BOT ---


if ia_utils.model is None:
    print("ERROR FATAL: El modelo de IA no se pudo inicializar.")
    driver.quit()
    exit()

# --- INICIO DEL SCRIPT ---
try:
    # Use 4 spaces for indentation
    print(f"Navegando: {config.URL_INICIAL}"); driver.get(config.URL_INICIAL)

    # --- LOGIN ---
    try:
        # Use 4 spaces for indentation
        print("P1: Pop-up..."); wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_CERRAR_POPUP)).click(); time.sleep(1)
    except TimeoutException:
        print("No pop-up.")
    print("P2: Inicia Sesión..."); wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_INICIA_SESION_VERDE)).click()
    print("P3: Login...");
    wait_long.until(EC.visibility_of_element_located(sel.SELECTOR_USUARIO_INPUT)).send_keys(config.TU_USUARIO_EMAIL);
    wait_long.until(EC.visibility_of_element_located(sel.SELECTOR_PASSWORD_INPUT)).send_keys(config.TU_CONTRASENA)
    print("P4: Enviar..."); wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_ACCEDER_AMARILLO)).click()

    print("Login OK! Navegando..."); time.sleep(2);

    # --- BUCLE DE LECCIONES (EXTERNO) ---
    print("\n" + "#"*40)
    print("Iniciando BUCLE DE LECCIONES...")
    while True:
        # Use 4 spaces for indentation

        # --- 1. ENCONTRAR Y EMPEZAR LA SIGUIENTE LECCIÓN ---
        try:
            # Use 8 spaces for indentation
            print("Buscando la siguiente lección disponible...")
            # --- ¡MODIFICADO! (Reading, Grammar y Listening/Teacher) ---
            # (Asegúrate que sel.SELECTOR_LECCION_DISPONIBLE esté actualizado en bot_selectors.py)
            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"); time.sleep(0.5)

            leccion = wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_LECCION_DISPONIBLE))
            # --- FIN MODIFICADO ---
            print("      Lección encontrada. Haciendo scroll...")
            driver.execute_script("arguments[0].scrollIntoView(true);", leccion); time.sleep(0.5)
            leccion.click()

            print("      Clic en 'Start'...")
            wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_BOTON_START)).click()
            print("Empezando nuevo test...")
        except TimeoutException:
            print("\n" + "#"*40); print("¡NO SE ENCONTRARON MÁS LECCIONES DISPONIBLES!"); print("¡Bot ha completado todo el trabajo! Terminando..."); break
        except Exception as e:
            print(f"Error al intentar empezar la siguiente lección: {e}"); break

        # --- BUCLE DE PREGUNTAS (INTERNO) ---
        pregunta_actual_texto = ""
        # --- ¡MODIFICADO! (Variables de bucle para lotes) ---
        tipo_pregunta = ""; clave_pregunta = None; lista_ideas_texto = []; lista_de_preguntas = []; lista_afirmaciones_texto = []; frases_des = []; lista_de_claves_individuales = []; lista_de_tareas_ordenar = []
        # --- ¡NUEVO TIPO 8! (Variables para TIPO 4 y 8) ---
        palabras_clave = []; definiciones = [] 

        while True:
            # Use 8 spaces for indentation
            print("\n" + "="*30)
            try:
                # Use 12 spaces for indentation
                # --- DETECCIÓN FIN ---
                print("Verificando fin...")
                try:
                    # Use 16 spaces for indentation
                    boton_continue = wait_short.until(EC.element_to_be_clickable(sel.SELECTOR_CONTINUE))
                    print("FIN DE LA LECCIÓN! Clic CONTINUE..."); boton_continue.click()
                    print("Esperando regreso a la página de lecciones...");
                    # --- ¡MODIFICADO! (Reading y Grammar) ---
                    wait_long.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
                    print("Página de lecciones cargada. Buscando siguiente lección..."); time.sleep(2); break
                except TimeoutException:
                    print("Test continúa...")

                # --- LÓGICA DE ESPERA (PLAN MAESTRO) ---
                print("Esperando nueva pregunta..."); current_url = driver.current_url
                try:
                    # Use 16 spaces for indentation
                    wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK)); print("      Botón 'CHECK' detectado. Página cargada.")
                except TimeoutException:
                    print("Error: El botón 'CHECK' no cargó. Página atascada."); raise

                time.sleep(1)
                print("Detectando tipo de pregunta por contenido...")

                # El ORDEN es crucial (del más específico al más genérico)
                if len(driver.find_elements(*sel.SELECTOR_ANSWER_Q_CAJAS)) > 0: print("      Contenido detectado: [TIPO 7]"); tipo_pregunta = "TIPO_7_OM_CARD"
                elif len(driver.find_elements(*sel.SELECTOR_PARAGRAPH_CAJAS)) > 0: print("      Contenido detectado: [TIPO 6]"); tipo_pregunta = "TIPO_6_PARAGRAPH"
                # --- ORDEN INVERTIDO ---
                elif len(driver.find_elements(*sel.SELECTOR_CAJAS_TF)) > 0: print("      Contenido detectado: [TIPO 3]"); tipo_pregunta = "TIPO_3_TF_MULTI" # <<< AHORA PRIMERO
                elif len(driver.find_elements(*sel.SELECTOR_MARK_TF_TRUE)) > 0: print("      Contenido detectado: [TIPO 5]"); tipo_pregunta = "TIPO_5_TF_SINGLE" # <<< AHORA DESPUÉS
                # --- FIN ORDEN INVERTIDO ---
                elif len(driver.find_elements(*sel.SELECTOR_LINEAS_COMPLETAR)) > 0: print("      Contenido detectado: [TIPO 2]"); tipo_pregunta = "TIPO_2_COMPLETAR"
                elif len(driver.find_elements(*sel.SELECTOR_CONTENEDOR_ORDENAR)) > 0: print("      Contenido detectado: [TIPO 1]"); tipo_pregunta = "TIPO_1_ORDENAR"
                
                # --- ¡INICIO DE LA MODIFICACIÓN TIPO 8! (Debe ir ANTES de TIPO 4) ---
                elif len(driver.find_elements(*sel.SELECTOR_IMAGEN_EMPAREJAR)) > 0: print("      Contenido detectado: [TIPO 8]"); tipo_pregunta = "TIPO_8_IMAGEN"
                # --- FIN DE LA MODIFICACIÓN TIPO 8 ---

                elif len(driver.find_elements(*sel.SELECTOR_FILAS_EMPAREJAR)) > 0: print("      Contenido detectado: [TIPO 4]"); tipo_pregunta = "TIPO_4_EMPAREJAR"
                elif len(driver.find_elements(*sel.SELECTOR_AUDIO)) > 0: print("      Contenido detectado: [TIPO 9]"); tipo_pregunta = "TIPO_9_AUDIO"
                else: print("      No se detectó contenido especial. Se asume [DEFAULT]"); tipo_pregunta = "TIPO_DEFAULT_OM"

                print("Leyendo datos (Contexto y Título)...")
                try: contexto = wait_short.until(EC.visibility_of_element_located(sel.SELECTOR_CONTEXTO)).text
                except TimeoutException: print("Warn: No contexto."); contexto = ""
                try:
                    # Use 16 spaces for indentation
                    pregunta_elemento = wait_short.until(EC.presence_of_element_located(sel.SELECTOR_PREGUNTA)); pregunta = pregunta_elemento.text.strip()
                    WebDriverWait(driver, 3).until(lambda d: d.find_element(*sel.SELECTOR_PREGUNTA).text.strip() != pregunta_actual_texto)
                    pregunta_actual_texto = pregunta; print(f"      Título detectado: '{pregunta}'")
                except TimeoutException:
                    print("Warn: No se encontró/actualizó el título."); pregunta = f"pregunta_sin_titulo_{contexto[:50]}"; pregunta_actual_texto = pregunta

                # --- TIPO 1: ORDENAR (REFACTORIZADO PARA MÚLTIPLES PREGUNTAS) ---
                if tipo_pregunta == "TIPO_1_ORDENAR": # Use if here, not elif
                    # Use 16 spaces for indentation
                    print("Tipo: ORDENAR (Múltiple).")
                    # 1. Encontrar TODOS los contenedores de preguntas
                    contenedores = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_CONTENEDOR_ORDENAR))
                    if not contenedores: raise Exception("No se encontraron contenedores TIPO 1.")
                    print(f"Encontrados {len(contenedores)} contenedores para ordenar.")

                    lista_de_claves_individuales = [] # Para la clave de lote
                    lista_de_tareas_ordenar = [] # Para guardar los datos de cada tarea
                    
                    # 2. Recolectar datos de CADA contenedor
                    for k, contenedor in enumerate(contenedores):
                        # Use 20 spaces for indentation
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", contenedor); time.sleep(0.1)
                        cajas_inicial = contenedor.find_elements(*sel.SELECTOR_CAJAS_ORDENAR)
                        frases_des_individual = []
                        map_id_a_texto_individual = {}
                        ids_individual = []

                        for i, c in enumerate(cajas_inicial):
                            # Use 24 spaces for indentation
                            try:
                                # Use 28 spaces for indentation
                                text_element = c.find_element(*sel.SELECTOR_TEXTO_CAJA_ORDENAR)
                                t = text_element.text.strip()
                                d_id = c.get_attribute("data-rbd-draggable-id")
                                if t and d_id:
                                    frases_des_individual.append(t)
                                    ids_individual.append(d_id)
                                    map_id_a_texto_individual[d_id] = t
                            except NoSuchElementException: continue
                        
                        if not frases_des_individual:
                            print(f"Warn: Contenedor {k+1} sin frases. Omitiendo.")
                            continue

                        print(f"      Tarea {k+1} Frases: {frases_des_individual}")
                        clave_ind = "|".join(frases_des_individual)
                        lista_de_claves_individuales.append(f"{k}:{clave_ind}") # Clave única con índice
                        lista_de_tareas_ordenar.append({
                            "frases": frases_des_individual,
                            "map_id_a_texto": map_id_a_texto_individual,
                            "contenedor_elem": contenedor
                        })
                        
                    if not lista_de_tareas_ordenar: raise Exception("No se recolectaron tareas TIPO 1 válidas.")

                    # 3. Consultar memoria de lote
                    clave_pregunta = "|".join(lista_de_claves_individuales) # Clave de lote
                    lista_ordenes_ia = [] # Aquí irán las listas ordenadas para cada tarea
                    
                    if clave_pregunta in soluciones_correctas:
                        print("      SOLUCIÓN LOTE TIPO 1 ENCONTRADA en memoria.");
                        lista_ordenes_ia = soluciones_correctas[clave_pregunta]
                    else:
                        print("      Llamando a IA individualmente para TIPO 1 (se guardará en lote)...")
                        exito_ia_individual = True
                        for i, tarea in enumerate(lista_de_tareas_ordenar):
                            # Use 24 spaces for indentation
                            print(f"      IA (Ord) para Tarea {i+1}...")
                            orden_ia_individual = ia_utils.obtener_orden_correcto(contexto, tarea["frases"])
                            if not orden_ia_individual:
                                print(f"Error IA (Ord) Tarea {i+1}."); exito_ia_individual = False; break
                            lista_ordenes_ia.append(orden_ia_individual)
                        
                        if not exito_ia_individual: raise Exception("Fallo IA al obtener orden TIPO 1 individual.")
                        preguntas_ya_vistas[clave_pregunta] = lista_ordenes_ia # Guardar en memoria de aciertos

                    print(f"Órdenes a aplicar (lote): {lista_ordenes_ia}")

                    # 4. Aplicar TODAS las soluciones
                    if len(lista_ordenes_ia) != len(lista_de_tareas_ordenar):
                        raise Exception("Fallo crítico: El número de soluciones no coincide con el de tareas TIPO 1.")

                    print("Reordenando JS (Lote)...")
                    exito_global = True
                    js = "var c=arguments[0],ids=arguments[1],m={};for(let i=0;i<c.children.length;i++){let o=c.children[i],d=o.firstElementChild;if(d&&d.getAttribute('data-rbd-draggable-id')){m[d.getAttribute('data-rbd-draggable-id')]=o;}}while(c.firstChild)c.removeChild(c.firstChild);ids.forEach(id=>{if(m[id])c.appendChild(m[id]);else console.error('JS Err ID:',id);});console.log('JS OK.');"

                    for orden_ia, tarea in zip(lista_ordenes_ia, lista_de_tareas_ordenar):
                        # Use 20 spaces for indentation
                        map_texto_a_id = {v: k for k, v in tarea["map_id_a_texto"].items()}
                        ids_ok = [map_texto_a_id.get(t) for t in orden_ia if map_texto_a_id.get(t)]

                        if len(ids_ok) != len(tarea["frases"]):
                            print(f"Error: Fallo mapeo IDs JS para tarea {tarea['frases']}"); exito_global = False; continue
                        
                        try:
                            # Use 24 spaces for indentation
                            driver.execute_script(js, tarea["contenedor_elem"], ids_ok); time.sleep(0.5)
                        except JavascriptException as e:
                            print(f"Error JS en TIPO 1 Lote: {e}"); exito_global = False; continue
                    
                    print("JS OK (Lote).")
                    if not exito_global: raise Exception("Fallo JS durante reordenamiento TIPO 1 Lote.")

                #--- TIPO 2: COMPLETAR PALABRAS ---
                elif tipo_pregunta == "TIPO_2_COMPLETAR":
                    # Use 16 spaces for indentation
                    print("Tipo: COMPLETAR PALABRAS.");
                    lineas = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_LINEAS_COMPLETAR))
                    if not lineas: raise Exception("No se encontraron líneas.")
                    print(f"Encontradas {len(lineas)} líneas.")
                    exito_global = True
                    for i, linea in enumerate(lineas):
                        # Use 20 spaces for indentation
                        print(f"\nProcesando línea {i+1}...")
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", linea); time.sleep(0.3)
                        spans = linea.find_elements(By.XPATH, "./div/span[@class='inline-block']")
                        grupo_actual_botones = []; indice_grupo = 0; span_indices_grupo = []
                        for j, span in enumerate(spans):
                            # Use 24 spaces for indentation
                            botones_en_span = span.find_elements(*sel.SELECTOR_BOTONES_OPCION_COMPLETAR)
                            if botones_en_span: grupo_actual_botones.extend(botones_en_span); span_indices_grupo.append(j)
                            if (not botones_en_span and grupo_actual_botones) or (j == len(spans) - 1 and grupo_actual_botones):
                                # Use 28 spaces for indentation
                                indice_grupo += 1
                                opciones_palabra = [b.text.strip() for b in grupo_actual_botones if b.text.strip()]
                                if not opciones_palabra: print(f"Warn: Grupo {indice_grupo} vacío."); grupo_actual_botones = []; span_indices_grupo = []; continue
                                frase_para_ia = ""; placeholder_colocado = False
                                for idx_s, s_temp in enumerate(spans):
                                    # Use 32 spaces for indentation
                                    if not s_temp.find_elements(*sel.SELECTOR_BOTONES_OPCION_COMPLETAR): frase_para_ia += s_temp.text.strip() + " "
                                    elif idx_s in span_indices_grupo and not placeholder_colocado: frase_para_ia += "___ "; placeholder_colocado = True
                                frase_para_ia = ' '.join(frase_para_ia.split())
                                print(f"      Espacio {indice_grupo}. Frase: '{frase_para_ia}'. Opciones: {opciones_palabra}"); clave_pregunta = frase_para_ia; opciones_ya_vistas[clave_pregunta] = opciones_palabra
                                if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA en memoria."); palabra_correcta_ia = soluciones_correctas[clave_pregunta]
                                else:
                                    opciones_para_ia = list(opciones_palabra)
                                    if clave_pregunta in preguntas_ya_vistas:
                                        respuesta_anterior = preguntas_ya_vistas[clave_pregunta]; print(f"      WARN: Pregunta (Completar) repetida. Anterior: '{respuesta_anterior}'.")
                                        if respuesta_anterior in opciones_para_ia: opciones_para_ia.remove(respuesta_anterior); print(f"      Reintentando con: {opciones_para_ia}")
                                        if not opciones_para_ia: opciones_para_ia = list(opciones_palabra)
                                    palabra_correcta_ia = ia_utils.obtener_palabra_correcta(contexto, frase_para_ia, opciones_para_ia)
                                    if palabra_correcta_ia: preguntas_ya_vistas[clave_pregunta] = palabra_correcta_ia
                                if not palabra_correcta_ia: print(f"Error IA espacio {indice_grupo}."); exito_global = False; grupo_actual_botones = []; span_indices_grupo = []; continue
                                print(f"      IA eligió: '{palabra_correcta_ia}'"); boton_clic = None
                                for b in grupo_actual_botones:
                                    # Use 32 spaces for indentation
                                    if b.text.strip() == palabra_correcta_ia: boton_clic = b; break
                                if boton_clic:
                                    try: print(f"      Clic en '{palabra_correcta_ia}'..."); driver.execute_script("arguments[0].click();", boton_clic); time.sleep(0.4)
                                    except Exception as e: print(f"Error clic: {e}"); exito_global = False
                                else: print(f"Error CRÍTICO: Botón '{palabra_correcta_ia}' no encontrado."); exito_global = False
                                grupo_actual_botones = []; span_indices_grupo = []
                    if not exito_global: raise Exception("Fallo al completar palabras.")

                # --- TIPO 3: TRUE/FALSE MÚLTIPLE [CORREGIDO] ---
                elif tipo_pregunta == "TIPO_3_TF_MULTI":
                    # Use 16 spaces for indentation
                    print("Tipo: TRUE/FALSE MÚLTIPLE.")
                    cajas_afirmacion = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_CAJAS_TF))
                    if not cajas_afirmacion: raise Exception("No se encontraron cajas True/False.")
                    print(f"Encontradas {len(cajas_afirmacion)} afirmaciones.")

                    lista_afirmaciones_texto = [] # Reiniciar para esta pregunta
                    elementos_cajas_botones = []

                    print("Recolectando afirmaciones...")
                    for k, caja in enumerate(cajas_afirmacion):
                        # Use 20 spaces for indentation
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            # Use 24 spaces for indentation
                            texto_afirmacion_elem = caja.find_element(*sel.SELECTOR_TEXTO_AFIRMACION_TF)
                            wait_short.until(EC.visibility_of(texto_afirmacion_elem))
                            texto_afirmacion = texto_afirmacion_elem.text.strip()
                            boton_true = caja.find_element(*sel.SELECTOR_BOTON_TRUE_TF)
                            boton_false = caja.find_element(*sel.SELECTOR_BOTON_FALSE_TF)
                            if texto_afirmacion:
                                clave_unica_afirmacion = f"{k}:{texto_afirmacion}" # <-- ¡CLAVE ÚNICA!
                                lista_afirmaciones_texto.append(clave_unica_afirmacion) # <-- ¡CAMBIADO!
                                elementos_cajas_botones.append((caja, boton_true, boton_false))
                            else: print(f"Warn: Caja {k+1} sin texto.")
                        except (NoSuchElementException, TimeoutException) as e_inner:
                            print(f"Error leyendo caja {k+1}: {e_inner}"); raise Exception(f"Fallo crítico al leer caja T/F {k+1}")

                    if not lista_afirmaciones_texto: raise Exception("No se pudieron recolectar afirmaciones T/F.")

                    clave_pregunta = "|".join(lista_afirmaciones_texto) # Clave única
                    respuestas_tf_lote = []

                    if clave_pregunta in soluciones_correctas:
                        print("      SOLUCIÓN LOTE T/F ENCONTRADA en memoria."); respuestas_tf_lote = soluciones_correctas[clave_pregunta]
                    else:
                        print("      Llamando a IA individualmente (con memoria de intento)...")
                        respuestas_tf_lote_temporal = []
                        exito_ia_individual = True
                        for texto_afirmacion_con_indice in lista_afirmaciones_texto:
                            # Use 24 spaces for indentation
                            # texto_afirmacion_con_indice es "0:La casa es roja"
                            texto_afirmacion_real = texto_afirmacion_con_indice.split(":", 1)[1]
                            clave_individual = texto_afirmacion_con_indice # Usamos la clave única "0:La casa es roja"
                            opciones_ya_vistas[clave_individual]=["True","False"]
                            respuesta_tf_ia = None
                            if clave_individual in preguntas_ya_vistas:
                                respuesta_anterior = preguntas_ya_vistas[clave_individual]; respuesta_tf_ia = "False" if respuesta_anterior == "True" else "True"
                                print(f"      WARN: Afirmación '{texto_afirmacion_real[:30]}...' repetida. Forzando: '{respuesta_tf_ia}'")
                            else:
                                print(f"      IA (T/F) para '{texto_afirmacion_real[:30]}...'?"); respuesta_tf_ia = ia_utils.obtener_true_false(contexto, texto_afirmacion_real)
                            if respuesta_tf_ia:
                                preguntas_ya_vistas[clave_individual] = respuesta_tf_ia; respuestas_tf_lote_temporal.append(respuesta_tf_ia)
                            else: print(f"Error IA T/F para afirmación: {texto_afirmacion_real}"); exito_ia_individual = False; break
                        if not exito_ia_individual: raise Exception("Fallo IA al obtener respuesta T/F individual.")
                        respuestas_tf_lote = respuestas_tf_lote_temporal
                        preguntas_ya_vistas[clave_pregunta] = respuestas_tf_lote

                    print(f"Respuestas T/F a usar: {respuestas_tf_lote}")

                    exito_global = True
                    for i, (respuesta_tf_ia, (caja, boton_true, boton_false)) in enumerate(zip(respuestas_tf_lote, elementos_cajas_botones)):
                        # Use 20 spaces for indentation
                        try:
                            # Use 24 spaces for indentation
                            boton_a_clicar = boton_true if respuesta_tf_ia == "True" else boton_false
                            print(f"      Clic en '{respuesta_tf_ia}' para afirmación {i+1}...")
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                            wait_short.until(EC.element_to_be_clickable(boton_a_clicar))
                            driver.execute_script("arguments[0].click();", boton_a_clicar); time.sleep(0.3)
                        except Exception as e_inner:
                            print(f"Error en clic T/F iteración {i+1}: {e_inner}"); exito_global = False; break
                    if not exito_global: raise Exception("Fallo durante los clics de T/F Múltiple.")

                # --- TIPO 6: MATCH IDEA TO PARAGRAPH ---
                elif tipo_pregunta == "TIPO_6_PARAGRAPH":
                    # Use 16 spaces for indentation
                    print("Tipo: MATCH IDEA TO PARAGRAPH.");
                    cajas_ideas = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_PARAGRAPH_CAJAS))
                    if not cajas_ideas: raise Exception("No cajas ideas.")
                    print(f"Encontradas {len(cajas_ideas)} ideas."); lista_ideas_texto = []; elementos_cajas = []
                    print("Recolectando ideas...");
                    for k, caja in enumerate(cajas_ideas):
                        # Use 20 spaces for indentation
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            # Use 24 spaces for indentation
                            idea_elem = caja.find_element(*sel.SELECTOR_PARAGRAPH_IDEA_TEXT); idea_texto = idea_elem.text.strip()
                            if idea_texto: 
                                clave_unica_idea = f"{k}:{idea_texto}" # <-- ¡CLAVE ÚNICA!
                                lista_ideas_texto.append(clave_unica_idea); # <-- ¡CAMBIADO!
                                elementos_cajas.append(caja); 
                                print(f"      Idea {k+1}: '{idea_texto}'")
                            else: print(f"Warn: Caja {k+1} sin texto.")
                        except (NoSuchElementException, TimeoutException) as e: print(f"Error leyendo idea {k+1}: {e}"); continue
                    if not lista_ideas_texto: raise Exception("No ideas recolectadas.")
                    clave_pregunta = "|".join(lista_ideas_texto)
                    if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA."); respuestas_lote_ia = soluciones_correctas[clave_pregunta]
                    else:
                        respuesta_anterior_incorrecta = None
                        if clave_pregunta in preguntas_ya_vistas: respuesta_anterior_incorrecta = preguntas_ya_vistas[clave_pregunta]; print(f"      WARN: Pregunta repetida. Anterior: {respuesta_anterior_incorrecta}.")
                        
                        # Extraer solo el texto para la IA
                        ideas_para_ia = [idea.split(":", 1)[1] for idea in lista_ideas_texto]
                        print(f"Enviando {len(ideas_para_ia)} ideas a IA..."); 
                        respuestas_lote_ia = ia_utils.obtener_numeros_parrafo_lote(contexto, ideas_para_ia, respuesta_anterior_incorrecta)
                        
                        if not respuestas_lote_ia or len(respuestas_lote_ia) != len(elementos_cajas): raise Exception("Fallo IA (Parag Lote) o nº resp no coincide.")
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia
                    print(f"Respuestas a usar: {respuestas_lote_ia}"); print("Haciendo clics...")
                    exito_global = True
                    for numero_parrafo_ia, caja in zip(respuestas_lote_ia, elementos_cajas):
                        # Use 20 spaces for indentation
                        try:
                            # Use 24 spaces for indentation
                            selector_boton_num = (By.XPATH, f".//button[normalize-space()='{numero_parrafo_ia}']"); boton_a_clicar = caja.find_element(*selector_boton_num)
                            print(f"      Clic en '{numero_parrafo_ia}'..."); wait_long.until(EC.element_to_be_clickable(boton_a_clicar)); driver.execute_script("arguments[0].click();", boton_a_clicar); time.sleep(0.3)
                        except Exception as e: print(f"Error clic Parágrafo '{numero_parrafo_ia}': {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo al resolver Match Paragraph.")

                # --- TIPO 4: EMPAREJAR ---
                elif tipo_pregunta == "TIPO_4_EMPAREJAR":
                    # Use 16 spaces for indentation
                    print("Tipo: EMPAREJAR PALABRAS.");
                    exito_global = True; print("      Extrayendo definiciones (JS)...")
                    js_get_defs = f"return Array.from(document.querySelectorAll('{sel.SELECTOR_DEFINICIONES_AZULES_CSS}')).map(el => el.innerText.trim());"
                    try:
                        # Use 20 spaces for indentation
                        definiciones = driver.execute_script(js_get_defs); definiciones = [d for d in definiciones if d]
                        if not definiciones: raise Exception("JS no encontró texto def.")
                        map_texto_def_a_elemento = {}
                        spans_defs_selenium = wait_long.until(EC.presence_of_all_elements_located((sel.SELECTOR_DEFINICIONES_AZULES_XPATH)))
                        for s in spans_defs_selenium:
                            # Use 24 spaces for indentation
                            texto = s.text.strip();
                            if texto in definiciones: map_texto_def_a_elemento[texto] = s
                        if len(map_texto_def_a_elemento) != len(definiciones): print("Warn: No se mapearon elementos def.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo def: {e}")
                    print(f"      Definiciones encontradas: {definiciones}"); print("      Extrayendo palabras clave (en orden)...")
                    js_get_keywords = f"let k=[];document.querySelectorAll('{sel.SELECTOR_FILAS_EMPAREJAR_CSS}').forEach(r=>{{let e=r.querySelector('{sel.SELECTOR_PALABRA_CLAVE_CSS}');if(e)k.push(e.innerText.replace(/_/g,'').replace(/:/g,'').trim());}});return k;"
                    try:
                        # Use 20 spaces for indentation
                        palabras_clave = driver.execute_script(js_get_keywords); palabras_clave = [p for p in palabras_clave if p]
                        if not palabras_clave: raise Exception("JS no encontró palabras clave.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo palabras: {e}")
                    print(f"      Palabras clave encontradas (en orden): {palabras_clave}"); 
                    
                    # --- ¡INICIO MODIFICACIÓN CLAVE DE MEMORIA TIPO 4! ---
                    # Usamos el Título de la pregunta y las definiciones como clave estable.
                    clave_pregunta = f"T4:{pregunta_actual_texto}||" + "|".join(sorted(definiciones))
                    
                    if clave_pregunta in soluciones_correctas:
                        # Use 20 spaces for indentation
                        print("      SOLUCIÓN ENCONTRADA en memoria.");
                        # La solución guardada es una LISTA de definiciones en el orden correcto
                        lista_definiciones_ordenadas = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 20 spaces for indentation
                        print("      IA (Emparejar)...")
                        # Pedimos a la IA el diccionario (como antes)
                        pares_ia_temporal = ia_utils.obtener_emparejamientos(palabras_clave, definiciones)
                        if not pares_ia_temporal: raise Exception("IA (Emparejar) falló.")
                        
                        # Convertimos el dict a una lista ordenada para el 'preguntas_ya_vistas'
                        lista_definiciones_ordenadas = []
                        for clave in palabras_clave: # Iteramos en el orden de las claves (top-to-bottom)
                            lista_definiciones_ordenadas.append(pares_ia_temporal[clave])
                        
                         # Guardamos en 'memoria de intentos' para aprender si es 'GREAT'
                        preguntas_ya_vistas[clave_pregunta] = lista_definiciones_ordenadas
                    # --- FIN LÓGICA MEMORIA MODIFICADA ---

                    print(f"      Solución a aplicar (en orden): {lista_definiciones_ordenadas}"); print("      Clickeando en orden (Sistema de Cola)...")
                    
                    # --- Lógica de Clics (MODIFICADA) ---
                    for definicion_correcta in lista_definiciones_ordenadas:
                        # Use 20 spaces for indentation
                        elemento_origen = map_texto_def_a_elemento.get(definicion_correcta)
                        if not elemento_origen: print(f"Error: No WebElement para def '{definicion_correcta}'"); exito_global = False; continue
                        print(f"            Clic en '{definicion_correcta}'...");
                        try:
                            # Use 24 spaces for indentation
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", elemento_origen); time.sleep(0.3)
                            wait_long.until(EC.element_to_be_clickable(elemento_origen)).click(); print("                  Clic OK."); time.sleep(1.0)
                        except Exception as e: print(f"                  Error CRÍTICO (Click) en '{definicion_correcta}': {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo emparejar (Clic en orden).")

                # --- TIPO 5: MARK TRUE/FALSE (SINGLE) ---
                elif tipo_pregunta == "TIPO_5_TF_SINGLE":
                    # Use 16 spaces for indentation
                    print("Tipo: MARK TRUE/FALSE (Single).");
                    try:
                        # Use 20 spaces for indentation
                        texto_afirmacion_elem = wait_long.until(EC.visibility_of_element_located(sel.SELECTOR_MARK_TF_TEXT)); texto_afirmacion = texto_afirmacion_elem.text.strip()
                        boton_true = wait_long.until(EC.presence_of_element_located(sel.SELECTOR_MARK_TF_TRUE)); boton_false = wait_long.until(EC.presence_of_element_located(sel.SELECTOR_MARK_TF_FALSE))
                        if not texto_afirmacion: raise Exception("No texto afirmación.")
                        print(f"      Afirmación: '{texto_afirmacion}'"); clave_pregunta = texto_afirmacion; opciones_ya_vistas[clave_pregunta] = ["True", "False"]
                        if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA."); respuesta_tf_ia = soluciones_correctas[clave_pregunta]
                        else:
                            if clave_pregunta in preguntas_ya_vistas:
                                respuesta_anterior = preguntas_ya_vistas[clave_pregunta]; respuesta_tf_ia = "False" if respuesta_anterior == "True" else "True"
                                print(f"      WARN: Pregunta repetida. Anterior: '{respuesta_anterior}'. Forzando: '{respuesta_tf_ia}'")
                            else: print("      IA (T/F)..."); respuesta_tf_ia = ia_utils.obtener_true_false(contexto, texto_afirmacion)
                            if respuesta_tf_ia: preguntas_ya_vistas[clave_pregunta] = respuesta_tf_ia
                        if not respuesta_tf_ia: raise Exception("IA (T/F) falló.")
                        print(f"      IA decidió: {respuesta_tf_ia}"); boton_a_clicar = boton_true if respuesta_tf_ia == "True" else boton_false
                        print(f"      Clic en '{respuesta_tf_ia}'..."); wait_long.until(EC.element_to_be_clickable(boton_a_clicar)); driver.execute_script("arguments[0].click();", boton_a_clicar); time.sleep(0.3)
                    except (NoSuchElementException, TimeoutException) as e: print(f"Error T/F (Single) elems: {e}"); raise Exception("Fallo resolver Mark T/F.")
                    except Exception as e: print(f"Error T/F (Single) lógica: {e}"); raise

                # --- TIPO 7: ANSWER THE QUESTION (OM in a Card) [REFACTORIZADO A LOTE] ---
                elif tipo_pregunta == "TIPO_7_OM_CARD":
                    # Use 16 spaces for indentation
                    print("Tipo: ANSWER THE QUESTION (OM in Card).");
                    cajas_preguntas = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_ANSWER_Q_CAJAS))
                    if not cajas_preguntas: raise Exception("No cajas 'Answer Question'.")
                    print(f"Encontradas {len(cajas_preguntas)} tarjetas."); lista_de_tareas = []; lista_de_preguntas = []; elementos_cajas = []
                    print("Recolectando tareas...");
                    for k, caja in enumerate(cajas_preguntas):
                        # Use 20 spaces for indentation
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            # Use 24 spaces for indentation
                            real_pregunta_elem = caja.find_element(*sel.SELECTOR_ANSWER_Q_TEXTO); real_pregunta = real_pregunta_elem.text.strip()
                            if not real_pregunta: raise Exception(f"Texto vacío tarjeta {k+1}.")
                            opciones_elementos = caja.find_elements(*sel.SELECTOR_ANSWER_Q_BOTONES); opciones = [e.text.strip() for e in opciones_elementos if e.text.strip()]
                            if not opciones: raise Exception(f"No opciones tarjeta {k+1}.")
                            
                            # --- ¡NUEVA CLAVE ÚNICA CON ÍNDICE! ---
                            clave_unica_pregunta = f"{k}:{real_pregunta}"
                            # --- FIN NUEVA CLAVE ---
                            
                            print(f"      Tarea {k+1}: '{real_pregunta}' Ops: {opciones}"); 
                            lista_de_tareas.append({"pregunta": real_pregunta, "opciones": opciones}); 
                            lista_de_preguntas.append(clave_unica_pregunta); # <-- ¡CAMBIADO!
                            elementos_cajas.append(caja)
                        except Exception as e: print(f"Error procesando tarjeta {k+1}: {e}"); raise
                    if not lista_de_tareas: raise Exception("No tareas recolectadas.")
                    clave_pregunta = "|".join(lista_de_preguntas)
                    if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA."); respuestas_lote_ia = soluciones_correctas[clave_pregunta]
                    else:
                        respuesta_anterior_incorrecta = None
                        if clave_pregunta in preguntas_ya_vistas: respuesta_anterior_incorrecta = preguntas_ya_vistas[clave_pregunta]; print(f"      WARN: Pregunta repetida. Anterior: {respuesta_anterior_incorrecta}.")
                        print(f"Enviando {len(lista_de_tareas)} tareas a IA..."); respuestas_lote_ia = ia_utils.obtener_respuestas_om_lote(contexto, lista_de_tareas, respuesta_anterior_incorrecta)
                        if not respuestas_lote_ia or len(respuestas_lote_ia) != len(elementos_cajas): raise Exception("Fallo IA (OM Lote) o nº resp no coincide.")
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia
                    print(f"Respuestas a usar: {respuestas_lote_ia}"); print("Haciendo clics...")
                    exito_global = True
                    for respuesta_ia, caja in zip(respuestas_lote_ia, elementos_cajas):
                        # Use 20 spaces for indentation
                        try:
                            # Use 24 spaces for indentation
                            opciones_elementos_caja = caja.find_elements(*sel.SELECTOR_ANSWER_Q_BOTONES); boton_encontrado = None
                            for b in opciones_elementos_caja:
                                # Use 28 spaces for indentation
                                if b.text.strip() == respuesta_ia: boton_encontrado = b; break
                            if boton_encontrado: print(f"      Clic en '{boton_encontrado.text}'..."); driver.execute_script("arguments[0].click();", boton_encontrado); time.sleep(0.3)
                            else: print(f"Error CRÍTICO: Botón '{respuesta_ia}' no encontrado."); exito_global = False
                        except Exception as e: print(f"Error bucle clics T7: {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo al resolver 'Answer Question'.")

                # --- ¡INICIO DE LA LÓGICA TIPO 8! (EMPAREJAR IMAGEN) ---
                elif tipo_pregunta == "TIPO_8_IMAGEN":
                    # Use 16 spaces for indentation
                    print("Tipo: EMPAREJAR IMAGEN (TIPO 8).");
                    exito_global = True; print("      Extrayendo definiciones (JS)...")
                    js_get_defs = f"return Array.from(document.querySelectorAll('{sel.SELECTOR_DEFINICIONES_AZULES_CSS}')).map(el => el.innerText.trim());"
                    try:
                        # Use 20 spaces for indentation
                        definiciones = driver.execute_script(js_get_defs); definiciones = [d for d in definiciones if d]
                        if not definiciones: raise Exception("JS no encontró texto def.")
                        map_texto_def_a_elemento = {}
                        spans_defs_selenium = wait_long.until(EC.presence_of_all_elements_located((sel.SELECTOR_DEFINICIONES_AZULES_XPATH)))
                        for s in spans_defs_selenium:
                            # Use 24 spaces for indentation
                            texto = s.text.strip();
                            if texto in definiciones: map_texto_def_a_elemento[texto] = s
                        if len(map_texto_def_a_elemento) != len(definiciones): print("Warn: No se mapearon elementos def.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo def: {e}")
                    print(f"      Definiciones encontradas: {definiciones}");
                    
                    print("      Extrayendo imágenes clave (en orden) [Usando SRC/GUID]...")
                    palabras_clave_src = [] # Aquí guardaremos los IDs
                    try:
                        # Use 20 spaces for indentation
                        filas_imagenes = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_IMAGEN_EMPAREJAR))
                        if not filas_imagenes: raise Exception("Selenium no encontró filas de imagen TIPO 8.")
                        for i, fila in enumerate(filas_imagenes):
                            # Use 24 spaces for indentation
                            img = fila.find_element(By.TAG_NAME, "img")
                            src = img.get_attribute("src")
                            if src:
                                # Use 28 spaces for indentation
                                nombre_archivo = src.split('/')[-1].split('?')[0].split('.')[0]
                                palabras_clave_src.append(nombre_archivo)
                            else:
                                print(f"      Error: Fila {i} TIPO 8 sin 'src'.")
                                palabras_clave_src.append(f"imagen_error_{i}")
                        if not palabras_clave_src: raise Exception("No se extrajeron 'src' de imágenes.")
                    except (NoSuchElementException, TimeoutException) as e:
                        raise Exception(f"Error extrayendo 'src' de img TIPO 8: {e}")
                    
                    palabras_clave = palabras_clave_src # Renombramos
                    
                    print(f"      Imágenes clave encontradas (en orden): {palabras_clave}"); 
                    
                    # --- ¡INICIO MODIFICACIÓN CLAVE DE MEMORIA TIPO 8! ---
                    # La clave 'palabras_clave' (los GUIDs) es dinámica.
                    # Usamos el Título de la pregunta y las definiciones como clave estable.
                    clave_pregunta = f"T8:{pregunta_actual_texto}||" + "|".join(sorted(definiciones))
                    
                    if clave_pregunta in soluciones_correctas:
                        # Use 20 spaces for indentation
                        print("      SOLUCIÓN ENCONTRADA en memoria.");
                        # La solución guardada es una LISTA de definiciones en el orden correcto
                        lista_definiciones_ordenadas = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 20 spaces for indentation
                        print("      IA (Emparejar)...")
                        # Pedimos a la IA el diccionario (como antes)
                        pares_ia_temporal = ia_utils.obtener_emparejamientos(palabras_clave, definiciones)
                        if not pares_ia_temporal: raise Exception("IA (Emparejar) falló.")
                        
                        # Convertimos el dict a una lista ordenada para el 'preguntas_ya_vistas'
                        lista_definiciones_ordenadas = []
                        for clave in palabras_clave: # Iteramos en el orden de las claves (top-to-bottom)
                            lista_definiciones_ordenadas.append(pares_ia_temporal[clave])

                         # Guardamos en 'memoria de intentos' para aprender si es 'GREAT'
                        preguntas_ya_vistas[clave_pregunta] = lista_definiciones_ordenadas
                    # --- FIN LÓGICA MEMORIA MODIFICADA ---

                    print(f"      Solución a aplicar (en orden): {lista_definiciones_ordenadas}"); print("      Clickeando en orden (Sistema de Cola)...")
                    
                    # --- Lógica de Clics (MODIFICADA) ---
                    for definicion_correcta in lista_definiciones_ordenadas:
                        # Use 20 spaces for indentation
                        elemento_origen = map_texto_def_a_elemento.get(definicion_correcta)
                        if not elemento_origen: print(f"Error: No WebElement para def '{definicion_correcta}'"); exito_global = False; continue
                        print(f"            Clic en '{definicion_correcta}'...");
                        try:
                            # Use 24 spaces for indentation
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", elemento_origen); time.sleep(0.3)
                            wait_long.until(EC.element_to_be_clickable(elemento_origen)).click(); print("                  Clic OK."); time.sleep(1.0)
                        except Exception as e: print(f"                  Error CRÍTICO (Click) en '{definicion_correcta}': {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo emparejar (Clic en orden).")
                
                # --- FIN TIPO 8 ---
                
                # --- TIPO 9: AUDIO (ADIVINAR Y APRENDER) ---
                elif tipo_pregunta == "TIPO_9_AUDIO":
                    # Use 16 spaces for indentation
                    print("Tipo: AUDIO (TIPO 9).");
                    opciones_elementos = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_OPCIONES))
                    opciones = [e.text for e in opciones_elementos if e.text and e.is_displayed()]
                    if not opciones: raise Exception("No opciones visibles (TIPO 9).")
                    
                    # Usamos la pregunta como clave
                    clave_pregunta = pregunta if "pregunta_sin_titulo" not in pregunta else contexto[:150]
                    
                    print(f"Resolviendo: {pregunta_actual_texto}\nOpciones: {opciones}"); 
                    opciones_ya_vistas[clave_pregunta] = opciones # <--- IMPORTANTE PARA APRENDER
                    
                    if clave_pregunta in soluciones_correctas: 
                        print("      SOLUCIÓN ENCONTRADA."); 
                        respuesta_adivinada = soluciones_correctas[clave_pregunta]
                    else:
                        opciones_para_adivinar = list(opciones)
                        # Si ya hemos fallado antes, intentamos no repetir la misma respuesta
                        if clave_pregunta in preguntas_ya_vistas:
                            respuesta_anterior = preguntas_ya_vistas[clave_pregunta]; 
                            print(f"      WARN: Pregunta (T9) repetida. Anterior: ('{respuesta_anterior}').")
                            if respuesta_anterior in opciones_para_adivinar: 
                                opciones_para_adivinar.remove(respuesta_anterior); 
                                print(f"      Reintentando con: {opciones_para_adivinar}")
                            if not opciones_para_adivinar: 
                                opciones_para_adivinar = list(opciones)
                        
                        # --- ¡LÓGICA DE ADIVINANZA! ---
                        print("      Adivinando respuesta (Audio)..."); 
                        respuesta_adivinada = random.choice(opciones_para_adivinar) # <-- Elige una al azar
                        # --- FIN LÓGICA DE ADIVINANZA ---
                        
                        preguntas_ya_vistas[clave_pregunta] = respuesta_adivinada
                    
                    print(f"Bot decidió: '{respuesta_adivinada}'"); boton_encontrado = None
                    opciones_visibles = driver.find_elements(*sel.SELECTOR_OPCIONES)
                    for b in opciones_visibles:
                        # Use 20 spaces for indentation
                        t_b = ' '.join(b.text.split()); t_ia = ' '.join(respuesta_adivinada.split())
                        if t_b == t_ia: boton_encontrado = b; break
                    if boton_encontrado: print(f"Clic en '{boton_encontrado.text}'..."); driver.execute_script("arguments[0].scrollIntoView(true);",boton_encontrado); time.sleep(0.2); boton_encontrado.click(); time.sleep(0.5)
                    else: raise Exception(f"Botón '{respuesta_adivinada}' no encontrado.")
                # --- FIN TIPO 9 ---

                # --- TIPO DEFAULT: OPCIÓN MÚLTIPLE ---
                elif tipo_pregunta == "TIPO_DEFAULT_OM":
                    # Use 16 spaces for indentation
                    print("Tipo: OPCIÓN MÚLTIPLE (Default).");
                    opciones_elementos = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_OPCIONES))
                    opciones = [e.text for e in opciones_elementos if e.text and e.is_displayed()]
                    if not opciones: raise Exception("No opciones visibles.")
                    clave_pregunta = pregunta if "pregunta_sin_titulo" not in pregunta else contexto[:150]
                    print(f"Resolviendo: {pregunta_actual_texto}\nOpciones: {opciones}"); opciones_ya_vistas[clave_pregunta] = opciones
                    if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA."); respuesta_ia = soluciones_correctas[clave_pregunta]
                    else:
                        opciones_para_ia = list(opciones)
                        if clave_pregunta in preguntas_ya_vistas:
                            respuesta_anterior = preguntas_ya_vistas[clave_pregunta]; print(f"      WARN: Pregunta repetida. Anterior: ('{respuesta_anterior}').")
                            if respuesta_anterior in opciones_para_ia: opciones_para_ia.remove(respuesta_anterior); print(f"      Reintentando con: {opciones_para_ia}")
                            if not opciones_para_ia: print("      ERROR: Se agotaron opciones."); opciones_para_ia = list(opciones)
                        print("IA (OM)..."); respuesta_ia = ia_utils.obtener_respuesta_opcion_multiple(contexto, pregunta, opciones_para_ia)
                        if not respuesta_ia: raise Exception("IA (OM) falló.")
                        preguntas_ya_vistas[clave_pregunta] = respuesta_ia
                    print(f"IA decidió: '{respuesta_ia}'"); boton_encontrado = None
                    opciones_visibles = driver.find_elements(*sel.SELECTOR_OPCIONES)
                    for b in opciones_visibles:
                        # Use 20 spaces for indentation
                        t_b = ' '.join(b.text.split()); t_ia = ' '.join(respuesta_ia.split())
                        if t_b == t_ia: boton_encontrado = b; break
                    if boton_encontrado: print(f"Clic en '{boton_encontrado.text}'..."); driver.execute_script("arguments[0].scrollIntoView(true);",boton_encontrado); time.sleep(0.2); boton_encontrado.click(); time.sleep(0.5)
                    else: raise Exception(f"Botón '{respuesta_ia}' no encontrado.")
                # --- FIN TIPOS ---

                # --- Común: CHECK y OK (Con Lógica de Aprendizaje) ---
                print("Clic CHECK...");
                boton_check = wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_CHECK))
                boton_check.click(); time.sleep(0.5)

                # --- LÓGICA DE APRENDIZAJE (Plan S) ---
                print("Esperando modal de respuesta...")
                boton_ok = wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_OK))
                try:
                    # Use 16 spaces for indentation
                    titulo_modal = driver.find_element(*sel.SELECTOR_MODAL_TITULO).text.lower()
                    
                    # --- CASO 1: RESPUESTA INCORRECTA (APRENDE LA SOLUCIÓN) ---
                    if "incorrect" in titulo_modal or "oops" in titulo_modal:
                        # Use 20 spaces for indentation
                        print("      Respuesta INCORRECTA detectada. Buscando solución...")
                        contenido_modal = driver.find_element(*sel.SELECTOR_MODAL_CONTENIDO).text
                        preguntas_para_ia = None; opciones_para_ia = None; solucion_aprendida = None

                        # Identificar qué tipo de clave/pregunta buscar
                        if tipo_pregunta == "TIPO_6_PARAGRAPH": clave_pregunta = "|".join(lista_ideas_texto); preguntas_para_ia = [idea.split(":", 1)[1] for idea in lista_ideas_texto] # Enviar texto limpio
                        elif tipo_pregunta == "TIPO_7_OM_CARD": clave_pregunta = "|".join(lista_de_preguntas); preguntas_para_ia = [preg.split(":", 1)[1] for preg in lista_de_preguntas] # Enviar texto limpio
                        elif tipo_pregunta == "TIPO_1_ORDENAR": clave_pregunta = "|".join(lista_de_claves_individuales); preguntas_para_ia = lista_de_tareas_ordenar # 'preguntas_para_ia' ahora tiene la lista de tareas
                        elif (tipo_pregunta == "TIPO_DEFAULT_OM" or tipo_pregunta == "TIPO_9_AUDIO") and clave_pregunta in opciones_ya_vistas: 
                            opciones_para_ia = opciones_ya_vistas[clave_pregunta]
                        elif tipo_pregunta == "TIPO_5_TF_SINGLE": opciones_para_ia = ["True", "False"] # clave_pregunta ya definida
                        elif tipo_pregunta == "TIPO_3_TF_MULTI": clave_pregunta = "|".join(lista_afirmaciones_texto); preguntas_para_ia = [afirm.split(":", 1)[1] for afirm in lista_afirmaciones_texto] # Enviar texto limpio
                        elif tipo_pregunta == "TIPO_2_COMPLETAR" and clave_pregunta in opciones_ya_vistas: opciones_para_ia = opciones_ya_vistas[clave_pregunta]
                        
                        # --- ¡INICIO DE LA MODIFICACIÓN (Aprendizaje TIPO 4 y TIPO 8)! ---
                        elif tipo_pregunta == "TIPO_4_EMPAREJAR" or tipo_pregunta == "TIPO_8_IMAGEN":
                            # Use 24 spaces for indentation
                            print(f"      Enviando texto a IA (Aprendizaje Emparejar TIPO {tipo_pregunta[-1]}) para extraer solución...");
                            try:
                                # 'palabras_clave' y 'definiciones' fueron definidas en la lógica de TIPO 4/8
                                # 1. Obtenemos el diccionario de aprendizaje (como antes)
                                dict_solucion = ia_utils.extraer_solucion_emparejar(contenido_modal, palabras_clave, definiciones)
                                
                                # 2. ¡MODIFICACIÓN! Convertimos el dict a una LISTA ordenada
                                if dict_solucion:
                                    solucion_aprendida_lista = []
                                    # Iteramos sobre 'palabras_clave' para mantener el orden de la página
                                    for clave in palabras_clave: 
                                        if clave in dict_solucion:
                                            solucion_aprendida_lista.append(dict_solucion[clave])
                                        else:
                                            # Fallback por si la IA modificó la clave (ej. 'img.png ' vs 'img.png')
                                            clave_alt = clave.strip()
                                            clave_alt2 = clave + " "
                                            if clave_alt in dict_solucion: solucion_aprendida_lista.append(dict_solucion[clave_alt])
                                            elif clave_alt2 in dict_solucion: solucion_aprendida_lista.append(dict_solucion[clave_alt2])
                                            else:
                                                print(f"      ERROR APRENDIZAJE: No se encontró la clave '{clave}' en el dict de la IA.")
                                                raise Exception("Fallo al mapear dict de aprendizaje a lista.")
                                    
                                    solucion_aprendida = solucion_aprendida_lista # ¡Ahora es una lista!
                                else:
                                    solucion_aprendida = None

                            except NameError:
                                print("      Error: 'palabras_clave' o 'definiciones' no definidas. No se puede aprender.")
                                solucion_aprendida = None
                        # --- FIN DE LA MODIFICACIÓN ---
                            
                        # Extraer solución LOTE (T1, T3, T6, T7)
                        # --- MODIFICADO: Añadido 'if' ---
                        if tipo_pregunta in ["TIPO_1_ORDENAR", "TIPO_3_TF_MULTI", "TIPO_6_PARAGRAPH", "TIPO_7_OM_CARD"] and clave_pregunta and preguntas_para_ia and contenido_modal:
                            # Use 24 spaces for indentation
                            solucion_lista_ordenada = None # Variable para guardar el resultado
                            if tipo_pregunta == "TIPO_3_TF_MULTI":
                                print("      Enviando texto a IA (Lote T/F) para extraer solución..."); solucion_lista_ordenada = ia_utils.extraer_solucion_lote_tf(contenido_modal, preguntas_para_ia)
                            elif tipo_pregunta == "TIPO_1_ORDENAR":
                                print("      Enviando texto a IA (Ordenar Lote) para extraer solución...")
                                solucion_lote_ordenar = []
                                exito_aprendizaje_lote = True
                                # 'preguntas_para_ia' es la lista_de_tareas_ordenar
                                for i, tarea_ind in enumerate(preguntas_para_ia): 
                                    print(f"      IA (Aprendizaje Ord) para Tarea {i+1}...")
                                    sol_individual = ia_utils.extraer_solucion_ordenar(contenido_modal, tarea_ind["frases"])
                                    if not sol_individual:
                                        print(f"      IA (Aprendizaje Ord) Tarea {i+1} falló.")
                                        exito_aprendizaje_lote = False; break
                                    solucion_lote_ordenar.append(sol_individual)
                                
                                if exito_aprendizaje_lote:
                                    solucion_lista_ordenada = solucion_lote_ordenar
                                else:
                                    solucion_lista_ordenada = None
                            else: # Para T6 y T7
                                print("      Enviando texto a IA (Lote Genérico) para extraer solución..."); solucion = ia_utils.extraer_solucion_del_error(contenido_modal, preguntas_para_ia)
                                if solucion:
                                    # Re-mapeamos la solución a las claves *limpias*
                                    solucion_lista_ordenada_temp = []
                                    mapeo_fallido = False
                                    for p_limpio in preguntas_para_ia: # 'preguntas_para_ia' tiene los textos limpios
                                        if p_limpio in solucion:
                                            solucion_lista_ordenada_temp.append(str(solucion[p_limpio]).strip())
                                        else:
                                            # Intentar encontrar con/sin espacio al final (bug IA T7)
                                            p_alt1 = p_limpio + " "
                                            p_alt2 = p_limpio.strip()
                                            if p_alt1 in solucion: solucion_lista_ordenada_temp.append(str(solucion[p_alt1]).strip())
                                            elif p_alt2 in solucion: solucion_lista_ordenada_temp.append(str(solucion[p_alt2]).strip())
                                            else:
                                                print(f"      IA (Lote Genérico) no pudo mapear solución para: '{p_limpio}'"); mapeo_fallido = True; break
                                    if not mapeo_fallido: solucion_lista_ordenada = solucion_lista_ordenada_temp
                                    else: solucion_lista_ordenada = None
                                else: solucion_lista_ordenada = None
                            
                            if solucion_lista_ordenada: 
                                print(f"      ¡SOLUCIÓN LOTE APRENDIDA! -> {solucion_lista_ordenada}"); 
                                solucion_aprendida = solucion_lista_ordenada
                            else: print("      IA (Lote) no pudo extraer o validar la solución.")
                        
                        # Extraer solución SIMPLE (T2, T5, Default)
                        elif tipo_pregunta in ["TIPO_2_COMPLETAR", "TIPO_5_TF_SINGLE", "TIPO_DEFAULT_OM", "TIPO_9_AUDIO"] and clave_pregunta and opciones_para_ia and contenido_modal:
                            # Use 24 spaces for indentation
                            print("      Enviando texto a IA (Simple) para extraer solución..."); solucion_simple = ia_utils.extraer_solucion_simple(contenido_modal, opciones_para_ia)
                            if solucion_simple: 
                                print(f"      ¡SOLUCIÓN SIMPLE APRENDIDA! -> {solucion_simple}"); 
                                solucion_aprendida = solucion_simple
                            else: print("      IA (Simple) no pudo extraer solución.")

                        # --- ¡INICIO MODIFICACIÓN! (Ignorar T4 y T8) ---
                        # Ignorar T4 y T8 (porque ya tienen su propio bloque de aprendizaje arriba)
                        elif not tipo_pregunta in ["TIPO_4_EMPAREJAR", "TIPO_8_IMAGEN"]: 
                             print(f"      No se implementó aprendizaje para ({tipo_pregunta}) o clave/opciones no encontradas.")
                        # --- FIN MODIFICACIÓN ---

                        # --- ¡GUARDADO EN MEMORIA (SI APRENDIÓ ALGO)! ---
                        if clave_pregunta and solucion_aprendida:
                            # Use 24 spaces for indentation
                            soluciones_correctas[clave_pregunta] = solucion_aprendida
                            guardar_memoria_en_disco() # <-- ¡GUARDAMOS EN DISCO!
                    
                    # --- CASO 2: RESPUESTA CORRECTA (GUARDA EL ACIERTO) ---
                    elif "correct" in titulo_modal or "great" in titulo_modal:
                        # Use 20 spaces for indentation
                        print(f"      Respuesta CORRECTA detectada (Modal: {titulo_modal}).")
                        
                        # Verificamos si la clave es válida y si NO la teníamos ya guardada
                        if clave_pregunta and clave_pregunta not in soluciones_correctas:
                            # Use 24 spaces for indentation
                            print(f"      Guardando nuevo acierto en memoria...")
                            try:
                                # Use 28 spaces for indentation
                                # La respuesta que dimos ya está en 'preguntas_ya_vistas'
                                respuesta_correcta = preguntas_ya_vistas[clave_pregunta]
                                soluciones_correctas[clave_pregunta] = respuesta_correcta
                                print(f"      ¡SOLUCIÓN (por acierto) APRENDIDA! -> {respuesta_correcta}")
                                guardar_memoria_en_disco() # <-- ¡GUARDAMOS EN DISCO!
                            except KeyError:
                                print(f"      WARN: Acierto, pero no se encontró la respuesta en 'preguntas_ya_vistas' para clave: {clave_pregunta}")
                            except Exception as e_acierto:
                                print(f"      WARN: Error guardando acierto: {e_acierto}")
                        elif clave_pregunta:
                            print("      La solución ya estaba en memoria. No se necesita guardar.")
                        
                except Exception as e: 
                    print(f"      WARN: No se pudo leer modal o aprender. {e}")

                print("Clic OK..."); boton_ok.click()
                print("Respuesta enviada! Esperando que desaparezca modal..."); wait_long.until(EC.invisibility_of_element_located(sel.SELECTOR_OK))
                print("Modal desaparecido. Cargando siguiente pregunta..."); time.sleep(0.5)

            except (TimeoutException, Exception) as e:
                # Use 12 spaces for indentation
                # --- PLAN V: SKIP EN LUGAR DE REFRESH ---
                print(f"Error inesperado o Timeout: {e}")
                try:
                    # Use 16 spaces for indentation
                    # --- ¡MODIFICADO! (Reading y Grammar) ---
                    wait_short.until(EC.element_to_be_clickable(sel.SELECTOR_CONTINUE)).click(); print("      FIN detectado tras error! Yendo a siguiente lección."); wait_long.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE)); break
                except (TimeoutException, NoSuchElementException):
                    print("      El test no ha terminado. Intentando 'SKIP'...");
                    try:
                        # Use 20 spaces for indentation
                        wait_short.until(EC.element_to_be_clickable(sel.SELECTOR_SKIP)).click(); print("      Botón 'SKIP' clickeado."); pregunta_actual_texto = ""; time.sleep(2); continue
                    except (TimeoutException, NoSuchElementException) as skip_e:
                        print(f"      No se pudo clickear 'SKIP' ({skip_e}). Refrescando como último recurso.");
                        try: driver.refresh(); pregunta_actual_texto = ""; time.sleep(3)
                        except Exception as refresh_err: print(f"¡Error al refrescar! {refresh_err}. Deteniendo."); raise

    # --- Fin Bucle EXTERNO ---
except Exception as e:
    print(f"\n--- ERROR FATAL ---"); print(f"Bot detenido: {e}")
finally:
    print("\nProceso terminado. Cerrando en 20 seg."); time.sleep(20); driver.quit()
