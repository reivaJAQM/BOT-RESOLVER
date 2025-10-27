# bot_main.py
# Script principal que orquesta el bot.
# ¡Refactorizado con "Plan Maestro" y "Plan S"!
# --- ¡ACTUALIZADO CON TIPO 11 (Escribir Opciones) y TODAS las correcciones! ---
# --- (T1, T2, T3/T5, T4, T10, T11) ---

import time
import json
import random
import copy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, JavascriptException
from selenium.webdriver.common.action_chains import ActionChains

# --- ¡NUESTROS MÓdulos! ---
import config
import bot_selectors as sel
import ia_utils
# -----------------------------

# Configuración Selenium
print("Iniciando Navegador...");
try:
    # Use 4 spaces for indentation
    service = EdgeService(executable_path=config.DRIVER_PATH)
    driver = webdriver.Edge(service=service)

    print("Maximizando ventana...")
    driver.maximize_window()

    wait_short = WebDriverWait(driver, 5)
    wait_long = WebDriverWait(driver, 15)
    wait_extra_long = WebDriverWait(driver, 25)
    print("Navegador Listo!")
except Exception as e:
    # Use 4 spaces for indentation
    print(f"Error iniciando navegador: {e}"); exit()

# --- INICIO DE LA MEMORIA DEL BOT ---
preguntas_ya_vistas = {}
opciones_ya_vistas = {}
soluciones_correctas = {}
MEMORIA_FILE = "memoria_bot.json"

try:
    # Use 4 spaces for indentation
    with open(MEMORIA_FILE, 'r', encoding='utf-8') as f:
        soluciones_correctas = json.load(f)
    print(f"¡Memoria cargada! {len(soluciones_correctas)} soluciones conocidas.")
except FileNotFoundError:
    # Use 4 spaces for indentation
    print("No se encontró memoria previa (memoria_bot.json). Empezando de cero.")
except json.JSONDecodeError:
    # Use 4 spaces for indentation
    print("Error al leer la memoria. Empezando de cero.")

def guardar_memoria_en_disco():
    """Guarda el diccionario 'soluciones_correctas' en el archivo JSON."""
    try:
        # Use 8 spaces for indentation
        with open(MEMORIA_FILE, 'w', encoding='utf-8') as f:
            json.dump(soluciones_correctas, f, indent=4, ensure_ascii=False)
        print("      ¡Memoria actualizada en disco!")
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"      ERROR CRÍTICO al guardar memoria: {e}")
# --- FIN DE LA MEMORIA DEL BOT ---


if ia_utils.model is None:
    # Use 4 spaces for indentation
    print("ERROR FATAL: El modelo de IA no se pudo inicializar.")
    driver.quit()
    exit()

# --- INICIO DEL SCRIPT ---
try:
    # Use 4 spaces for indentation
    print(f"Navegando: {config.URL_INICIAL}"); driver.get(config.URL_INICIAL)

    # --- LOGIN ---
    try:
        # Use 8 spaces for indentation
        print("P1: Pop-up..."); wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_CERRAR_POPUP)).click(); time.sleep(1)
    except TimeoutException:
        # Use 8 spaces for indentation
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
        # Use 8 spaces for indentation
        try:
            # Use 12 spaces for indentation
            print("Buscando la siguiente lección disponible...")
            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"); time.sleep(0.5)

            leccion = wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_LECCION_DISPONIBLE))
            print("      Lección encontrada. Haciendo scroll...")
            driver.execute_script("arguments[0].scrollIntoView(true);", leccion); time.sleep(0.5)
            leccion.click()

            print("      Clic en 'Start'...")
            wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_BOTON_START)).click()
            print("Empezando nuevo test...")
        except TimeoutException:
            # Use 12 spaces for indentation
            print("\n" + "#"*40); print("¡NO SE ENCONTRARON MÁS LECCIONES DISPONIBLES!"); print("¡Bot ha completado todo el trabajo! Terminando..."); break
        except Exception as e:
            # Use 12 spaces for indentation
            print(f"Error al intentar empezar la siguiente lección: {e}"); break

        # --- BUCLE DE PREGUNTAS (INTERNO) ---
        pregunta_actual_texto = ""
        # --- INICIO MODIFICACIÓN HASH ---
        tipo_pregunta = ""; clave_pregunta = None; lista_ideas_texto = []; lista_de_preguntas = []; lista_afirmaciones_texto = []; frases_des = []; lista_de_claves_individuales = []; lista_de_tareas_ordenar = []
        palabras_clave = []; definiciones = []; lista_de_tareas_completar = []
        # --- ¡AÑADIDO PARA TIPO 11! ---
        lista_de_tareas_escribir = []; lista_palabras_desordenadas_raw = []; lista_frases_t11 = []
        imagen_hash = ""; audio_hash = ""; contexto_hash = "" # Añadimos reseteo de hashes
        # --- FIN MODIFICACIÓN HASH ---
        respuesta_fue_incorrecta = False

        while True:
            # Use 12 spaces for indentation
            print("\n" + "="*30)
            try:
                # Use 16 spaces for indentation
                # --- DETECCIÓN FIN ---
                print("Verificando fin...")
                try:
                    # Use 20 spaces for indentation
                    boton_continue = wait_short.until(EC.element_to_be_clickable(sel.SELECTOR_CONTINUE))
                    print("FIN DE LA LECCIÓN! Clic CONTINUE..."); boton_continue.click()
                    print("Esperando regreso a la página de lecciones...");
                    wait_long.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
                    print("Página de lecciones cargada. Buscando siguiente lección..."); time.sleep(2); break
                except TimeoutException:
                    # Use 20 spaces for indentation
                    print("Test continúa...")

                # --- LÓGICA DE ESPERA ---
                print("Esperando nueva pregunta..."); current_url = driver.current_url
                try:
                    # Use 20 spaces for indentation
                    wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK)); print("      Botón 'CHECK' detectado. Página cargada.")
                except TimeoutException:
                    # Use 20 spaces for indentation
                    print("Error: El botón 'CHECK' no cargó. Página atascada."); raise

                time.sleep(1)
                print("Detectando tipo de pregunta por contenido...")

                # El ORDEN es crucial
                
                # --- ¡INICIO CORRECCIÓN DETECCIÓN T10 / T11 / T3 / T5! ---
                letras_elem_t10 = driver.find_elements(*sel.SELECTOR_LETRAS_DESORDENADAS)
                input_elem = driver.find_elements(*sel.SELECTOR_INPUT_ESCRIBIR)
                
                if len(input_elem) > 0 and len(letras_elem_t10) > 0 and len(input_elem) == len(letras_elem_t10):
                    print("      Contenido detectado: [TIPO 10]"); tipo_pregunta = "TIPO_10_ESCRIBIR" # T10 (Anagrama)
                elif len(input_elem) > 0 and len(letras_elem_t10) == 0:
                     print("      Contenido detectado: [TIPO 11]"); tipo_pregunta = "TIPO_11_ESCRIBIR_OPCIONES" # T11 (Completar escribiendo)
                
                elif len(driver.find_elements(*sel.SELECTOR_ANSWER_Q_CAJAS)) > 0: print("      Contenido detectado: [TIPO 7]"); tipo_pregunta = "TIPO_7_OM_CARD"
                elif len(driver.find_elements(*sel.SELECTOR_PARAGRAPH_CAJAS)) > 0: print("      Contenido detectado: [TIPO 6]"); tipo_pregunta = "TIPO_6_PARAGRAPH"
                
                # --- LÓGICA DE DETECCIÓN MEJORADA (T3 vs T5) ---
                elif len(driver.find_elements(*sel.SELECTOR_CAJAS_TF)) > 0: 
                    num_cajas_tf = len(driver.find_elements(*sel.SELECTOR_CAJAS_TF))
                    if num_cajas_tf > 1:
                        print(f"      Contenido detectado: [TIPO 3] ({num_cajas_tf} cajas)"); 
                        tipo_pregunta = "TIPO_3_TF_MULTI"
                    else:
                        print(f"      Contenido detectado: [TIPO 5] ({num_cajas_tf} caja)"); 
                        tipo_pregunta = "TIPO_5_TF_SINGLE"
                # --- ¡FIN CORRECCIÓN DETECCIÓN! ---

                elif len(driver.find_elements(*sel.SELECTOR_LINEAS_COMPLETAR)) > 0: print("      Contenido detectado: [TIPO 2]"); tipo_pregunta = "TIPO_2_COMPLETAR"
                elif len(driver.find_elements(*sel.SELECTOR_CONTENEDOR_ORDENAR)) > 0: print("      Contenido detectado: [TIPO 1]"); tipo_pregunta = "TIPO_1_ORDENAR"
                elif len(driver.find_elements(*sel.SELECTOR_IMAGEN_EMPAREJAR)) > 0: print("      Contenido detectado: [TIPO 8]"); tipo_pregunta = "TIPO_8_IMAGEN"
                elif len(driver.find_elements(*sel.SELECTOR_FILAS_EMPAREJAR)) > 0: print("      Contenido detectado: [TIPO 4]"); tipo_pregunta = "TIPO_4_EMPAREJAR"
                elif len(driver.find_elements(*sel.SELECTOR_AUDIO)) > 0: print("      Contenido detectado: [TIPO 9]"); tipo_pregunta = "TIPO_9_AUDIO"
                else: print("      No se detectó contenido especial. Se asume [DEFAULT]"); tipo_pregunta = "TIPO_DEFAULT_OM"

                print("Leyendo datos (Contexto y Título)...")
                try:
                    # Use 20 spaces for indentation
                    contexto = wait_short.until(EC.visibility_of_element_located(sel.SELECTOR_CONTEXTO)).text
                except TimeoutException:
                    # Use 20 spaces for indentation
                    print("Warn: No contexto."); contexto = ""

                # --- INICIO MODIFICACIÓN HASH DE CONTEXTO ---
                # Creamos un hash simple del contexto para diferenciar preguntas
                # con el mismo título pero diferente párrafo.
                contexto_hash = f"CTX:{contexto[:50]}...{contexto[-50:]}"
                # --- FIN MODIFICACIÓN HASH DE CONTEXTO ---
                
                try:
                    # Use 20 spaces for indentation
                    pregunta_elemento = wait_long.until(EC.presence_of_element_located(sel.SELECTOR_PREGUNTA))
                    try:
                        # Use 24 spaces for indentation
                        WebDriverWait(driver, 7).until(lambda d: d.find_element(*sel.SELECTOR_PREGUNTA).text.strip() != "")
                    except TimeoutException:
                        # Use 24 spaces for indentation
                        print("      WARN: Title element found, but text remained empty.")
                    pregunta = pregunta_elemento.text.strip()
                    try:
                        # Use 24 spaces for indentation
                        WebDriverWait(driver, 3).until(lambda d: d.find_element(*sel.SELECTOR_PREGUNTA).text.strip() != pregunta_actual_texto)
                    except TimeoutException:
                        # Use 24 spaces for indentation
                         print("      WARN: Title text appeared but did not change from previous.")
                    current_title_text = driver.find_element(*sel.SELECTOR_PREGUNTA).text.strip()
                    if not current_title_text:
                        # Use 24 spaces for indentation
                        print("      ERROR: Title extraction failed, text remained empty. Using fallback.")
                        pregunta = f"pregunta_sin_titulo_{contexto[:50]}"
                        pregunta_actual_texto = pregunta
                    else:
                        # Use 24 spaces for indentation
                        pregunta_actual_texto = current_title_text
                        pregunta = pregunta_actual_texto
                        print(f"      Título detectado: '{pregunta}'")
                except TimeoutException:
                    # Use 20 spaces for indentation
                    print("      ERROR: Title element (SELECTOR_PREGUNTA) not found. Using fallback.")
                    pregunta = f"pregunta_sin_titulo_{contexto[:50]}";
                    pregunta_actual_texto = pregunta

                # --- TIPO 1: ORDENAR (MÚLTIPLE) ---
                if tipo_pregunta == "TIPO_1_ORDENAR":
                    # Use 20 spaces for indentation
                    print("Tipo: ORDENAR (Múltiple).")
                    # ... (Lógica TIPO 1 completa) ...
                    contenedores = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_CONTENEDOR_ORDENAR))
                    if not contenedores: raise Exception("No se encontraron contenedores TIPO 1.")
                    print(f"Encontrados {len(contenedores)} contenedores para ordenar.")
                    lista_de_claves_individuales = []
                    lista_de_tareas_ordenar = []
                    for k, contenedor in enumerate(contenedores):
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", contenedor); time.sleep(0.1)
                        cajas_inicial = contenedor.find_elements(*sel.SELECTOR_CAJAS_ORDENAR)
                        frases_des_individual = []
                        map_id_a_texto_individual = {}
                        ids_individual = []
                        for i, c in enumerate(cajas_inicial):
                            try:
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
                        
                        # --- ¡INICIO CORRECCIÓN CLAVE INESTABLE TIPO 1! ---
                        # Ordenamos las frases alfabéticamente para crear una clave estable
                        # que no dependa del orden en que Selenium las encuentre.
                        frases_ordenadas_para_clave = sorted(frases_des_individual)
                        clave_ind = "|".join(frases_ordenadas_para_clave) 
                        # --- ¡FIN CORRECCIÓN CLAVE INESTABLE TIPO 1! ---
                        
                        lista_de_claves_individuales.append(f"{k}:{clave_ind}")
                        lista_de_tareas_ordenar.append({"frases": frases_des_individual,"map_id_a_texto": map_id_a_texto_individual,"contenedor_elem": contenedor})
                    if not lista_de_tareas_ordenar: raise Exception("No se recolectaron tareas TIPO 1 válidas.")
                    clave_pregunta = "|".join(lista_de_claves_individuales)
                    lista_ordenes_ia = []
                    if clave_pregunta in soluciones_correctas:
                        print("      SOLUCIÓN LOTE TIPO 1 ENCONTRADA en memoria.");
                        lista_ordenes_ia = soluciones_correctas[clave_pregunta]
                    else:
                        print("      Llamando a IA individualmente para TIPO 1 (se guardará en lote)...")
                        exito_ia_individual = True
                        for i, tarea in enumerate(lista_de_tareas_ordenar):
                            print(f"      IA (Ord) para Tarea {i+1}...")
                            # --- ¡INICIO CORRECCIÓN TIPO 1 (Contexto/Título)! ---
                            orden_ia_individual = ia_utils.obtener_orden_correcto(contexto, tarea["frases"], pregunta_actual_texto)
                            # --- ¡FIN CORRECCIÓN TIPO 1! ---
                            if not orden_ia_individual:
                                print(f"Error IA (Ord) Tarea {i+1}."); exito_ia_individual = False; break
                            lista_ordenes_ia.append(orden_ia_individual)
                        if not exito_ia_individual: raise Exception("Fallo IA al obtener orden TIPO 1 individual.")
                        preguntas_ya_vistas[clave_pregunta] = lista_ordenes_ia
                    print(f"Órdenes a aplicar (lote): {lista_ordenes_ia}")
                    if len(lista_ordenes_ia) != len(lista_de_tareas_ordenar):
                        raise Exception("Fallo crítico: El número de soluciones no coincide con el de tareas TIPO 1.")
                    print("Reordenando JS (Lote)...")
                    exito_global = True
                    js = "var c=arguments[0],ids=arguments[1],m={};for(let i=0;i<c.children.length;i++){let o=c.children[i],d=o.firstElementChild;if(d&&d.getAttribute('data-rbd-draggable-id')){m[d.getAttribute('data-rbd-draggable-id')]=o;}}while(c.firstChild)c.removeChild(c.firstChild);ids.forEach(id=>{if(m[id])c.appendChild(m[id]);else console.error('JS Err ID:',id);});console.log('JS OK.');"
                    for orden_ia, tarea in zip(lista_ordenes_ia, lista_de_tareas_ordenar):
                        
                        # --- ¡INICIO 2DA CORRECCIÓN MAPEO TIPO 1 (Manejo de Duplicados)! ---
                        
                        # 1. Creamos un mapa que almacena LISTAS de IDs por cada texto
                        #    (para manejar frases duplicadas como 'going')
                        map_texto_lower_a_ids_lista = {}
                        for id_val, texto_val in tarea["map_id_a_texto"].items():
                            texto_lower = texto_val.lower().strip()
                            if texto_lower not in map_texto_lower_a_ids_lista:
                                map_texto_lower_a_ids_lista[texto_lower] = []
                            map_texto_lower_a_ids_lista[texto_lower].append(id_val)
                        
                        # 2. Hacemos una copia para poder "consumir" los IDs con .pop()
                        map_ids_disponibles = copy.deepcopy(map_texto_lower_a_ids_lista)
                        
                        ids_ok_filtrado = []
                        mapeo_fallido = False
                        
                        # 3. Iteramos por la solución de la IA y consumimos los IDs
                        for texto_ia in orden_ia:
                            texto_ia_lower = texto_ia.lower().strip()
                            
                            if texto_ia_lower in map_ids_disponibles and map_ids_disponibles[texto_ia_lower]:
                                # Tomamos el primer ID disponible y lo removemos de la lista
                                id_para_usar = map_ids_disponibles[texto_ia_lower].pop(0)
                                ids_ok_filtrado.append(id_para_usar)
                            else:
                                # Si la IA nos da un texto que no existe o ya se usaron todos sus IDs
                                print(f"Error Mapeo T1: No hay ID disponible para '{texto_ia}' (Buscando: '{texto_ia_lower}')")
                                mapeo_fallido = True
                                break
                        
                        if mapeo_fallido or len(ids_ok_filtrado) != len(tarea["frases"]):
                        # --- ¡FIN 2DA CORRECCIÓN MAPEO TIPO 1! ---
                            print(f"Error: Fallo mapeo IDs JS para tarea {tarea['frases']}"); exito_global = False; continue
                        try:
                            driver.execute_script(js, tarea["contenedor_elem"], ids_ok_filtrado); time.sleep(0.5)
                        except JavascriptException as e:
                            print(f"Error JS en TIPO 1 Lote: {e}"); exito_global = False; continue
                    print("JS OK (Lote).")
                    if not exito_global: raise Exception("Fallo JS durante reordenamiento TIPO 1 Lote.")

                #--- TIPO 2: COMPLETAR (REFACTORIZADO A LOTE CON CLAVE ESTABLE) ---
                elif tipo_pregunta == "TIPO_2_COMPLETAR":
                    # Use 20 spaces for indentation
                    print("Tipo: COMPLETAR PALABRAS (Lote).");
                    lineas = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_LINEAS_COMPLETAR))
                    if not lineas: raise Exception("No se encontraron líneas.")
                    print(f"Encontradas {len(lineas)} líneas (tareas).")
                    lista_de_tareas_completar = []
                    for i, linea in enumerate(lineas):
                        # Use 24 spaces for indentation
                        print(f"\nRecolectando línea {i+1}...")
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", linea); time.sleep(0.1)
                        spans = linea.find_elements(By.XPATH, "./div/span[@class='inline-block']")
                        botones_en_linea = linea.find_elements(*sel.SELECTOR_BOTONES_OPCION_COMPLETAR)
                        opciones_palabra = [b.text.strip() for b in botones_en_linea if b.text.strip()]
                        if not opciones_palabra:
                            # Use 28 spaces for indentation
                            print(f"Warn: Línea {i+1} sin opciones. Omitiendo.")
                            continue
                        frase_para_ia = ""; placeholder_colocado = False
                        for j, span in enumerate(spans):
                            # Use 28 spaces for indentation
                            if not span.find_elements(*sel.SELECTOR_BOTONES_OPCION_COMPLETAR):
                                # Use 32 spaces for indentation
                                frase_para_ia += span.text.strip() + " "
                            elif not placeholder_colocado:
                                # Use 32 spaces for indentation
                                frase_para_ia += "___ "
                                placeholder_colocado = True
                        frase_para_ia = ' '.join(frase_para_ia.split())
                        if not placeholder_colocado: frase_para_ia = "___"
                        print(f"      Tarea {i+1}. Frase: '{frase_para_ia}'. Opciones: {opciones_palabra}");
                        lista_de_tareas_completar.append({"frase": frase_para_ia,"opciones": opciones_palabra,"botones": botones_en_linea})
                    if not lista_de_tareas_completar: raise Exception("No se recolectaron tareas TIPO 2 válidas.")
                    titulo_limpio = pregunta_actual_texto.strip()
                    # --- INICIO MODIFICACIÓN HASH DE CONTEXTO ---
                    clave_pregunta = f"T2_BATCH:{titulo_limpio}||{contexto_hash}"
                    # --- FIN MODIFICACIÓN HASH DE CONTEXTO ---
                    
                    respuestas_lote_ia = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN LOTE TIPO 2 ENCONTRADA en memoria (Dict).");
                        dict_soluciones = soluciones_correctas[clave_pregunta]
                        mapeo_ok = True
                        for tarea in lista_de_tareas_completar:
                            # Use 28 spaces for indentation
                            frase_key = tarea["frase"]
                            if frase_key in dict_soluciones:
                                # Use 32 spaces for indentation
                                respuestas_lote_ia.append(dict_soluciones[frase_key])
                            else:
                                # Use 32 spaces for indentation
                                print(f"      ERROR Memoria T2: No se encontró la frase '{frase_key}' en el dict de soluciones.");
                                respuestas_lote_ia = []
                                mapeo_ok = False; break
                        if not mapeo_ok:
                             # Use 28 spaces for indentation
                             print("      Fallo mapeo de memoria T2, llamando a IA...")
                    if not respuestas_lote_ia:
                        # Use 24 spaces for indentation
                        print("      Llamando a IA (Lote Completar) para TIPO 2...")
                        tareas_para_ia = [{"frase": t["frase"], "opciones": t["opciones"]} for t in lista_de_tareas_completar]
                        respuestas_ia_temp = ia_utils.obtener_palabras_correctas_lote(contexto, tareas_para_ia)
                        if not respuestas_ia_temp or len(respuestas_ia_temp) != len(lista_de_tareas_completar):
                            # Use 28 spaces for indentation
                            raise Exception("Fallo IA (Completar Lote) o nº resp no coincide.")
                        respuestas_lote_ia = respuestas_ia_temp
                        frases_clave = [t["frase"] for t in lista_de_tareas_completar]
                        preguntas_ya_vistas[clave_pregunta] = dict(zip(frases_clave, respuestas_lote_ia))
                    print(f"Respuestas TIPO 2 a aplicar (lote): {respuestas_lote_ia}")
                    exito_global = True
                    for respuesta_ia, tarea in zip(respuestas_lote_ia, lista_de_tareas_completar):
                        # Use 24 spaces for indentation
                        boton_clic = None
                        for b in tarea["botones"]:
                            # Use 28 spaces for indentation
                            if b.text.strip() == respuesta_ia:
                                # Use 32 spaces for indentation
                                boton_clic = b; break
                        if boton_clic:
                            # Use 28 spaces for indentation
                            try:
                                # Use 32 spaces for indentation
                                print(f"      Clic en '{respuesta_ia}'...");
                                driver.execute_script("arguments[0].click();", boton_clic); time.sleep(0.4)
                            except Exception as e:
                                # Use 32 spaces for indentation
                                print(f"Error clic T2: {e}"); exito_global = False; break
                        else:
                            # Use 28 spaces for indentation
                            print(f"Error CRÍTICO T2: Botón '{respuesta_ia}' no encontrado.");
                            exito_global = False; break
                    if not exito_global: raise Exception("Fallo al completar palabras (Lote).")

                # --- TIPO 3: TRUE/FALSE MÚLTIPLE ---
                elif tipo_pregunta == "TIPO_3_TF_MULTI":
                    # Use 20 spaces for indentation
                    print("Tipo: TRUE/FALSE MÚLTIPLE.")
                    # ... (Lógica TIPO 3 completa) ...
                    cajas_afirmacion = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_CAJAS_TF))
                    if not cajas_afirmacion: raise Exception("No se encontraron cajas True/False.")
                    print(f"Encontradas {len(cajas_afirmacion)} afirmaciones.")
                    lista_afirmaciones_texto = []
                    elementos_cajas_botones = []
                    print("Recolectando afirmaciones...")
                    for k, caja in enumerate(cajas_afirmacion):
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            texto_afirmacion_elem = caja.find_element(*sel.SELECTOR_TEXTO_AFIRMACION_TF)
                            wait_short.until(EC.visibility_of(texto_afirmacion_elem))
                            texto_afirmacion = texto_afirmacion_elem.text.strip()
                            boton_true = caja.find_element(*sel.SELECTOR_BOTON_TRUE_TF)
                            boton_false = caja.find_element(*sel.SELECTOR_BOTON_FALSE_TF)
                            if texto_afirmacion:
                                clave_unica_afirmacion = f"{k}:{texto_afirmacion}"
                                lista_afirmaciones_texto.append(clave_unica_afirmacion)
                                elementos_cajas_botones.append((caja, boton_true, boton_false))
                            else: print(f"Warn: Caja {k+1} sin texto.")
                        except (NoSuchElementException, TimeoutException) as e_inner:
                            print(f"Error leyendo caja {k+1}: {e_inner}"); raise Exception(f"Fallo crítico al leer caja T/F {k+1}")
                    if not lista_afirmaciones_texto: raise Exception("No se pudieron recolectar afirmaciones T/F.")
                    clave_pregunta = "|".join(lista_afirmaciones_texto)
                    respuestas_tf_lote = []
                    if clave_pregunta in soluciones_correctas:
                        print("      SOLUCIÓN LOTE T/F ENCONTRADA en memoria."); respuestas_tf_lote = soluciones_correctas[clave_pregunta]
                    else:
                        print("      Llamando a IA individualmente (con memoria de intento)...")
                        respuestas_tf_lote_temporal = []
                        exito_ia_individual = True
                        for texto_afirmacion_con_indice in lista_afirmaciones_texto:
                            texto_afirmacion_real = texto_afirmacion_con_indice.split(":", 1)[1]
                            clave_individual = texto_afirmacion_con_indice
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
                        try:
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
                    # Use 20 spaces for indentation
                    print("Tipo: MATCH IDEA TO PARAGRAPH.");
                    # ... (Lógica TIPO 6 completa) ...
                    cajas_ideas = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_PARAGRAPH_CAJAS))
                    if not cajas_ideas: raise Exception("No cajas ideas.")
                    print(f"Encontradas {len(cajas_ideas)} ideas."); lista_ideas_texto = []; elementos_cajas = []
                    print("Recolectando ideas...");
                    for k, caja in enumerate(cajas_ideas):
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            idea_elem = caja.find_element(*sel.SELECTOR_PARAGRAPH_IDEA_TEXT); idea_texto = idea_elem.text.strip()
                            if idea_texto:
                                clave_unica_idea = f"{k}:{idea_texto}"
                                lista_ideas_texto.append(clave_unica_idea);
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
                        ideas_para_ia = [idea.split(":", 1)[1] for idea in lista_ideas_texto]
                        print(f"Enviando {len(ideas_para_ia)} ideas a IA...");
                        respuestas_lote_ia = ia_utils.obtener_numeros_parrafo_lote(contexto, ideas_para_ia, respuesta_anterior_incorrecta)
                        if not respuestas_lote_ia or len(respuestas_lote_ia) != len(elementos_cajas): raise Exception("Fallo IA (Parag Lote) o nº resp no coincide.")
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia
                    print(f"Respuestas a usar: {respuestas_lote_ia}"); print("Haciendo clics...")
                    exito_global = True
                    for numero_parrafo_ia, caja in zip(respuestas_lote_ia, elementos_cajas):
                        try:
                            selector_boton_num = (By.XPATH, f".//button[normalize-space()='{numero_parrafo_ia}']"); boton_a_clicar = caja.find_element(*selector_boton_num)
                            print(f"      Clic en '{numero_parrafo_ia}'..."); wait_long.until(EC.element_to_be_clickable(boton_a_clicar)); driver.execute_script("arguments[0].click();", boton_a_clicar); time.sleep(0.3)
                        except Exception as e: print(f"Error clic Parágrafo '{numero_parrafo_ia}': {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo al resolver Match Paragraph.")

                # --- TIPO 4: EMPAREJAR (REFACTORIZADO CON LISTA-SOLUCIÓN) ---
                elif tipo_pregunta == "TIPO_4_EMPAREJAR":
                    # Use 20 spaces for indentation
                    print("Tipo: EMPAREJAR PALABRAS.");
                    # ... (Lógica TIPO 4 completa) ...
                    exito_global = True; print("      Extrayendo definiciones (JS)...")
                    js_get_defs = f"return Array.from(document.querySelectorAll('{sel.SELECTOR_DEFINICIONES_AZULES_CSS}')).map(el => el.innerText.trim());"
                    try:
                        definiciones = driver.execute_script(js_get_defs); definiciones = [d.strip() for d in definiciones if d]
                        if not definiciones: raise Exception("JS no encontró texto def.")
                        map_texto_def_a_elemento = {}
                        spans_defs_selenium = wait_long.until(EC.presence_of_all_elements_located((sel.SELECTOR_DEFINICIONES_AZULES_XPATH)))
                        for s in spans_defs_selenium:
                            texto = s.text.strip();
                            if texto in definiciones: map_texto_def_a_elemento[texto] = s
                        if len(map_texto_def_a_elemento) != len(definiciones): print("Warn: No se mapearon elementos def.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo def: {e}")
                    print(f"      Definiciones encontradas: {definiciones}"); print("      Extrayendo palabras clave (en orden)...")
                    # --- ¡INICIO CORRECCIÓN TIPO 4 (JS Clean)! ---
                    js_get_keywords = f"let k=[];document.querySelectorAll('{sel.SELECTOR_FILAS_EMPAREJAR_CSS}').forEach(r=>{{let e=r.querySelector('{sel.SELECTOR_PALABRA_CLAVE_CSS}');if(e)k.push(e.innerText.replace(/_/g,'').replace(/:/g,'').replace(/'/g,'').replace(/\s+/g, ' ').trim());}});return k;"
                    # --- ¡FIN CORRECCIÓN TIPO 4! ---
                    try:
                        palabras_clave = driver.execute_script(js_get_keywords); palabras_clave = [p.strip() for p in palabras_clave if p]
                        if not palabras_clave: raise Exception("JS no encontró palabras clave.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo palabras: {e}")
                    print(f"      Palabras clave encontradas (en orden): {palabras_clave}");
                    titulo_limpio = pregunta_actual_texto.strip()
                    defs_limpias_sorted = sorted([d.strip() for d in definiciones])
                    clave_pregunta = f"T4:{titulo_limpio}||" + "|".join(defs_limpias_sorted)
                    if clave_pregunta in soluciones_correctas:
                        print("      SOLUCIÓN ENCONTRADA en memoria.");
                        lista_definiciones_ordenadas = soluciones_correctas[clave_pregunta]
                    else:
                        print("      IA (Emparejar)...")
                        pares_ia_temporal = ia_utils.obtener_emparejamientos(palabras_clave, definiciones)
                        if not pares_ia_temporal: raise Exception("IA (Emparejar) falló.")
                        lista_definiciones_ordenadas = []
                        for clave in palabras_clave:
                            if clave in pares_ia_temporal:
                                lista_definiciones_ordenadas.append(pares_ia_temporal[clave])
                            else:
                                print(f"Error: IA no devolvió clave '{clave}'"); raise Exception("Fallo mapeo IA T4")
                        preguntas_ya_vistas[clave_pregunta] = lista_definiciones_ordenadas
                    print(f"      Solución a aplicar (en orden): {lista_definiciones_ordenadas}"); print("      Clickeando en orden (Sistema de Cola)...")
                    for definicion_correcta in lista_definiciones_ordenadas:
                        elemento_origen = map_texto_def_a_elemento.get(definicion_correcta)
                        if not elemento_origen: print(f"Error: No WebElement para def '{definicion_correcta}'"); exito_global = False; continue
                        print(f"            Clic en '{definicion_correcta}'...");
                        try:
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", elemento_origen); time.sleep(0.3)
                            wait_long.until(EC.element_to_be_clickable(elemento_origen)).click(); print("                  Clic OK."); time.sleep(1.0)
                        except Exception as e: print(f"                  Error CRÍTICO (Click) en '{definicion_correcta}': {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo emparejar (Clic en orden).")

                # --- TIPO 5: MARK TRUE/FALSE (SINGLE) ---
                elif tipo_pregunta == "TIPO_5_TF_SINGLE":
                    # Use 20 spaces for indentation
                    print("Tipo: MARK TRUE/FALSE (Single).");
                    # --- ¡INICIO 3RA REFACTORIZACIÓN TIPO 5 (Global Selectors)! ---
                    try:
                        # 1. Usamos el TÍTULO como texto de la afirmación
                        texto_afirmacion = pregunta_actual_texto.strip()
                        if not texto_afirmacion: raise Exception("No texto afirmación (leído de título).")
                        
                        # 2. Buscamos los botones GLOBALMENTE (no relativo)
                        #    usando los selectores TIPO 5 que restauramos
                        boton_true = wait_long.until(EC.presence_of_element_located(sel.SELECTOR_MARK_TF_TRUE))
                        boton_false = wait_long.until(EC.presence_of_element_located(sel.SELECTOR_MARK_TF_FALSE))

                        print(f"      Afirmación (de Título): '{texto_afirmacion}'");
                        opciones_t5 = ["True", "False"]
                        titulo_limpio_t5 = texto_afirmacion.strip()
                        # --- INICIO MODIFICACIÓN HASH DE CONTEXTO ---
                        clave_pregunta = f"T5:{titulo_limpio_t5}||{contexto_hash}||" + "|".join(sorted(opciones_t5))
                        # --- FIN MODIFICACIÓN HASH DE CONTEXTO ---
                        
                        opciones_ya_vistas[clave_pregunta] = opciones_t5
                        if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA."); respuesta_tf_ia = soluciones_correctas[clave_pregunta]
                        else:
                            if clave_pregunta in preguntas_ya_vistas:
                                respuesta_anterior = preguntas_ya_vistas[clave_pregunta]; respuesta_tf_ia = "False" if respuesta_anterior == "True" else "True"
                                print(f"      WARN: Pregunta repetida (T5). Anterior: '{respuesta_anterior}'. Forzando: '{respuesta_tf_ia}'")
                            else: print("      IA (T/F)..."); respuesta_tf_ia = ia_utils.obtener_true_false(contexto, texto_afirmacion)
                            if respuesta_tf_ia: preguntas_ya_vistas[clave_pregunta] = respuesta_tf_ia
                        if not respuesta_tf_ia: raise Exception("IA (T/F) falló.")
                        print(f"      IA decidió: {respuesta_tf_ia}"); boton_a_clicar = boton_true if respuesta_tf_ia == "True" else boton_false
                        
                        print(f"      Clic en '{respuesta_tf_ia}'..."); 
                        wait_long.until(EC.element_to_be_clickable(boton_a_clicar)); 
                        driver.execute_script("arguments[0].click();", boton_a_clicar); time.sleep(0.3)
                    
                    except (NoSuchElementException, TimeoutException) as e: 
                        print(f"Error T/F (Single) elems: {e}"); 
                        raise Exception("Fallo resolver Mark T/F.")
                    except Exception as e: 
                        print(f"Error T/F (Single) lógica: {e}"); 
                        raise
                    # --- ¡FIN 3RA REFACTORIZACIÓN TIPO 5! ---

                # --- TIPO 7: ANSWER THE QUESTION (OM in a Card) ---
                elif tipo_pregunta == "TIPO_7_OM_CARD":
                    # Use 20 spaces for indentation
                    print("Tipo: ANSWER THE QUESTION (OM in Card).");
                    # ... (Lógica TIPO 7 completa) ...
                    cajas_preguntas = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_ANSWER_Q_CAJAS))
                    if not cajas_preguntas: raise Exception("No cajas 'Answer Question'.")
                    print(f"Encontradas {len(cajas_preguntas)} tarjetas."); lista_de_tareas = []; lista_de_preguntas = []; elementos_cajas = []
                    print("Recolectando tareas...");
                    for k, caja in enumerate(cajas_preguntas):
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            real_pregunta_elem = caja.find_element(*sel.SELECTOR_ANSWER_Q_TEXTO); real_pregunta = real_pregunta_elem.text.strip()
                            if not real_pregunta: raise Exception(f"Texto vacío tarjeta {k+1}.")
                            opciones_elementos = caja.find_elements(*sel.SELECTOR_ANSWER_Q_BOTONES); opciones = [e.text.strip() for e in opciones_elementos if e.text.strip()]
                            if not opciones: raise Exception(f"No opciones tarjeta {k+1}.")
                            clave_unica_pregunta = f"{k}:{real_pregunta}"
                            print(f"      Tarea {k+1}: '{real_pregunta}' Ops: {opciones}");
                            lista_de_tareas.append({"pregunta": real_pregunta, "opciones": opciones});
                            lista_de_preguntas.append(clave_unica_pregunta);
                            elementos_cajas.append(caja)
                        except Exception as e: print(f"Error procesando tarjeta {k+1}: {e}"); raise
                    if not lista_de_tareas: raise Exception("No tareas recolectadas.")
                    clave_pregunta = "|".join([p.strip() for p in lista_de_preguntas])
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
                        try:
                            opciones_elementos_caja = caja.find_elements(*sel.SELECTOR_ANSWER_Q_BOTONES); boton_encontrado = None
                            for b in opciones_elementos_caja:
                                if b.text.strip() == respuesta_ia: boton_encontrado = b; break
                            if boton_encontrado: print(f"      Clic en '{boton_encontrado.text}'..."); driver.execute_script("arguments[0].click();", boton_encontrado); time.sleep(0.3)
                            else: print(f"Error CRÍTICO: Botón '{respuesta_ia}' no encontrado."); exito_global = False
                        except Exception as e: print(f"Error bucle clics T7: {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo al resolver 'Answer Question'.")

                # --- TIPO 8: EMPAREJAR IMAGEN (REFACTORIZADO CON LISTA-SOLUCIÓN) ---
                elif tipo_pregunta == "TIPO_8_IMAGEN":
                    # Use 20 spaces for indentation
                    print("Tipo: EMPAREJAR IMAGEN (TIPO 8).");
                    # ... (Lógica TIPO 8 completa) ...
                    exito_global = True; print("      Extrayendo definiciones (JS)...")
                    js_get_defs = f"return Array.from(document.querySelectorAll('{sel.SELECTOR_DEFINICIONES_AZULES_CSS}')).map(el => el.innerText.trim());"
                    try:
                        definiciones = driver.execute_script(js_get_defs); definiciones = [d.strip() for d in definiciones if d]
                        if not definiciones: raise Exception("JS no encontró texto def.")
                        map_texto_def_a_elemento = {}
                        spans_defs_selenium = wait_long.until(EC.presence_of_all_elements_located((sel.SELECTOR_DEFINICIONES_AZULES_XPATH)))
                        for s in spans_defs_selenium:
                            texto = s.text.strip();
                            if texto in definiciones: map_texto_def_a_elemento[texto] = s
                        if len(map_texto_def_a_elemento) != len(definiciones): print("Warn: No se mapearon elementos def.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo def: {e}")
                    print(f"      Definiciones encontradas: {definiciones}");
                    print("      Extrayendo imágenes clave (en orden) [Usando SRC/GUID]...");
                    palabras_clave_src = []
                    try:
                        filas_imagenes = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_IMAGEN_EMPAREJAR))
                        if not filas_imagenes: raise Exception("Selenium no encontró filas de imagen TIPO 8.")
                        for i, fila in enumerate(filas_imagenes):
                            img = fila.find_element(By.TAG_NAME, "img")
                            src = img.get_attribute("src")
                            if src:
                                nombre_archivo = src.split('/')[-1].split('?')[0].split('.')[0]
                                palabras_clave_src.append(nombre_archivo.strip())
                            else:
                                print(f"      Error: Fila {i} TIPO 8 sin 'src'.")
                                palabras_clave_src.append(f"imagen_error_{i}")
                        if not palabras_clave_src: raise Exception("No se extrajeron 'src' de imágenes.")
                    except (NoSuchElementException, TimeoutException) as e:
                        raise Exception(f"Error extrayendo 'src' de img TIPO 8: {e}")
                    palabras_clave = palabras_clave_src
                    print(f"      Imágenes clave encontradas (en orden): {palabras_clave}");
                    titulo_limpio = pregunta_actual_texto.strip()
                    defs_limpias_sorted = sorted([d.strip() for d in definiciones])
                    clave_pregunta = f"T8:{titulo_limpio}||" + "|".join(defs_limpias_sorted)
                    print(f"DEBUG: Generated Key T8: '{clave_pregunta}'") # DEBUG
                    if clave_pregunta in soluciones_correctas:
                        print("      SOLUCIÓN ENCONTRADA en memoria.");
                        lista_definiciones_ordenadas = soluciones_correctas[clave_pregunta]
                    else:
                        print("      IA (Emparejar)...")
                        pares_ia_temporal = ia_utils.obtener_emparejamientos(palabras_clave, definiciones)
                        if not pares_ia_temporal: raise Exception("IA (Emparejar) falló.")
                        lista_definiciones_ordenadas = []
                        for clave in palabras_clave:
                            clave_encontrada = None
                            if clave in pares_ia_temporal: clave_encontrada = clave
                            elif clave.strip() in pares_ia_temporal: clave_encontrada = clave.strip()
                            elif clave + " " in pares_ia_temporal: clave_encontrada = clave + " "
                            if clave_encontrada:
                                 lista_definiciones_ordenadas.append(pares_ia_temporal[clave_encontrada])
                            else:
                                print(f"Error: IA no devolvió clave '{clave}' (ni variantes)"); raise Exception("Fallo mapeo IA T8")
                        preguntas_ya_vistas[clave_pregunta] = lista_definiciones_ordenadas
                    print(f"      Solución a aplicar (en orden): {lista_definiciones_ordenadas}"); print("      Clickeando en orden (Sistema de Cola)...")
                    for definicion_correcta in lista_definiciones_ordenadas:
                        elemento_origen = map_texto_def_a_elemento.get(definicion_correcta)
                        if not elemento_origen: elemento_origen = map_texto_def_a_elemento.get(definicion_correcta.strip())
                        if not elemento_origen: print(f"Error: No WebElement para def '{definicion_correcta}'"); exito_global = False; continue
                        print(f"            Clic en '{definicion_correcta}'...");
                        try:
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", elemento_origen); time.sleep(0.3)
                            wait_long.until(EC.element_to_be_clickable(elemento_origen)).click(); print("                  Clic OK."); time.sleep(1.0)
                        except Exception as e: print(f"                  Error CRÍTICO (Click) en '{definicion_correcta}': {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo emparejar (Clic en orden).")

                # --- TIPO 9: AUDIO (ADIVINAR Y APRENDER) ---
                elif tipo_pregunta == "TIPO_9_AUDIO":
                    # Use 20 spaces for indentation
                    print("Tipo: AUDIO (TIPO 9).");
                    opciones_elementos = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_OPCIONES))
                    opciones = [e.text.strip() for e in opciones_elementos if e.text and e.is_displayed()]
                    if not opciones: raise Exception("No opciones visibles (TIPO 9).")
                    
                    # --- INICIO: HASHING por AUDIO para TIPO_9 ---
                    audio_hash = "" # Reseteamos por si acaso
                    try:
                        audio_elem = driver.find_element(*sel.SELECTOR_AUDIO)
                        audio_src = audio_elem.get_attribute("src")
                        if audio_src:
                            # Extraemos el GUID del audio
                            nombre_archivo = audio_src.split('/')[-1].split('?')[0]
                            audio_hash = f"AUD:{nombre_archivo}"
                            print(f"      Audio detectado. Añadiendo hash a la clave: {audio_hash}")
                    except Exception as e_aud:
                        print(f"      WARN: No se pudo extraer hash de audio: {e_aud}")
                    # --- FIN: HASHING por AUDIO ---
                    
                    titulo_limpio_t9 = pregunta_actual_texto.strip() if "pregunta_sin_titulo" not in pregunta_actual_texto else contexto[:150]
                    opciones_limpias_sorted_t9 = sorted([o.strip() for o in opciones])
                    # --- INICIO MODIFICACIÓN HASH DE CONTEXTO ---
                    clave_pregunta = f"T9:{titulo_limpio_t9}||{contexto_hash}||{audio_hash}||" + "|".join(opciones_limpias_sorted_t9)
                    # --- FIN MODIFICACIÓN HASH DE CONTEXTO ---
                    
                    print(f"Resolviendo: {pregunta_actual_texto}\nOpciones: {opciones}");
                    opciones_ya_vistas[clave_pregunta] = opciones
                    if clave_pregunta in soluciones_correctas:
                        print("      SOLUCIÓN ENCONTRADA.");
                        respuesta_adivinada = soluciones_correctas[clave_pregunta]
                    else:
                        opciones_para_adivinar = list(opciones)
                        if clave_pregunta in preguntas_ya_vistas:
                            respuesta_anterior = preguntas_ya_vistas[clave_pregunta];
                            print(f"      WARN: Pregunta (T9) repetida. Anterior: ('{respuesta_anterior}').")
                            if respuesta_anterior in opciones_para_adivinar:
                                opciones_para_adivinar.remove(respuesta_anterior);
                                print(f"      Reintentando con: {opciones_para_adivinar}")
                            if not opciones_para_adivinar:
                                opciones_para_adivinar = list(opciones)
                        print("      Adivinando respuesta (Audio)...");
                        respuesta_adivinada = random.choice(opciones_para_adivinar)
                        preguntas_ya_vistas[clave_pregunta] = respuesta_adivinada
                    print(f"Bot decidió: '{respuesta_adivinada}'"); boton_encontrado = None
                    opciones_visibles = driver.find_elements(*sel.SELECTOR_OPCIONES)
                    for b in opciones_visibles:
                        t_b = ' '.join(b.text.split()); t_ia = ' '.join(respuesta_adivinada.split())
                        if t_b == t_ia: boton_encontrado = b; break
                    if boton_encontrado: print(f"Clic en '{boton_encontrado.text}'..."); driver.execute_script("arguments[0].scrollIntoView(true);",boton_encontrado); time.sleep(0.2); boton_encontrado.click(); time.sleep(0.5)
                    else: raise Exception(f"Botón '{respuesta_adivinada}' no encontrado.")

                # --- LÓGICA TIPO 10 (LOTE) ---
                elif tipo_pregunta == "TIPO_10_ESCRIBIR":
                    # Use 20 spaces for indentation
                    print("Tipo: ESCRIBIR PALABRA ORDENADA (TIPO 10 - Lote).");
                    # ... (Lógica TIPO 10 completa) ...
                    letras_elems = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_LETRAS_DESORDENADAS))
                    input_elems = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_INPUT_ESCRIBIR))
                    if not letras_elems or not input_elems or len(letras_elems) != len(input_elems):
                        raise Exception(f"Error TIPO 10: No coinciden elementos de letras ({len(letras_elems)}) e inputs ({len(input_elems)}).")
                    num_tareas = len(letras_elems)
                    print(f"Encontradas {num_tareas} tareas TIPO 10.")
                    lista_de_tareas_escribir = []
                    lista_palabras_desordenadas_raw = []
                    for i in range(num_tareas):
                        letras_desordenadas_raw = letras_elems[i].text.strip()
                        input_elem_actual = input_elems[i]
                        if not letras_desordenadas_raw:
                            print(f"WARN TIPO 10: Tarea {i+1} sin letras. Omitiendo.")
                            continue
                        letras_limpias_clave = "".join(letras_desordenadas_raw.split('/')).replace(" ", "").strip().upper()
                        print(f"      Tarea {i+1}: Letras='{letras_desordenadas_raw}' (Clave='{letras_limpias_clave}')")
                        lista_de_tareas_escribir.append({"letras_raw": letras_desordenadas_raw,"letras_clave": letras_limpias_clave,"input_elem": input_elem_actual})
                        lista_palabras_desordenadas_raw.append(letras_desordenadas_raw)
                    if not lista_de_tareas_escribir: raise Exception("No se recolectaron tareas TIPO 10 válidas.")
                    titulo_limpio = pregunta_actual_texto.strip()
                    claves_ordenadas_str = "|".join(sorted([t["letras_clave"] for t in lista_de_tareas_escribir]))
                    clave_pregunta = f"T10_BATCH:{titulo_limpio}||{claves_ordenadas_str}"
                    respuestas_lote_ia = []
                    if clave_pregunta in soluciones_correctas:
                        print("      SOLUCIÓN LOTE TIPO 10 ENCONTRADA en memoria.");
                        respuestas_lote_ia = soluciones_correctas[clave_pregunta]
                    else:
                        print("      Llamando a IA (Ordenar Palabra Lote)...")
                        respuestas_ia_temp = ia_utils.obtener_palabras_ordenadas_lote(lista_palabras_desordenadas_raw)
                        if not respuestas_ia_temp or len(respuestas_ia_temp) != len(lista_de_tareas_escribir):
                            raise Exception("Fallo IA (Ordenar Lote) o nº resp no coincide.")
                        respuestas_lote_ia = respuestas_ia_temp
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia
                    print(f"Palabras ordenadas a escribir: {respuestas_lote_ia}")
                    exito_global = True
                    if len(respuestas_lote_ia) != len(lista_de_tareas_escribir):
                        print("Error crítico T10: Número de respuestas IA no coincide con tareas.")
                        raise Exception("Fallo TIPO 10 - Mismatch respuestas/tareas")
                    for palabra_correcta, tarea in zip(respuestas_lote_ia, lista_de_tareas_escribir):
                        try:
                            input_actual = tarea["input_elem"]
                            print(f"      Escribiendo '{palabra_correcta}'...");
                            wait_short.until(EC.element_to_be_clickable(input_actual))
                            input_actual.clear()
                            input_actual.send_keys(palabra_correcta)
                            time.sleep(0.3)
                        except Exception as e:
                            print(f"Error al escribir en input TIPO 10: {e}");
                            exito_global = False; break
                    if not exito_global: raise Exception("Fallo al escribir en inputs TIPO 10.")
                
                # --- ¡INICIO LÓGICA TIPO 11! ---
                # --- LÓGICA TIPO 11 (ESCRIBIR OPCIONES) ---
                elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES":
                    # Use 20 spaces for indentation
                    print("Tipo: ESCRIBIR OPCIONES (TIPO 11 - Lote).");
                    input_elems = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_INPUT_ESCRIBIR))
                    if not input_elems:
                        raise Exception("Error TIPO 11: No se encontraron inputs.")
                    
                    num_tareas = len(input_elems)
                    print(f"Encontradas {num_tareas} tareas TIPO 11.")
                    lista_de_tareas_escribir = [] # Reusamos variable de T10
                    lista_frases_t11 = [] # Nueva lista para guardar las frases
                    
                    for i, input_elem_actual in enumerate(input_elems):
                        try:
                            # Use 24 spaces for indentation
                            # Buscamos la frase relativa al input
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", input_elem_actual); time.sleep(0.1)
                            frase_elem = input_elem_actual.find_element(*sel.SELECTOR_FRASE_T11)
                            frase_texto = frase_elem.text.strip()
                            if not frase_texto: raise Exception("Frase T11 vacía.")
                            
                            # Reemplazamos el input (que está vacío) con '___'
                            # Asumimos que el input está al final o donde está el <input>
                            frase_para_ia = frase_texto + " ___" # Simplificación
                            print(f"      Tarea {i+1}: Frase='{frase_para_ia}'")
                            
                            lista_de_tareas_escribir.append({"frase": frase_para_ia, "input_elem": input_elem_actual})
                            lista_frases_t11.append(frase_para_ia) # Para aprendizaje

                        except (NoSuchElementException, TimeoutException) as e_t11:
                             # Use 24 spaces for indentation
                             print(f"WARN TIPO 11: Tarea {i+1} sin frase. Omitiendo. ({e_t11})")
                             continue

                    if not lista_de_tareas_escribir: raise Exception("No se recolectaron tareas TIPO 11 válidas.")
                    
                    titulo_limpio = pregunta_actual_texto.strip()
                    frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                    # --- INICIO MODIFICACIÓN HASH DE CONTEXTO ---
                    clave_pregunta = f"T11_BATCH:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"
                    # --- FIN MODIFICACIÓN HASH DE CONTEXTO ---

                    respuestas_lote_ia = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN LOTE TIPO 11 ENCONTRADA en memoria.");
                        respuestas_lote_ia = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 24 spaces for indentation
                        print("      Llamando a IA (Escribir Opciones Lote)...")
                        # Pasamos el título como contexto clave (IN, ON, AT)
                        tareas_para_ia = [{"frase": t["frase"]} for t in lista_de_tareas_escribir]
                        respuestas_ia_temp = ia_utils.obtener_respuestas_escribir_opciones_lote(contexto, pregunta_actual_texto, tareas_para_ia)
                        
                        if not respuestas_ia_temp or len(respuestas_ia_temp) != len(lista_de_tareas_escribir):
                            # Use 28 spaces for indentation
                            raise Exception("Fallo IA (Escribir Opciones Lote) o nº resp no coincide.")
                        respuestas_lote_ia = respuestas_ia_temp
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia
                    
                    print(f"Palabras (Opciones) a escribir: {respuestas_lote_ia}")
                    exito_global = True
                    if len(respuestas_lote_ia) != len(lista_de_tareas_escribir):
                        # Use 24 spaces for indentation
                        print("Error crítico T11: Número de respuestas IA no coincide con tareas.")
                        raise Exception("Fallo TIPO 11 - Mismatch respuestas/tareas")
                    
                    for palabra_correcta, tarea in zip(respuestas_lote_ia, lista_de_tareas_escribir):
                        try:
                            # Use 28 spaces for indentation
                            input_actual = tarea["input_elem"]
                            print(f"      Escribiendo '{palabra_correcta}'...");
                            wait_short.until(EC.element_to_be_clickable(input_actual))
                            input_actual.clear()
                            input_actual.send_keys(palabra_correcta)
                            time.sleep(0.3)
                        except Exception as e:
                            # Use 28 spaces for indentation
                            print(f"Error al escribir en input TIPO 11: {e}");
                            exito_global = False; break
                    if not exito_global: raise Exception("Fallo al escribir en inputs TIPO 11.")
                # --- ¡FIN LÓGICA TIPO 11! ---

                # --- TIPO DEFAULT: OPCIÓN MÚLTIPLE ---
                elif tipo_pregunta == "TIPO_DEFAULT_OM":
                    # Use 20 spaces for indentation
                    print("Tipo: OPCIÓN MÚLTIPLE (Default).");
                    opciones_elementos = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_OPCIONES))
                    opciones = [e.text.strip() for e in opciones_elementos if e.text and e.is_displayed()]
                    if not opciones: raise Exception("No opciones visibles.")
                    
                    # --- INICIO: HASHING por IMAGEN para DEFAULT_OM ---
                    imagen_hash = "" # Reseteamos por si acaso
                    try:
                        # Intentamos encontrar imágenes dentro del área principal de la pregunta
                        imagenes_en_pregunta = driver.find_elements(By.XPATH, "//div[contains(@class,'card')]//img")
                        if imagenes_en_pregunta:
                            # Usamos la primera imagen encontrada
                            img_src = imagenes_en_pregunta[0].get_attribute("src")
                            if img_src:
                                # Extraemos el GUID de la imagen (ej: 'image-guid-12345.png')
                                nombre_archivo = img_src.split('/')[-1].split('?')[0]
                                imagen_hash = f"IMG:{nombre_archivo}"
                                print(f"      Imagen detectada. Añadiendo hash a la clave: {imagen_hash}")
                    except Exception as e_img:
                        print(f"      WARN: No se pudo extraer hash de imagen: {e_img}")
                    # --- FIN: HASHING por IMAGEN ---

                    titulo_limpio_def = pregunta_actual_texto.strip() if "pregunta_sin_titulo" not in pregunta_actual_texto else contexto[:150]
                    opciones_limpias_sorted_def = sorted([o.strip() for o in opciones])
                    # --- INICIO MODIFICACIÓN HASH DE CONTEXTO ---
                    clave_pregunta = f"DEFAULT:{titulo_limpio_def}||{contexto_hash}||{imagen_hash}||" + "|".join(opciones_limpias_sorted_def)
                    # --- FIN MODIFICACIÓN HASH DE CONTEXTO ---
                    
                    print(f"Resolviendo: {pregunta_actual_texto}\nOpciones: {opciones}");
                    opciones_ya_vistas[clave_pregunta] = opciones
                    if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA."); respuesta_ia = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 24 spaces for indentation
                        opciones_para_ia = list(opciones)
                        if clave_pregunta in preguntas_ya_vistas:
                            # Use 28 spaces for indentation
                            respuesta_anterior = preguntas_ya_vistas[clave_pregunta]; print(f"      WARN: Pregunta repetida (Default). Anterior: ('{respuesta_anterior}').")
                            if respuesta_anterior in opciones_para_ia: opciones_para_ia.remove(respuesta_anterior); print(f"      Reintentando con: {opciones_para_ia}")
                            if not opciones_para_ia: print("      ERROR: Se agotaron opciones."); opciones_para_ia = list(opciones)
                        print("IA (OM)..."); respuesta_ia = ia_utils.obtener_respuesta_opcion_multiple(contexto, pregunta, opciones_para_ia)
                        if not respuesta_ia: raise Exception("IA (OM) falló.")
                        preguntas_ya_vistas[clave_pregunta] = respuesta_ia
                    print(f"IA decidió: '{respuesta_ia}'"); boton_encontrado = None
                    opciones_visibles = driver.find_elements(*sel.SELECTOR_OPCIONES)
                    for b in opciones_visibles:
                        # Use 24 spaces for indentation
                        t_b = ' '.join(b.text.split()); t_ia = ' '.join(respuesta_ia.split())
                        if t_b == t_ia: boton_encontrado = b; break
                    if boton_encontrado: print(f"Clic en '{boton_encontrado.text}'..."); driver.execute_script("arguments[0].scrollIntoView(true);",boton_encontrado); time.sleep(0.2); boton_encontrado.click(); time.sleep(0.5)
                    else: raise Exception(f"Botón '{respuesta_ia}' no encontrado.")
                # --- FIN TIPOS ---

                # --- Común: CHECK y OK ---
                print("Clic CHECK...");
                boton_check = wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_CHECK))
                boton_check.click(); time.sleep(0.5)

                # --- LÓGICA DE APRENDIZAJE ---
                print("Esperando modal de respuesta...")
                boton_ok = wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_OK))
                try:
                    # Use 20 spaces for indentation
                    titulo_modal = driver.find_element(*sel.SELECTOR_MODAL_TITULO).text.lower()

                    # --- CASO 1: INCORRECTA ---
                    if "incorrect" in titulo_modal or "oops" in titulo_modal:
                        # Use 24 spaces for indentation
                        respuesta_fue_incorrecta = True
                        print("      Respuesta INCORRECTA detectada. Buscando solución...")
                        contenido_modal = driver.find_element(*sel.SELECTOR_MODAL_CONTENIDO).text
                        preguntas_para_ia = None; opciones_para_ia = None; solucion_aprendida = None

                        # 1. Preparar datos (Claves corregidas y limpias)
                        if tipo_pregunta == "TIPO_6_PARAGRAPH":
                            # Use 28 spaces for indentation
                            clave_pregunta = "|".join([p.strip() for p in lista_ideas_texto]); preguntas_para_ia = [idea.split(":", 1)[1] for idea in lista_ideas_texto]
                        elif tipo_pregunta == "TIPO_7_OM_CARD":
                            # Use 28 spaces for indentation
                            clave_pregunta = "|".join([p.strip() for p in lista_de_preguntas]); preguntas_para_ia = [preg.split(":", 1)[1] for preg in lista_de_preguntas]
                        elif tipo_pregunta == "TIPO_1_ORDENAR":
                            # Use 28 spaces for indentation
                            clave_pregunta = "|".join([p.strip() for p in lista_de_claves_individuales]); preguntas_para_ia = lista_de_tareas_ordenar
                        elif tipo_pregunta == "TIPO_2_COMPLETAR":
                            # Use 28 spaces for indentation
                            titulo_limpio = pregunta_actual_texto.strip()
                            # --- INICIO MODIFICACIÓN HASH DE CONTEXTO ---
                            clave_pregunta = f"T2_BATCH:{titulo_limpio}||{contexto_hash}";
                            # --- FIN MODIFICACIÓN HASH DE CONTEXTO ---
                            preguntas_para_ia = lista_de_tareas_completar
                        elif tipo_pregunta == "TIPO_3_TF_MULTI":
                            # Use 28 spaces for indentation
                            clave_pregunta = "|".join([p.strip() for p in lista_afirmaciones_texto]); preguntas_para_ia = [afirm.split(":", 1)[1] for afirm in lista_afirmaciones_texto]
                        elif (tipo_pregunta == "TIPO_DEFAULT_OM" or tipo_pregunta == "TIPO_9_AUDIO"):
                            # Use 28 spaces for indentation
                            titulo_limpio = pregunta_actual_texto.strip() if "pregunta_sin_titulo" not in pregunta_actual_texto else contexto[:150]
                            current_opciones = []
                            try:
                                # Use 32 spaces for indentation
                                current_opciones = opciones # Usamos la variable 'opciones' guardada
                            except:
                                # Use 32 spaces for indentation
                                print(f"WARN Learn Prep: No se pudieron leer opciones para {tipo_pregunta}")
                            if current_opciones:
                                # Use 32 spaces for indentation
                                opciones_limpias_sorted = sorted(current_opciones)
                                prefix = "T9" if tipo_pregunta == "TIPO_9_AUDIO" else "DEFAULT"
                                # --- INICIO MODIFICACIÓN HASH DE CONTEXTO (APRENDIZAJE) ---
                                hash_extra = ""
                                if tipo_pregunta == "TIPO_9_AUDIO": hash_extra = audio_hash
                                else: hash_extra = imagen_hash
                                clave_pregunta = f"{prefix}:{titulo_limpio}||{contexto_hash}||{hash_extra}||" + "|".join(opciones_limpias_sorted)
                                # --- FIN MODIFICACIÓN HASH DE CONTEXTO (APRENDIZAJE) ---
                                opciones_para_ia = current_opciones 
                                print(f"      Preparando aprendizaje para {tipo_pregunta}. Clave: {clave_pregunta[:50]}...")
                            else:
                                # Use 32 spaces for indentation
                                print(f"WARN Learn Prep: No hay opciones disponibles para {tipo_pregunta}")
                                clave_pregunta = None
                        elif tipo_pregunta == "TIPO_5_TF_SINGLE":
                            # Use 28 spaces for indentation
                            titulo_limpio = pregunta_actual_texto.strip()
                            opciones_t5 = ["True", "False"]
                            # --- INICIO MODIFICACIÓN HASH DE CONTEXTO ---
                            clave_pregunta = f"T5:{titulo_limpio}||{contexto_hash}||" + "|".join(sorted(opciones_t5))
                            # --- FIN MODIFICACIÓN HASH DE CONTEXTO ---
                            opciones_para_ia = opciones_t5
                            print(f"      Preparando aprendizaje para TIPO 5. Clave: {clave_pregunta[:50]}...")
                        elif tipo_pregunta == "TIPO_10_ESCRIBIR":
                             # Use 28 spaces for indentation
                             titulo_limpio = pregunta_actual_texto.strip()
                             claves_ordenadas_str = "|".join(sorted([t["letras_clave"] for t in lista_de_tareas_escribir]))
                             clave_pregunta = f"T10_BATCH:{titulo_limpio}||{claves_ordenadas_str}"
                             preguntas_para_ia = lista_palabras_desordenadas_raw
                             print(f"      Preparando aprendizaje para TIPO 10. Clave: {clave_pregunta[:50]}...")
                        
                        # --- ¡INICIO APRENDIZAJE TIPO 11 (Incorrecto)! ---
                        elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES":
                             # Use 28 spaces for indentation
                             titulo_limpio = pregunta_actual_texto.strip()
                             frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                             clave_pregunta = f"T11_BATCH:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"
                             preguntas_para_ia = [{"frase": f} for f in lista_frases_t11] # Usamos la lista de frases
                             print(f"      Preparando aprendizaje para TIPO 11. Clave: {clave_pregunta[:50]}...")
                        # --- ¡FIN APRENDIZAJE TIPO 11! ---

                        elif tipo_pregunta == "TIPO_4_EMPAREJAR" or tipo_pregunta == "TIPO_8_IMAGEN":
                             # Use 28 spaces for indentation
                             titulo_limpio = pregunta_actual_texto.strip()
                             defs_limpias_sorted = sorted([d.strip() for d in definiciones])
                             tipo_num_str = ''.join(filter(str.isdigit, tipo_pregunta))
                             if tipo_num_str:
                                 # Use 32 spaces for indentation
                                 clave_pregunta = f"T{tipo_num_str}:{titulo_limpio}||" + "|".join(defs_limpias_sorted)
                                 print(f"      Preparando aprendizaje para TIPO {tipo_num_str}. Clave: {clave_pregunta[:50]}...")
                             else:
                                 # Use 32 spaces for indentation
                                 print(f"      ERROR: No se pudo extraer número de tipo {tipo_pregunta} para clave aprendizaje.")
                                 clave_pregunta = None

                        # 2. Extraer solución
                        if tipo_pregunta in ["TIPO_1_ORDENAR", "TIPO_2_COMPLETAR", "TIPO_3_TF_MULTI", "TIPO_6_PARAGRAPH", "TIPO_7_OM_CARD", "TIPO_10_ESCRIBIR", "TIPO_11_ESCRIBIR_OPCIONES"] and clave_pregunta and contenido_modal:
                            # Use 28 spaces for indentation
                            solucion_lista_ordenada = None
                            if preguntas_para_ia is None:
                                # Use 32 spaces for indentation
                                print("      ERROR Aprendizaje Lote: 'preguntas_para_ia' no está definida.")
                            elif tipo_pregunta == "TIPO_3_TF_MULTI":
                                # Use 32 spaces for indentation
                                print("      Enviando texto a IA (Lote T/F) para extraer solución..."); solucion_lista_ordenada = ia_utils.extraer_solucion_lote_tf(contenido_modal, preguntas_para_ia)
                            elif tipo_pregunta == "TIPO_2_COMPLETAR":
                                # Use 32 spaces for indentation
                                print("      Enviando texto a IA (Lote Completar) para extraer solución...");
                                tareas_aprendizaje_t2 = [{"frase": t["frase"], "opciones": t["opciones"]} for t in preguntas_para_ia]
                                solucion_lista_ordenada = ia_utils.extraer_solucion_lote_completar(contenido_modal, tareas_aprendizaje_t2)
                            elif tipo_pregunta == "TIPO_1_ORDENAR":
                                # Use 32 spaces for indentation
                                print("      Enviando texto a IA (Ordenar Lote) para extraer solución...")
                                solucion_lote_ordenar = []
                                exito_aprendizaje_lote = True
                                for i, tarea_ind in enumerate(preguntas_para_ia):
                                    # Use 36 spaces for indentation
                                    print(f"      IA (Aprendizaje Ord) para Tarea {i+1}...")
                                    sol_individual = ia_utils.extraer_solucion_ordenar(contenido_modal, tarea_ind["frases"])
                                    if not sol_individual:
                                        # Use 40 spaces for indentation
                                        print(f"      IA (Aprendizaje Ord) Tarea {i+1} falló.")
                                        exito_aprendizaje_lote = False; break
                                    solucion_lote_ordenar.append(sol_individual)
                                if exito_aprendizaje_lote: solucion_lista_ordenada = solucion_lote_ordenar
                                else: solucion_lista_ordenada = None
                            elif tipo_pregunta == "TIPO_10_ESCRIBIR":
                                # Use 32 spaces for indentation
                                print("      Enviando texto a IA (Lote Escribir) para extraer solución...");
                                solucion_lista_ordenada = ia_utils.extraer_solucion_lote_escribir(contenido_modal, preguntas_para_ia)
                            
                            # --- ¡INICIO APRENDIZAJE TIPO 11 (Incorrecto)! ---
                            elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES":
                                # Use 32 spaces for indentation
                                print("      Enviando texto a IA (Lote Escribir Opciones) para extraer solución...");
                                # preguntas_para_ia ya es [{"frase": ...}]
                                solucion_lista_ordenada = ia_utils.extraer_solucion_lote_escribir_opciones(contenido_modal, preguntas_para_ia)
                            # --- ¡FIN APRENDIZAJE TIPO 11! ---

                            else: # Para T6 y T7
                                # Use 32 spaces for indentation
                                print("      Enviando texto a IA (Lote Genérico) para extraer solución..."); solucion = ia_utils.extraer_solucion_del_error(contenido_modal, preguntas_para_ia)
                                if solucion:
                                    # Use 36 spaces for indentation
                                    solucion_lista_ordenada_temp = []
                                    mapeo_fallido = False
                                    for p_limpio in preguntas_para_ia:
                                        # Use 40 spaces for indentation
                                        if p_limpio in solucion:
                                            # Use 44 spaces for indentation
                                            solucion_lista_ordenada_temp.append(str(solucion[p_limpio]).strip())
                                        else:
                                            # Use 44 spaces for indentation
                                            p_alt1 = p_limpio + " "; p_alt2 = p_limpio.strip()
                                            if p_alt1 in solucion: solucion_lista_ordenada_temp.append(str(solucion[p_alt1]).strip())
                                            elif p_alt2 in solucion: solucion_lista_ordenada_temp.append(str(solucion[p_alt2]).strip())
                                            else:
                                                # Use 48 spaces for indentation
                                                print(f"      IA (Lote Genérico) no pudo mapear solución para: '{p_limpio}'"); mapeo_fallido = True; break
                                    if not mapeo_fallido: solucion_lista_ordenada = solucion_lista_ordenada_temp
                                    else: solucion_lista_ordenada = None
                                else: solucion_lista_ordenada = None

                            if solucion_lista_ordenada:
                                # Use 32 spaces for indentation
                                print(f"      ¡SOLUCIÓN LOTE APRENDIDA! -> {solucion_lista_ordenada}");
                                if tipo_pregunta == "TIPO_2_COMPLETAR":
                                    # Use 36 spaces for indentation
                                    frases_clave = [t["frase"] for t in preguntas_para_ia]
                                    solucion_aprendida = dict(zip(frases_clave, solucion_lista_ordenada))
                                    print(f"      Guardando como DICT: {solucion_aprendida}")
                                else:
                                    # Use 36 spaces for indentation
                                    solucion_aprendida = solucion_lista_ordenada
                            else:
                                # Use 32 spaces for indentation
                                print("      IA (Lote) no pudo extraer o validar la solución.")

                        elif (tipo_pregunta == "TIPO_4_EMPAREJAR" or tipo_pregunta == "TIPO_8_IMAGEN") and clave_pregunta and contenido_modal:
                            # Use 28 spaces for indentation
                             tipo_num_str = ''.join(filter(str.isdigit, tipo_pregunta))
                             print(f"      Enviando texto a IA (Aprendizaje Emparejar TIPO {tipo_num_str}) para extraer solución...");
                             try:
                                # Use 32 spaces for indentation
                                dict_solucion = ia_utils.extraer_solucion_emparejar(contenido_modal, palabras_clave, definiciones)
                                if dict_solucion:
                                    # Use 36 spaces for indentation
                                    solucion_aprendida_lista = []
                                    for clave in palabras_clave:
                                        # Use 40 spaces for indentation
                                        clave_encontrada = None
                                        if clave in dict_solucion: clave_encontrada = clave
                                        elif clave.strip() in dict_solucion: clave_encontrada = clave.strip()
                                        elif clave + " " in dict_solucion: clave_encontrada = clave + " "
                                        if clave_encontrada:
                                             # Use 44 spaces for indentation
                                             solucion_aprendida_lista.append(dict_solucion[clave_encontrada])
                                        else:
                                            # Use 44 spaces for indentation
                                            print(f"      ERROR APRENDIZAJE: No se encontró la clave '{clave}' (ni variantes) en el dict de la IA.")
                                            raise Exception("Fallo al mapear dict de aprendizaje a lista.")
                                    solucion_aprendida = solucion_aprendida_lista
                                else:
                                    # Use 36 spaces for indentation
                                    solucion_aprendida = None
                             except NameError:
                                # Use 32 spaces for indentation
                                print("      Error: 'palabras_clave' o 'definiciones' no definidas. No se puede aprender.")
                                solucion_aprendida = None

                        elif tipo_pregunta in ["TIPO_5_TF_SINGLE", "TIPO_DEFAULT_OM", "TIPO_9_AUDIO"] and clave_pregunta and contenido_modal:
                            # Use 28 spaces for indentation
                            if opciones_para_ia:
                                # Use 32 spaces for indentation
                                print(f"      Enviando texto a IA (Simple) para extraer solución (Tipo: {tipo_pregunta})...");
                                solucion_simple = ia_utils.extraer_solucion_simple(contenido_modal, opciones_para_ia)
                                if solucion_simple:
                                    # Use 36 spaces for indentation
                                    print(f"      ¡SOLUCIÓN SIMPLE APRENDIDA! -> {solucion_simple}");
                                    solucion_aprendida = solucion_simple.strip()
                                else: print("      IA (Simple) no pudo extraer solución.")
                            else:
                                # Use 32 spaces for indentation
                                print(f"      Error Aprendizaje Simple: No se pudieron preparar 'opciones_para_ia' para {tipo_pregunta}")

                        # --- GUARDADO EN MEMORIA ---
                        if clave_pregunta and solucion_aprendida:
                            # Use 28 spaces for indentation
                            
                            # --- ¡INICIO DE LA CORRECCIÓN TIPO 2 APRENDIZAJE (Incorrecto)! ---
                            if tipo_pregunta == "TIPO_2_COMPLETAR" and clave_pregunta in soluciones_correctas:
                                # Use 32 spaces for indentation
                                print("      FUSIONANDO aprendizaje TIPO 2 en memoria existente...")
                                # 'solucion_aprendida' es un dict (ej: {'frase_nueva': 'resp_nueva'})
                                # 'soluciones_correctas[clave_pregunta]' es el dict existente
                                memoria_existente = soluciones_correctas[clave_pregunta]
                                if isinstance(memoria_existente, dict) and isinstance(solucion_aprendida, dict):
                                    # Use 36 spaces for indentation
                                    memoria_existente.update(solucion_aprendida) # Fusionamos el nuevo dict con el viejo
                                    soluciones_correctas[clave_pregunta] = memoria_existente
                                    print(f"      Memoria T2 fusionada: {solucion_aprendida}")
                                else:
                                    # Use 36 spaces for indentation
                                    print("      WARN: No se pudo fusionar T2, tipos no son dict. Sobrescribiendo...")
                                    soluciones_correctas[clave_pregunta] = solucion_aprendida
                            else:
                                # Use 32 spaces for indentation
                                # Comportamiento original (sobrescribir o crear nuevo)
                                # (Esto se aplica a TIPO 2 la primera vez, y a todos los demás tipos)
                                soluciones_correctas[clave_pregunta] = solucion_aprendida
                            # --- ¡FIN DE LA CORRECCIÓN TIPO 2 APRENDIZAJE (Incorrecto)! ---

                            guardar_memoria_en_disco() # Guardamos el resultado (fusionado o nuevo)

                    # --- CASO 2: RESPUESTA CORRECTA ---
                    elif "correct" in titulo_modal or "great" in titulo_modal:
                        # Use 24 spaces for indentation
                        print(f"      Respuesta CORRECTA detectada (Modal: {titulo_modal}).")
                        
                        # Regenerar clave correcta para guardar el acierto
                        
                        # --- INICIO DE LA CORRECCIÓN (BUG Guardado Acierto) ---
                        # (La 'clave_pregunta' original generada antes del CHECK
                        # ya incluye el HASH de contexto/imagen/audio si aplica,
                        # así que usamos esa directamente.)
                        
                        if tipo_pregunta == "TIPO_10_ESCRIBIR":
                             # Use 28 spaces for indentation
                             # (Esta lógica se mantiene porque 'lista_de_tareas_escribir'
                             #  sí existe en memoria y no depende del DOM)
                             titulo_limpio = pregunta_actual_texto.strip()
                             if lista_de_tareas_escribir:
                                 # Use 32 spaces for indentation
                                 claves_ordenadas_str = "|".join(sorted([t["letras_clave"] for t in lista_de_tareas_escribir]))
                                 clave_pregunta = f"T10_BATCH:{titulo_limpio}||{claves_ordenadas_str}"
                             else:
                                 # Use 32 spaces for indentation
                                 print("WARN Acierto T10: 'lista_de_tareas_escribir' vacía. No se puede generar clave.")
                                 clave_pregunta = None
                        
                        # --- ¡INICIO APRENDIZAJE TIPO 11 (Correcto)! ---
                        elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES":
                             # Use 28 spaces for indentation
                             titulo_limpio = pregunta_actual_texto.strip()
                             if lista_de_tareas_escribir: # Reusamos esta variable
                                 frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                                 clave_pregunta = f"T11_BATCH:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"
                             else:
                                 # Use 32 spaces for indentation
                                 print("WARN Acierto T11: 'lista_de_tareas_escribir' vacía. No se puede generar clave.")
                                 clave_pregunta = None
                        # --- ¡FIN APRENDIZAJE TIPO 11! ---

                        elif clave_pregunta:
                            # Use 28 spaces for indentation
                           # (Este 'elif' ahora capturará T2, T5, T9, Default y los demás
                           #  tipos, usando la clave original que ya estaba guardada)
                           clave_pregunta = clave_pregunta.strip()
                        # --- FIN DE LA CORRECCIÓN ---


                        # --- ¡INICIO CORRECCIÓN APRENDIZAJE TIPO 2 (Correcto)! ---
                        if clave_pregunta:
                            # Use 28 spaces for indentation
                            respuesta_correcta_actual = preguntas_ya_vistas.get(clave_pregunta)
                            
                            if respuesta_correcta_actual is None:
                                # Use 32 spaces for indentation
                                print(f"      WARN: Acierto, pero no se encontró la respuesta en 'preguntas_ya_vistas' para clave: {clave_pregunta}")
                            
                            # --- ¡INICIO DE LA CORRECCIÓN TIPO 2 ACIERTO! ---
                            elif tipo_pregunta == "TIPO_2_COMPLETAR":
                                # Use 32 spaces for indentation
                                print("      Procesando acierto para TIPO 2 (Dict)...")
                                # respuesta_correcta_actual es el DICT {"frase_actual": "resp_actual"}
                                if not isinstance(respuesta_correcta_actual, dict):
                                    # Use 36 spaces for indentation
                                    print(f"      ERROR Acierto T2: La respuesta guardada no es un dict: {respuesta_correcta_actual}")
                                
                                elif clave_pregunta in soluciones_correctas:
                                    # Use 36 spaces for indentation
                                    # La clave principal (título) ya existe. Fusionamos.
                                    memoria_existente = soluciones_correctas[clave_pregunta]
                                    nuevas_frases_count = 0
                                    for frase, respuesta in respuesta_correcta_actual.items():
                                        # Use 40 spaces for indentation
                                        if frase not in memoria_existente:
                                            # Use 44 spaces for indentation
                                            memoria_existente[frase] = respuesta
                                            print(f"      ¡SOLUCIÓN T2 (frase) APRENDIDA! -> {frase}: {respuesta}")
                                            nuevas_frases_count += 1
                                    
                                    if nuevas_frases_count > 0:
                                        # Use 40 spaces for indentation
                                        soluciones_correctas[clave_pregunta] = memoria_existente # Actualizamos el dict fusionado
                                        guardar_memoria_en_disco()
                                    else:
                                        # Use 40 spaces for indentation
                                        print("      La solución T2 (frase) ya estaba en memoria. No se necesita guardar.")
                                
                                else:
                                    # Use 36 spaces for indentation
                                    # La clave principal (título) NO existe. Guardamos el dict nuevo.
                                    print(f"      Guardando nuevo acierto (Lote T2 Completo) en memoria...")
                                    soluciones_correctas[clave_pregunta] = respuesta_correcta_actual
                                    print(f"      ¡SOLUCIÓN (por acierto T2) APRENDIDA! -> {respuesta_correcta_actual}")
                                    guardar_memoria_en_disco()
                            # --- FIN DE LA CORRECCIÓN TIPO 2 ACIERTO ---
                            
                            # --- LÓGICA ORIGINAL PARA TODOS LOS DEMÁS TIPOS (T1, T3, T4... T10, T11, Default) ---
                            elif clave_pregunta not in soluciones_correctas:
                                # Use 32 spaces for indentation
                                print(f"      Guardando nuevo acierto en memoria (Tipo: {tipo_pregunta})...")
                                try:
                                    # Use 36 spaces for indentation
                                    # Limpieza (la lógica original estaba un poco dispersa, la unificamos aquí)
                                    if isinstance(respuesta_correcta_actual, str):
                                        respuesta_correcta_actual = respuesta_correcta_actual.strip()
                                    if tipo_pregunta == "TIPO_10_ESCRIBIR" and isinstance(respuesta_correcta_actual, list):
                                         respuesta_correcta_actual = [p.upper() for p in respuesta_correcta_actual]
                                    elif tipo_pregunta == "TIPO_10_ESCRIBIR" and isinstance(respuesta_correcta_actual, str):
                                         respuesta_correcta_actual = respuesta_correcta_actual.upper()
                                    
                                    # --- ¡INICIO APRENDIZAJE TIPO 11 (Correcto)! ---
                                    elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES" and isinstance(respuesta_correcta_actual, list):
                                         respuesta_correcta_actual = [p.upper() for p in respuesta_correcta_actual]
                                    # --- ¡FIN APRENDIZAJE TIPO 11! ---

                                    soluciones_correctas[clave_pregunta] = respuesta_correcta_actual
                                    print(f"      ¡SOLUCIÓN (por acierto) APRENDIDA! -> {respuesta_correcta_actual}")
                                    guardar_memoria_en_disco()
                                except Exception as e_acierto:
                                    # Use 36 spaces for indentation
                                    print(f"      WARN: Error guardando acierto: {e_acierto}")
                            
                            elif clave_pregunta: # (Este 'elif' es el original)
                                # Use 32 spaces for indentation
                                print("      La solución ya estaba en memoria. No se necesita guardar.")
                        # --- ¡FIN CORRECCIÓN APRENDIZAJE TIPO 2 (Correcto)! ---

                except Exception as e:
                    # Use 20 spaces for indentation
                    print(f"      WARN: No se pudo leer modal o aprender. {e}")

                print("Clic OK..."); boton_ok.click()
                print("Respuesta enviada! Esperando que desaparezca modal..."); wait_long.until(EC.invisibility_of_element_located(sel.SELECTOR_OK))

                # --- ¡INICIO LÓGICA DE REFRESCO! ---
                if respuesta_fue_incorrecta:
                    print("      Respuesta fue incorrecta. Refrescando la página para resetear estado...")
                    try:
                        driver.refresh()
                        # Damos tiempo a que la página cargue tras el refresco
                        wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                        respuesta_fue_incorrecta = False # Reseteamos el flag
                        pregunta_actual_texto = "" # Reseteamos el texto
                        print("      Página refrescada. Reintentando...")
                    except Exception as e_refresh:
                        print(f"      ERROR CRÍTICO: No se pudo refrescar la página: {e_refresh}")
                        raise # Detener el bot si no puede refrescar
                # --- ¡FIN LÓGICA DE REFRESCO! ---

                print("Modal desaparecido. Cargando siguiente pregunta..."); time.sleep(0.5)

            except (TimeoutException, Exception) as e:
                # Use 16 spaces for indentation
                print(f"Error inesperado o Timeout: {e}")
                try:
                    # Use 20 spaces for indentation
                    wait_short.until(EC.element_to_be_clickable(sel.SELECTOR_CONTINUE)).click(); print("      FIN detectado tras error! Yendo a siguiente lección."); wait_long.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE)); break
                except (TimeoutException, NoSuchElementException):
                    # Use 20 spaces for indentation
                    print("      El test no ha terminado. Intentando 'SKIP'...");
                    try:
                        # Use 24 spaces for indentation
                        wait_short.until(EC.element_to_be_clickable(sel.SELECTOR_SKIP)).click(); print("      Botón 'SKIP' clickeado."); pregunta_actual_texto = ""; time.sleep(2); continue
                    except (TimeoutException, NoSuchElementException) as skip_e:
                        # Use 24 spaces for indentation
                        print(f"      No se pudo clickear 'SKIP' ({skip_e}). Refrescando como último recurso.");
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh(); pregunta_actual_texto = ""; time.sleep(3)
                        except Exception as refresh_err:
                            # Use 28 spaces for indentation
                            print(f"¡Error al refrescar! {refresh_err}. Deteniendo."); raise

    # --- Fin Bucle EXTERNO ---
except Exception as e:
    # Use 4 spaces for indentation
    print(f"\n--- ERROR FATAL ---"); print(f"Bot detenido: {e}")
finally:
    # Use 4 spaces for indentation
    print("\nProceso terminado. Cerrando en 20 seg."); time.sleep(20); driver.quit()





