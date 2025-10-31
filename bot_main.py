import time
import json
import random
import copy
import os # Para basename en fallback
from urllib.parse import urlparse # Mantener para fallback de audio
from collections import defaultdict # Para contador de desambiguación
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
        ultima_clave_pregunta_procesada = ""

        # Resetear variables antes de cada pregunta
        tipo_pregunta = ""; clave_pregunta = None; lista_ideas_texto = []; lista_de_preguntas = []; lista_afirmaciones_texto = []; frases_des = []; lista_de_claves_individuales = []; lista_de_tareas_ordenar = []
        palabras_clave = []; definiciones = []; lista_de_tareas_completar = []
        lista_de_tareas_escribir = []; lista_palabras_desordenadas_raw = []; lista_frases_t11 = []; lista_frases_t12 = [] # T12 AÑADIDO
        lista_frases_t11_raw = [] # AÑADIDO PARA FIX T11
        imagen_hash = ""; audio_hash = ""; contexto_hash = ""; body_hash = "" # Añadido reset body_hash
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

                # --- ¡INICIO LÓGICA DE DETECCIÓN T12! ---
                # El ORDEN es crucial
                letras_elem_t10 = driver.find_elements(*sel.SELECTOR_LETRAS_DESORDENADAS)
                input_elem = driver.find_elements(*sel.SELECTOR_INPUT_ESCRIBIR)
                audio_elem = driver.find_elements(*sel.SELECTOR_AUDIO) # <-- Comprobar audio

                if len(input_elem) > 0 and len(audio_elem) > 0:
                    print("      Contenido detectado: [TIPO 12 DICTADO]"); tipo_pregunta = "TIPO_12_DICTADO"
                # --- FIN LÓGICA T12 ---
                
                elif len(input_elem) > 0 and len(letras_elem_t10) > 0 and len(input_elem) == len(letras_elem_t10):
                    print("      Contenido detectado: [TIPO 10]"); tipo_pregunta = "TIPO_10_ESCRIBIR"
                elif len(input_elem) > 0 and len(letras_elem_t10) == 0:
                     print("      Contenido detectado: [TIPO 11]"); tipo_pregunta = "TIPO_11_ESCRIBIR_OPCIONES"
                elif len(driver.find_elements(*sel.SELECTOR_ANSWER_Q_CAJAS)) > 0: print("      Contenido detectado: [TIPO 7]"); tipo_pregunta = "TIPO_7_OM_CARD"
                elif len(driver.find_elements(*sel.SELECTOR_PARAGRAPH_CAJAS)) > 0: print("      Contenido detectado: [TIPO 6]"); tipo_pregunta = "TIPO_6_PARAGRAPH"
                elif len(driver.find_elements(*sel.SELECTOR_CAJAS_TF)) > 0:
                    num_cajas_tf = len(driver.find_elements(*sel.SELECTOR_CAJAS_TF))
                    if num_cajas_tf > 1:
                        print(f"      Contenido detectado: [TIPO 3] ({num_cajas_tf} cajas)");
                        tipo_pregunta = "TIPO_3_TF_MULTI"
                    else:
                        print(f"      Contenido detectado: [TIPO 5] ({num_cajas_tf} caja)");
                        tipo_pregunta = "TIPO_5_TF_SINGLE"
                elif len(driver.find_elements(*sel.SELECTOR_LINEAS_COMPLETAR)) > 0: print("      Contenido detectado: [TIPO 2]"); tipo_pregunta = "TIPO_2_COMPLETAR"
                elif len(driver.find_elements(*sel.SELECTOR_CONTENEDOR_ORDENAR)) > 0: print("      Contenido detectado: [TIPO 1]"); tipo_pregunta = "TIPO_1_ORDENAR"
                elif len(driver.find_elements(*sel.SELECTOR_IMAGEN_EMPAREJAR)) > 0: print("      Contenido detectado: [TIPO 8]"); tipo_pregunta = "TIPO_8_IMAGEN"
                elif len(driver.find_elements(*sel.SELECTOR_FILAS_EMPAREJAR)) > 0: print("      Contenido detectado: [TIPO 4]"); tipo_pregunta = "TIPO_4_EMPAREJAR"
                elif len(audio_elem) > 0: print("      Contenido detectado: [TIPO 9]"); tipo_pregunta = "TIPO_9_AUDIO" # T9 ahora va después de T12
                else: print("      No se detectó contenido especial. Se asume [DEFAULT]"); tipo_pregunta = "TIPO_DEFAULT_OM"
                # --- ¡FIN LÓGICA DE DETECCIÓN! ---

                print("Leyendo datos (Contexto y Título)...")
                try:
                    # Use 20 spaces for indentation
                    contexto = wait_short.until(EC.visibility_of_element_located(sel.SELECTOR_CONTEXTO)).text
                except TimeoutException:
                    # Use 20 spaces for indentation
                    print("Warn: No contexto."); contexto = ""

                contexto_hash = f"CTX:{contexto[:50]}...{contexto[-50:]}"

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

                # --- ¡NUEVO! Extraer Hash del Cuerpo de la Pregunta (para Default, T9) ---
                body_text = ""
                body_hash = ""
                if tipo_pregunta in ["TIPO_DEFAULT_OM", "TIPO_9_AUDIO"]: # Solo necesario para estos por ahora
                     # Use 20 spaces for indentation
                    try:
                        # Use 24 spaces for indentation
                        body_element = WebDriverWait(driver, 3).until(
                            EC.visibility_of_element_located(sel.SELECTOR_CUERPO_PREGUNTA)
                        )
                        body_text = body_element.text.strip()
                        if body_text:
                            # Use 28 spaces for indentation
                            cleaned_body = ' '.join(body_text.split())
                            # Acortar hash para evitar claves excesivamente largas
                            body_hash = f"BODY:{cleaned_body[:70]}...{cleaned_body[-70:]}" if len(cleaned_body) > 140 else f"BODY:{cleaned_body}"
                            print(f"      Cuerpo detectado. Hash: {body_hash}")
                        else:
                            # Use 28 spaces for indentation
                            print("      WARN: Cuerpo de pregunta encontrado pero vacío.")
                    except TimeoutException:
                        # Use 24 spaces for indentation
                        print("      WARN: No se encontró cuerpo de pregunta separado (Timeout). body_hash estará vacío.")
                    except Exception as e_body:
                        # Use 24 spaces for indentation
                        print(f"      WARN: Error extrayendo cuerpo de pregunta: {e_body}")
                # --- FIN Extracción Hash Cuerpo ---


                # --- Resetear listas/variables específicas de tipo (SEGUNDA VEZ PARA ASEGURAR) ---
                lista_ideas_texto = []; lista_de_preguntas = []; lista_afirmaciones_texto = []; frases_des = []; lista_de_claves_individuales = []; lista_de_tareas_ordenar = []
                palabras_clave = []; definiciones = []; lista_de_tareas_completar = []
                lista_de_tareas_escribir = []; lista_palabras_desordenadas_raw = []; lista_frases_t11 = []; lista_frases_t12 = [] # T12 AÑADIDO
                lista_frases_t11_raw = [] # AÑADIDO PARA FIX T11
                imagen_hash = ""; audio_hash = "" # No resetear contexto_hash ni body_hash aquí


                # --- TIPO 1: ORDENAR (MÚLTIPLE) ---
                if tipo_pregunta == "TIPO_1_ORDENAR":
                    # Use 20 spaces for indentation
                    print("Tipo: ORDENAR (Múltiple).")
                    contenedores = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_CONTENEDOR_ORDENAR))
                    if not contenedores: raise Exception("No se encontraron contenedores TIPO 1.")
                    print(f"Encontrados {len(contenedores)} contenedores para ordenar.")
                    lista_de_claves_individuales = []
                    lista_de_tareas_ordenar = []
                    for k, contenedor in enumerate(contenedores):
                        # Use 24 spaces for indentation
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", contenedor); time.sleep(0.1)
                        cajas_inicial = contenedor.find_elements(*sel.SELECTOR_CAJAS_ORDENAR)
                        frases_des_individual = []
                        map_id_a_texto_individual = {}
                        for i, c in enumerate(cajas_inicial):
                            # Use 28 spaces for indentation
                            try:
                                # Use 32 spaces for indentation
                                text_element = c.find_element(*sel.SELECTOR_TEXTO_CAJA_ORDENAR)
                                t = text_element.text.strip()
                                d_id = c.get_attribute("data-rbd-draggable-id")
                                if t and d_id:
                                    # Use 36 spaces for indentation
                                    frases_des_individual.append(t)
                                    map_id_a_texto_individual[d_id] = t
                            except NoSuchElementException: continue
                        if not frases_des_individual:
                            # Use 28 spaces for indentation
                            print(f"Warn: Contenedor {k+1} sin frases. Omitiendo.")
                            continue
                        print(f"      Tarea {k+1} Frases: {frases_des_individual}")
                        frases_ordenadas_para_clave = sorted(frases_des_individual)
                        clave_ind = "|".join(frases_ordenadas_para_clave)
                        lista_de_claves_individuales.append(f"{k}:{clave_ind}")
                        lista_de_tareas_ordenar.append({"frases": frases_des_individual,"map_id_a_texto": map_id_a_texto_individual,"contenedor_elem": contenedor})
                    if not lista_de_tareas_ordenar: raise Exception("No se recolectaron tareas TIPO 1 válidas.")
                    clave_pregunta = "|".join(lista_de_claves_individuales)

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 1)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

                    lista_ordenes_ia = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN LOTE TIPO 1 ENCONTRADA en memoria.");
                        lista_ordenes_ia = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 24 spaces for indentation
                        print("      Llamando a IA individualmente para TIPO 1 (se guardará en lote)...")
                        exito_ia_individual = True
                        for i, tarea in enumerate(lista_de_tareas_ordenar):
                            # Use 28 spaces for indentation
                            print(f"      IA (Ord) para Tarea {i+1}...")
                            orden_ia_individual = ia_utils.obtener_orden_correcto(contexto, tarea["frases"], pregunta_actual_texto)
                            if not orden_ia_individual:
                                # Use 32 spaces for indentation
                                print(f"Error IA (Ord) Tarea {i+1}."); exito_ia_individual = False; break
                            lista_ordenes_ia.append(orden_ia_individual)
                        if not exito_ia_individual: raise Exception("Fallo IA al obtener orden TIPO 1 individual.")
                        preguntas_ya_vistas[clave_pregunta] = lista_ordenes_ia
                    print(f"Órdenes a aplicar (lote): {lista_ordenes_ia}")
                    if len(lista_ordenes_ia) != len(lista_de_tareas_ordenar):
                        # Use 24 spaces for indentation
                        raise Exception("Fallo crítico: El número de soluciones no coincide con el de tareas TIPO 1.")
                    print("Reordenando JS (Lote)...")
                    exito_global = True
                    js = "var c=arguments[0],ids=arguments[1],m={};for(let i=0;i<c.children.length;i++){let o=c.children[i],d=o.firstElementChild;if(d&&d.getAttribute('data-rbd-draggable-id')){m[d.getAttribute('data-rbd-draggable-id')]=o;}}while(c.firstChild)c.removeChild(c.firstChild);ids.forEach(id=>{if(m[id])c.appendChild(m[id]);else console.error('JS Err ID:',id);});console.log('JS OK.');"
                    for orden_ia, tarea in zip(lista_ordenes_ia, lista_de_tareas_ordenar):
                        # Use 24 spaces for indentation
                        map_texto_lower_a_ids_lista = {}
                        for id_val, texto_val in tarea["map_id_a_texto"].items():
                            # Use 28 spaces for indentation
                            texto_lower = texto_val.lower().strip()
                            if texto_lower not in map_texto_lower_a_ids_lista:
                                # Use 32 spaces for indentation
                                map_texto_lower_a_ids_lista[texto_lower] = []
                            map_texto_lower_a_ids_lista[texto_lower].append(id_val)
                        map_ids_disponibles = copy.deepcopy(map_texto_lower_a_ids_lista)
                        ids_ok_filtrado = []
                        mapeo_fallido = False
                        for texto_ia in orden_ia:
                            # Use 28 spaces for indentation
                            texto_ia_lower = texto_ia.lower().strip()
                            if texto_ia_lower in map_ids_disponibles and map_ids_disponibles[texto_ia_lower]:
                                # Use 32 spaces for indentation
                                id_para_usar = map_ids_disponibles[texto_ia_lower].pop(0)
                                ids_ok_filtrado.append(id_para_usar)
                            else:
                                # Use 32 spaces for indentation
                                print(f"Error Mapeo T1: No hay ID disponible para '{texto_ia}' (Buscando: '{texto_ia_lower}')")
                                mapeo_fallido = True; break
                        if mapeo_fallido or len(ids_ok_filtrado) != len(tarea["frases"]):
                            # Use 28 spaces for indentation
                            print(f"Error: Fallo mapeo IDs JS para tarea {tarea['frases']}"); exito_global = False; continue
                        try:
                            # Use 28 spaces for indentation
                            driver.execute_script(js, tarea["contenedor_elem"], ids_ok_filtrado); time.sleep(0.5)
                        except JavascriptException as e:
                            # Use 28 spaces for indentation
                            print(f"Error JS en TIPO 1 Lote: {e}"); exito_global = False; continue
                    print("JS OK (Lote).")
                    if not exito_global: raise Exception("Fallo JS durante reordenamiento TIPO 1 Lote.")

                #--- TIPO 2: COMPLETAR ---
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

                    # --- ¡INICIO CORRECCIÓN CLAVE TIPO 2! ---
                    titulo_limpio = pregunta_actual_texto.strip()
                    if lista_de_tareas_completar:
                        # Use 24 spaces for indentation
                        frases_para_clave = sorted([t["frase"] for t in lista_de_tareas_completar])
                        frases_hash_str = "|".join(frases_para_clave)
                        clave_pregunta = f"T2_BATCH:{titulo_limpio}||{contexto_hash}||FRASES:{frases_hash_str}"
                    else:
                        # Use 24 spaces for indentation
                        clave_pregunta = f"T2_BATCH:{titulo_limpio}||{contexto_hash}||FRASES:NO_TASKS"
                    print(f"      Clave T2 generada: {clave_pregunta[:100]}...") # Log para verificar
                    # --- ¡FIN CORRECCIÓN CLAVE TIPO 2! ---

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 2)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

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
                                print(f"      ERROR Memoria T2: No se encontró la frase '{frase_key}' en el dict de soluciones para la clave principal '{clave_pregunta[:70]}...'.");
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
                        frases_clave_actual = [t["frase"] for t in lista_de_tareas_completar]
                        preguntas_ya_vistas[clave_pregunta] = dict(zip(frases_clave_actual, respuestas_lote_ia))
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
                            print(f"Error CRÍTICO T2: Botón '{respuesta_ia}' no encontrado en opciones {tarea['opciones']}.");
                            exito_global = False; break
                    if not exito_global: raise Exception("Fallo al completar palabras (Lote).")


                # --- TIPO 3: TRUE/FALSE MÚLTIPLE ---
                elif tipo_pregunta == "TIPO_3_TF_MULTI":
                    # Use 20 spaces for indentation
                    print("Tipo: TRUE/FALSE MÚLTIPLE.")
                    cajas_afirmacion = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_CAJAS_TF))
                    if not cajas_afirmacion: raise Exception("No se encontraron cajas True/False.")
                    print(f"Encontradas {len(cajas_afirmacion)} afirmaciones.")
                    lista_afirmaciones_texto = []
                    elementos_cajas_botones = []
                    print("Recolectando afirmaciones...")
                    for k, caja in enumerate(cajas_afirmacion):
                        # Use 24 spaces for indentation
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            # Use 28 spaces for indentation
                            texto_afirmacion_elem = caja.find_element(*sel.SELECTOR_TEXTO_AFIRMACION_TF)
                            wait_short.until(EC.visibility_of(texto_afirmacion_elem))
                            texto_afirmacion = texto_afirmacion_elem.text.strip()
                            boton_true = caja.find_element(*sel.SELECTOR_BOTON_TRUE_TF)
                            boton_false = caja.find_element(*sel.SELECTOR_BOTON_FALSE_TF)
                            if texto_afirmacion:
                                # Use 32 spaces for indentation
                                clave_unica_afirmacion = f"{k}:{texto_afirmacion}"
                                lista_afirmaciones_texto.append(clave_unica_afirmacion)
                                elementos_cajas_botones.append((caja, boton_true, boton_false))
                            else: print(f"Warn: Caja {k+1} sin texto.")
                        except (NoSuchElementException, TimeoutException) as e_inner:
                            # Use 28 spaces for indentation
                            print(f"Error leyendo caja {k+1}: {e_inner}"); raise Exception(f"Fallo crítico al leer caja T/F {k+1}")
                    if not lista_afirmaciones_texto: raise Exception("No se pudieron recolectar afirmaciones T/F.")
                    clave_pregunta = "|".join(lista_afirmaciones_texto)

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 3)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

                    respuestas_tf_lote = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN LOTE T/F ENCONTRADA en memoria."); respuestas_tf_lote = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 24 spaces for indentation
                        print("      Llamando a IA individualmente (con memoria de intento)...")
                        respuestas_tf_lote_temporal = []
                        exito_ia_individual = True
                        for texto_afirmacion_con_indice in lista_afirmaciones_texto:
                            # Use 28 spaces for indentation
                            texto_afirmacion_real = texto_afirmacion_con_indice.split(":", 1)[1]
                            clave_individual = texto_afirmacion_con_indice
                            opciones_ya_vistas[clave_individual]=["True","False"]
                            respuesta_tf_ia = None
                            if clave_individual in preguntas_ya_vistas:
                                # Use 32 spaces for indentation
                                respuesta_anterior = preguntas_ya_vistas[clave_individual]; respuesta_tf_ia = "False" if respuesta_anterior == "True" else "True"
                                print(f"      WARN: Afirmación '{texto_afirmacion_real[:30]}...' repetida. Forzando: '{respuesta_tf_ia}'")
                            else:
                                # Use 32 spaces for indentation
                                print(f"      IA (T/F) para '{texto_afirmacion_real[:30]}...'?"); respuesta_tf_ia = ia_utils.obtener_true_false(contexto, texto_afirmacion_real)
                            if respuesta_tf_ia:
                                # Use 32 spaces for indentation
                                preguntas_ya_vistas[clave_individual] = respuesta_tf_ia; respuestas_tf_lote_temporal.append(respuesta_tf_ia)
                            else: print(f"Error IA T/F para afirmación: {texto_afirmacion_real}"); exito_ia_individual = False; break
                        if not exito_ia_individual: raise Exception("Fallo IA al obtener respuesta T/F individual.")
                        respuestas_tf_lote = respuestas_tf_lote_temporal
                        preguntas_ya_vistas[clave_pregunta] = respuestas_tf_lote
                    print(f"Respuestas T/F a usar: {respuestas_tf_lote}")
                    exito_global = True
                    for i, (respuesta_tf_ia, (caja, boton_true, boton_false)) in enumerate(zip(respuestas_tf_lote, elementos_cajas_botones)):
                        # Use 24 spaces for indentation
                        try:
                            # Use 28 spaces for indentation
                            boton_a_clicar = boton_true if respuesta_tf_ia == "True" else boton_false
                            print(f"      Clic en '{respuesta_tf_ia}' para afirmación {i+1}...")
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                            wait_short.until(EC.element_to_be_clickable(boton_a_clicar))
                            driver.execute_script("arguments[0].click();", boton_a_clicar); time.sleep(0.3)
                        except Exception as e_inner:
                            # Use 28 spaces for indentation
                            print(f"Error en clic T/F iteración {i+1}: {e_inner}"); exito_global = False; break
                    if not exito_global: raise Exception("Fallo durante los clics de T/F Múltiple.")

                # --- TIPO 6: MATCH IDEA TO PARAGRAPH ---
                elif tipo_pregunta == "TIPO_6_PARAGRAPH":
                    # Use 20 spaces for indentation
                    print("Tipo: MATCH IDEA TO PARAGRAPH.");
                    cajas_ideas = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_PARAGRAPH_CAJAS))
                    if not cajas_ideas: raise Exception("No cajas ideas.")
                    print(f"Encontradas {len(cajas_ideas)} ideas."); lista_ideas_texto = []; elementos_cajas = []
                    print("Recolectando ideas...");
                    for k, caja in enumerate(cajas_ideas):
                        # Use 24 spaces for indentation
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            # Use 28 spaces for indentation
                            idea_elem = caja.find_element(*sel.SELECTOR_PARAGRAPH_IDEA_TEXT); idea_texto = idea_elem.text.strip()
                            if idea_texto:
                                # Use 32 spaces for indentation
                                clave_unica_idea = f"{k}:{idea_texto}"
                                lista_ideas_texto.append(clave_unica_idea);
                                elementos_cajas.append(caja);
                                print(f"      Idea {k+1}: '{idea_texto}'")
                            else: print(f"Warn: Caja {k+1} sin texto.")
                        except (NoSuchElementException, TimeoutException) as e: print(f"Error leyendo idea {k+1}: {e}"); continue
                    if not lista_ideas_texto: raise Exception("No ideas recolectadas.")
                    clave_pregunta = "|".join(lista_ideas_texto)

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 6)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

                    if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA."); respuestas_lote_ia = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 24 spaces for indentation
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
                        # Use 24 spaces for indentation
                        try:
                            # Use 28 spaces for indentation
                            selector_boton_num = (By.XPATH, f".//button[normalize-space()='{numero_parrafo_ia}']"); boton_a_clicar = caja.find_element(*selector_boton_num)
                            print(f"      Clic en '{numero_parrafo_ia}'..."); wait_long.until(EC.element_to_be_clickable(boton_a_clicar)); driver.execute_script("arguments[0].click();", boton_a_clicar); time.sleep(0.3)
                        except Exception as e: print(f"Error clic Parágrafo '{numero_parrafo_ia}': {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo al resolver Match Paragraph.")

                # --- TIPO 4: EMPAREJAR ---
                elif tipo_pregunta == "TIPO_4_EMPAREJAR":
                    # Use 20 spaces for indentation
                    print("Tipo: EMPAREJAR PALABRAS.");
                    exito_global = True; print("      Extrayendo definiciones (JS)...")
                    js_get_defs = f"return Array.from(document.querySelectorAll('{sel.SELECTOR_DEFINICIONES_AZULES_CSS}')).map(el => el.innerText.trim());"
                    try:
                        # Use 24 spaces for indentation
                        definiciones = driver.execute_script(js_get_defs); definiciones = [d.strip() for d in definiciones if d]
                        if not definiciones: raise Exception("JS no encontró texto def.")
                        map_texto_def_a_elemento = {}
                        spans_defs_selenium = wait_long.until(EC.presence_of_all_elements_located((sel.SELECTOR_DEFINICIONES_AZULES_XPATH)))
                        for s in spans_defs_selenium:
                            # Use 28 spaces for indentation
                            texto = s.text.strip();
                            if texto in definiciones: map_texto_def_a_elemento[texto] = s
                        if len(map_texto_def_a_elemento) != len(definiciones): print("Warn: No se mapearon elementos def.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo def: {e}")
                    print(f"      Definiciones encontradas: {definiciones}"); print("      Extrayendo palabras clave (en orden)...")
                    js_get_keywords = f"let k=[];document.querySelectorAll('{sel.SELECTOR_FILAS_EMPAREJAR_CSS}').forEach(r=>{{let e=r.querySelector('{sel.SELECTOR_PALABRA_CLAVE_CSS}');if(e)k.push(e.innerText.replace(/_/g,'').replace(/:/g,'').replace(/'/g,'').replace(/\s+/g, ' ').trim());}});return k;"
                    try:
                        # Use 24 spaces for indentation
                        palabras_clave = driver.execute_script(js_get_keywords); palabras_clave = [p.strip() for p in palabras_clave if p]
                        if not palabras_clave: raise Exception("JS no encontró palabras clave.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo palabras: {e}")
                    print(f"      Palabras clave encontradas (en orden): {palabras_clave}");
                    titulo_limpio = pregunta_actual_texto.strip()
                    defs_limpias_sorted = sorted([d.strip() for d in definiciones])
                    clave_pregunta = f"T4:{titulo_limpio}||" + "|".join(defs_limpias_sorted)

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 4)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN ENCONTRADA en memoria.");
                        lista_definiciones_ordenadas = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 24 spaces for indentation
                        print("      IA (Emparejar)...")
                        pares_ia_temporal = ia_utils.obtener_emparejamientos(palabras_clave, definiciones)
                        if not pares_ia_temporal: raise Exception("IA (Emparejar) falló.")
                        lista_definiciones_ordenadas = []
                        for clave in palabras_clave:
                            # Use 28 spaces for indentation
                            if clave in pares_ia_temporal:
                                # Use 32 spaces for indentation
                                lista_definiciones_ordenadas.append(pares_ia_temporal[clave])
                            else:
                                # Use 32 spaces for indentation
                                print(f"Error: IA no devolvió clave '{clave}'"); raise Exception("Fallo mapeo IA T4")
                        preguntas_ya_vistas[clave_pregunta] = lista_definiciones_ordenadas
                    print(f"      Solución a aplicar (en orden): {lista_definiciones_ordenadas}"); print("      Clickeando en orden (Sistema de Cola)...")
                    for definicion_correcta in lista_definiciones_ordenadas:
                        # Use 24 spaces for indentation
                        elemento_origen = map_texto_def_a_elemento.get(definicion_correcta)
                        if not elemento_origen: print(f"Error: No WebElement para def '{definicion_correcta}'"); exito_global = False; continue
                        print(f"            Clic en '{definicion_correcta}'...");
                        try:
                            # Use 28 spaces for indentation
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", elemento_origen); time.sleep(0.3)
                            wait_long.until(EC.element_to_be_clickable(elemento_origen)).click(); print("                  Clic OK."); time.sleep(1.0)
                        except Exception as e: print(f"                  Error CRÍTICO (Click) en '{definicion_correcta}': {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo emparejar (Clic en orden).")

                # --- TIPO 5: MARK TRUE/FALSE (SINGLE) ---
                elif tipo_pregunta == "TIPO_5_TF_SINGLE":
                    # Use 20 spaces for indentation
                    print("Tipo: MARK TRUE/FALSE (Single).");
                    try:
                        # Use 24 spaces for indentation
                        # --- ¡INICIO CORRECCIÓN T5! ---
                        # Leer la afirmación real desde la tarjeta, no desde el título de la página
                        texto_afirmacion_elem = wait_long.until(EC.presence_of_element_located(sel.SELECTOR_MARK_TF_TEXT))
                        texto_afirmacion = texto_afirmacion_elem.text.strip()
                        if not texto_afirmacion: raise Exception("No se pudo leer el texto de la afirmación TIPO 5.")
                        # --- FIN CORRECCIÓN T5! ---
                        
                        boton_true = wait_long.until(EC.presence_of_element_located(sel.SELECTOR_MARK_TF_TRUE))
                        boton_false = wait_long.until(EC.presence_of_element_located(sel.SELECTOR_MARK_TF_FALSE))

                        print(f"      Afirmación (de Tarjeta): '{texto_afirmacion}'"); # <-- Log corregido
                        opciones_t5 = ["True", "False"]
                        titulo_limpio_t5 = texto_afirmacion.strip()
                        clave_pregunta = f"T5:{titulo_limpio_t5}||{contexto_hash}||" + "|".join(sorted(opciones_t5))

                        # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 5)! ---
                        if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                            # Use 28 spaces for indentation
                            print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                            print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                            try:
                                # Use 32 spaces for indentation
                                driver.refresh()
                                wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                                print("      Página refrescada. Reintentando...")
                                pregunta_actual_texto = ""
                                ultima_clave_pregunta_procesada = ""
                                respuesta_fue_incorrecta = False
                                continue
                            except Exception as e_refresh:
                                # Use 32 spaces for indentation
                                print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                                raise
                        # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

                        opciones_ya_vistas[clave_pregunta] = opciones_t5
                        if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA."); respuesta_tf_ia = soluciones_correctas[clave_pregunta]
                        else:
                            # Use 28 spaces for indentation
                            if clave_pregunta in preguntas_ya_vistas:
                                # Use 32 spaces for indentation
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
                        # Use 24 spaces for indentation
                        print(f"Error T/F (Single) elems: {e}");
                        raise Exception("Fallo resolver Mark T/F.")
                    except Exception as e:
                        # Use 24 spaces for indentation
                        print(f"Error T/F (Single) lógica: {e}");
                        raise

                # --- TIPO 7: ANSWER THE QUESTION ---
                elif tipo_pregunta == "TIPO_7_OM_CARD":
                    # Use 20 spaces for indentation
                    print("Tipo: ANSWER THE QUESTION (OM in Card).");
                    cajas_preguntas = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_ANSWER_Q_CAJAS))
                    if not cajas_preguntas: raise Exception("No cajas 'Answer Question'.")
                    print(f"Encontradas {len(cajas_preguntas)} tarjetas."); lista_de_tareas = []; lista_de_preguntas = []; elementos_cajas = []
                    print("Recolectando tareas...");
                    for k, caja in enumerate(cajas_preguntas):
                        # Use 24 spaces for indentation
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            # Use 28 spaces for indentation
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

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 7)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

                    if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA."); respuestas_lote_ia = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 24 spaces for indentation
                        respuesta_anterior_incorrecta = None
                        if clave_pregunta in preguntas_ya_vistas: respuesta_anterior_incorrecta = preguntas_ya_vistas[clave_pregunta]; print(f"      WARN: Pregunta repetida. Anterior: {respuesta_anterior_incorrecta}.")
                        print(f"Enviando {len(lista_de_tareas)} tareas a IA..."); respuestas_lote_ia = ia_utils.obtener_respuestas_om_lote(contexto, lista_de_tareas, respuesta_anterior_incorrecta)
                        if not respuestas_lote_ia or len(respuestas_lote_ia) != len(elementos_cajas): raise Exception("Fallo IA (OM Lote) o nº resp no coincide.")
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia
                    print(f"Respuestas a usar: {respuestas_lote_ia}"); print("Haciendo clics...")
                    exito_global = True
                    for respuesta_ia, caja in zip(respuestas_lote_ia, elementos_cajas):
                        # Use 24 spaces for indentation
                        try:
                            # Use 28 spaces for indentation
                            opciones_elementos_caja = caja.find_elements(*sel.SELECTOR_ANSWER_Q_BOTONES); boton_encontrado = None
                            for b in opciones_elementos_caja:
                                # Use 32 spaces for indentation
                                if b.text.strip() == respuesta_ia: boton_encontrado = b; break
                            if boton_encontrado: print(f"      Clic en '{boton_encontrado.text}'..."); driver.execute_script("arguments[0].click();", boton_encontrado); time.sleep(0.3)
                            else: print(f"Error CRÍTICO: Botón '{respuesta_ia}' no encontrado."); exito_global = False
                        except Exception as e: print(f"Error bucle clics T7: {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo al resolver 'Answer Question'.")

                # --- TIPO 8: EMPAREJAR IMAGEN ---
                elif tipo_pregunta == "TIPO_8_IMAGEN":
                    # Use 20 spaces for indentation
                    print("Tipo: EMPAREJAR IMAGEN (TIPO 8).");
                    imagen_hash = ""
                    palabras_clave = []
                    hash_counts = defaultdict(int)

                    exito_global = True; print("      Extrayendo definiciones (JS)...")
                    js_get_defs = f"return Array.from(document.querySelectorAll('{sel.SELECTOR_DEFINICIONES_AZULES_CSS}')).map(el => el.innerText.trim());"
                    try:
                        # Use 24 spaces for indentation
                        definiciones = driver.execute_script(js_get_defs); definiciones = [d.strip() for d in definiciones if d]
                        if not definiciones: raise Exception("JS no encontró texto def.")
                        map_texto_def_a_elemento = {}
                        spans_defs_selenium = wait_long.until(EC.presence_of_all_elements_located((sel.SELECTOR_DEFINICIONES_AZULES_XPATH)))
                        for s in spans_defs_selenium:
                            # Use 28 spaces for indentation
                            texto = s.text.strip();
                            if texto in definiciones: map_texto_def_a_elemento[texto] = s
                        if len(map_texto_def_a_elemento) != len(definiciones): print("Warn: No se mapearon elementos def.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo def: {e}")
                    print(f"      Definiciones encontradas: {definiciones}");

                    print("      Extrayendo ALT/Dimensiones de imagen + Desambiguación (en orden)...");
                    try:
                        # Use 24 spaces for indentation
                        filas_imagenes = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_IMAGEN_EMPAREJAR))
                        if not filas_imagenes: raise Exception("Selenium no encontró filas de imagen TIPO 8.")
                        for i, fila in enumerate(filas_imagenes):
                            # Use 28 spaces for indentation
                            img_elem = fila.find_element(By.TAG_NAME, "img")
                            hash_base = None
                            hash_final = None

                            alt_text = img_elem.get_attribute("alt")
                            alt_text_limpio = alt_text.strip() if alt_text else ""
                            if alt_text_limpio and alt_text_limpio.lower() != "descripción de la imagen":
                                # Use 32 spaces for indentation
                                hash_base = f"IMG_ALT:{alt_text_limpio}"
                                print(f"      Fila {i+1}: Usando ALT='{alt_text_limpio}'", end="")

                            if not hash_base:
                                # Use 32 spaces for indentation
                                try:
                                    # Use 36 spaces for indentation
                                    size = img_elem.size
                                    width = size.get('width', 0)
                                    height = size.get('height', 0)
                                    if width > 0 and height > 0:
                                        # Use 40 spaces for indentation
                                        hash_base = f"IMG_DIM:{width}x{height}"
                                        print(f"      Fila {i+1}: ALT genérico/vacío. Usando Dimensiones='{width}x{height}'", end="")
                                    else:
                                        # Use 40 spaces for indentation
                                        print(f"      Fila {i+1}: ALT genérico/vacío Y Dimensiones 0x0.", end="")
                                        hash_base = f"imagen_error_{i}_nodim"
                                except Exception as e_size:
                                    # Use 36 spaces for indentation
                                    print(f"      Fila {i+1}: ALT genérico/vacío. Error obteniendo dimensiones: {e_size}.", end="")
                                    hash_base = f"imagen_error_{i}_sizefail"

                            if hash_base:
                                # Use 32 spaces for indentation
                                count = hash_counts[hash_base]
                                if count > 0:
                                    # Use 36 spaces for indentation
                                    hash_final = f"{hash_base}_{count}"
                                    print(f" (Duplicado #{count}) -> Hash='{hash_final}'")
                                else:
                                    # Use 36 spaces for indentation
                                    hash_final = hash_base
                                    print(f" -> Hash='{hash_final}'")
                                hash_counts[hash_base] += 1
                            else:
                                # Use 32 spaces for indentation
                                hash_final = f"imagen_error_{i}_final"
                                print(f" -> Hash='{hash_final}' (Fallback final)")

                            palabras_clave.append(hash_final)

                        if not palabras_clave: raise Exception("No se extrajeron ALT/Dimensiones/Índices de imágenes.")
                    except (NoSuchElementException, TimeoutException) as e:
                        # Use 24 spaces for indentation
                        raise Exception(f"Error extrayendo ALT/Dimensiones/Índices de img TIPO 8: {e}")

                    print(f"      Claves Únicas (ALT/DIM+Índice) encontradas (en orden): {palabras_clave}");
                    titulo_limpio = pregunta_actual_texto.strip()
                    defs_limpias_sorted = sorted([d.strip() for d in definiciones])
                    claves_unicas_ordenados_str = "|".join(sorted(palabras_clave))
                    clave_pregunta = f"T8:{titulo_limpio}||{claves_unicas_ordenados_str}||" + "|".join(defs_limpias_sorted)

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 8)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

                    print(f"DEBUG: Generated Key T8: '{clave_pregunta}'")
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN ENCONTRADA en memoria.");
                        lista_definiciones_ordenadas = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 24 spaces for indentation
                        print("      IA (Emparejar - T8)...")
                        pares_ia_temporal = ia_utils.obtener_emparejamientos(palabras_clave, definiciones)
                        if not pares_ia_temporal or len(pares_ia_temporal) != len(palabras_clave) or not all(k in pares_ia_temporal for k in palabras_clave):
                             # Use 28 spaces for indentation
                             print(f"Error IA (Emparejar T8): Respuesta incompleta o inválida. Esperaba {len(palabras_clave)} claves, recibió {len(pares_ia_temporal) if pares_ia_temporal else 0}.")
                             print(f"Respuesta IA: {pares_ia_temporal}")
                             raise Exception("IA (Emparejar T8) falló o devolvió respuesta incompleta.")

                        lista_definiciones_ordenadas = []
                        for clave_unica in palabras_clave:
                            # Use 28 spaces for indentation
                            if clave_unica in pares_ia_temporal:
                                 # Use 32 spaces for indentation
                                 lista_definiciones_ordenadas.append(pares_ia_temporal[clave_unica])
                            else:
                                # Use 32 spaces for indentation
                                print(f"Error CRÍTICO: IA validó pero falta la clave_unica '{clave_unica}'"); raise Exception("Fallo mapeo IA T8 post-validación")
                        preguntas_ya_vistas[clave_pregunta] = lista_definiciones_ordenadas
                    print(f"      Solución a aplicar (en orden): {lista_definiciones_ordenadas}"); print("      Clickeando en orden (Sistema de Cola)...")
                    for definicion_correcta in lista_definiciones_ordenadas:
                        # Use 24 spaces for indentation
                        elemento_origen = map_texto_def_a_elemento.get(definicion_correcta)
                        if not elemento_origen: elemento_origen = map_texto_def_a_elemento.get(definicion_correcta.strip())
                        if not elemento_origen: print(f"Error: No WebElement para def '{definicion_correcta}'"); exito_global = False; continue
                        print(f"            Clic en '{definicion_correcta}'...");
                        try:
                            # Use 28 spaces for indentation
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", elemento_origen); time.sleep(0.3)
                            wait_long.until(EC.element_to_be_clickable(elemento_origen)).click(); print("                  Clic OK."); time.sleep(1.0)
                        except Exception as e: print(f"                  Error CRÍTICO (Click) en '{definicion_correcta}': {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo emparejar T8 (Clic en orden).")

                # --- TIPO 9: AUDIO ---
                elif tipo_pregunta == "TIPO_9_AUDIO":
                    # Use 20 spaces for indentation
                    print("Tipo: AUDIO (TIPO 9).");
                    opciones_elementos = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_OPCIONES))
                    opciones = [e.text.strip() for e in opciones_elementos if e.text and e.is_displayed()]
                    if not opciones: raise Exception("No opciones visibles (TIPO 9).")

                    # --- Lógica de HASH de AUDIO (original, blob) ---
                    # (Como pediste, no tocamos T9)
                    audio_hash = ""
                    try:
                        # Use 24 spaces for indentation
                        audio_elem = driver.find_element(*sel.SELECTOR_AUDIO)
                        audio_src = audio_elem.get_attribute("src")
                        if audio_src:
                            # Use 28 spaces for indentation
                            try:
                                # Use 32 spaces for indentation
                                parsed_url = urlparse(audio_src)
                                path = parsed_url.path
                                nombre_archivo = os.path.basename(path)
                                if nombre_archivo:
                                    # Use 36 spaces for indentation
                                    audio_hash = f"AUD:{nombre_archivo}"
                                    print(f"      Audio detectado. Añadiendo hash a la clave: {audio_hash}")
                                else:
                                    # Use 36 spaces for indentation
                                    print("      WARN: No se pudo extraer nombre de archivo del path de audio.")
                            except Exception as e_parse_aud:
                                # Use 32 spaces for indentation
                                print(f"      WARN: Error parseando URL de audio '{audio_src}': {e_parse_aud}")
                    except Exception as e_aud:
                        # Use 24 spaces for indentation
                        print(f"      WARN: No se pudo extraer hash de audio: {e_aud}")

                    titulo_limpio_t9 = pregunta_actual_texto.strip() if "pregunta_sin_titulo" not in pregunta_actual_texto else contexto[:150]
                    opciones_limpias_sorted_t9 = sorted([o.strip() for o in opciones])
                    clave_pregunta = f"T9:{titulo_limpio_t9}||{contexto_hash}||{body_hash}||{audio_hash}||" + "|".join(opciones_limpias_sorted_t9) # body_hash añadido

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 9)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

                    print(f"Resolviendo: {pregunta_actual_texto}\nOpciones: {opciones}");
                    opciones_ya_vistas[clave_pregunta] = opciones
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN ENCONTRADA.");
                        respuesta_adivinada = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 24 spaces for indentation
                        opciones_para_adivinar = list(opciones)
                        if clave_pregunta in preguntas_ya_vistas:
                            # Use 28 spaces for indentation
                            respuesta_anterior = preguntas_ya_vistas[clave_pregunta];
                            print(f"      WARN: Pregunta (T9) repetida. Anterior: ('{respuesta_anterior}').")
                            if respuesta_anterior in opciones_para_adivinar:
                                # Use 32 spaces for indentation
                                opciones_para_adivinar.remove(respuesta_anterior);
                                print(f"      Reintentando con: {opciones_para_adivinar}")
                            if not opciones_para_adivinar:
                                # Use 32 spaces for indentation
                                opciones_para_adivinar = list(opciones)
                        print("      Adivinando respuesta (Audio)...");
                        respuesta_adivinada = random.choice(opciones_para_adivinar)
                        preguntas_ya_vistas[clave_pregunta] = respuesta_adivinada
                    print(f"Bot decidió: '{respuesta_adivinada}'"); boton_encontrado = None
                    opciones_visibles = driver.find_elements(*sel.SELECTOR_OPCIONES)
                    for b in opciones_visibles:
                        # Use 24 spaces for indentation
                        t_b = ' '.join(b.text.split()); t_ia = ' '.join(respuesta_adivinada.split())
                        if t_b == t_ia: boton_encontrado = b; break
                    if boton_encontrado: print(f"Clic en '{boton_encontrado.text}'..."); driver.execute_script("arguments[0].scrollIntoView(true);",boton_encontrado); time.sleep(0.2); boton_encontrado.click(); time.sleep(0.5)
                    else: raise Exception(f"Botón '{respuesta_adivinada}' no encontrado.")


                # --- TIPO 10: ESCRIBIR PALABRA ORDENADA ---
                elif tipo_pregunta == "TIPO_10_ESCRIBIR":
                    # Use 20 spaces for indentation
                    print("Tipo: ESCRIBIR PALABRA ORDENADA (TIPO 10 - Lote).");
                    letras_elems = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_LETRAS_DESORDENADAS))
                    input_elems = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_INPUT_ESCRIBIR))
                    if not letras_elems or not input_elems or len(letras_elems) != len(input_elems):
                        raise Exception(f"Error TIPO 10: No coinciden elementos de letras ({len(letras_elems)}) e inputs ({len(input_elems)}).")
                    num_tareas = len(letras_elems)
                    print(f"Encontradas {num_tareas} tareas TIPO 10.")
                    lista_de_tareas_escribir = []
                    lista_palabras_desordenadas_raw = []
                    for i in range(num_tareas):
                        # Use 24 spaces for indentation
                        letras_desordenadas_raw = letras_elems[i].text.strip()
                        input_elem_actual = input_elems[i]
                        if not letras_desordenadas_raw:
                            # Use 28 spaces for indentation
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

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 10)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

                    respuestas_lote_ia = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN LOTE TIPO 10 ENCONTRADA en memoria.");
                        respuestas_lote_ia = soluciones_correctas[clave_pregunta]
                    else:
                        # Use 24 spaces for indentation
                        print("      Llamando a IA (Ordenar Palabra Lote)...")
                        respuestas_ia_temp = ia_utils.obtener_palabras_ordenadas_lote(lista_palabras_desordenadas_raw)
                        if not respuestas_ia_temp or len(respuestas_ia_temp) != len(lista_de_tareas_escribir):
                            # Use 28 spaces for indentation
                            raise Exception("Fallo IA (Ordenar Lote) o nº resp no coincide.")
                        respuestas_lote_ia = respuestas_ia_temp
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia
                    print(f"Palabras ordenadas a escribir: {respuestas_lote_ia}")
                    exito_global = True
                    if len(respuestas_lote_ia) != len(lista_de_tareas_escribir):
                        # Use 24 spaces for indentation
                        print("Error crítico T10: Número de respuestas IA no coincide con tareas.")
                        raise Exception("Fallo TIPO 10 - Mismatch respuestas/tareas")
                    for palabra_correcta, tarea in zip(respuestas_lote_ia, lista_de_tareas_escribir):
                        # Use 24 spaces for indentation
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
                            print(f"Error al escribir en input TIPO 10: {e}");
                            exito_global = False; break
                    if not exito_global: raise Exception("Fallo al escribir en inputs TIPO 10.")

                # --- TIPO 11: ESCRIBIR OPCIONES ---
                elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES":
                    # Use 20 spaces for indentation
                    print("Tipo: ESCRIBIR OPCIONES (TIPO 11 - Lote).");
                    input_elems = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_INPUT_ESCRIBIR))
                    if not input_elems:
                        raise Exception("Error TIPO 11: No se encontraron inputs.")

                    num_tareas = len(input_elems)
                    print(f"Encontradas {num_tareas} tareas TIPO 11.")
                    lista_de_tareas_escribir = []
                    lista_frases_t11 = []
                    lista_frases_t11_raw = [] # ¡NUEVO! Para guardar las letras desordenadas (ej. "NTESNI")

                    for i, input_elem_actual in enumerate(input_elems):
                        # Use 24 spaces for indentation
                        try:
                            # Use 28 spaces for indentation
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", input_elem_actual); time.sleep(0.1)
                            frase_elem = input_elem_actual.find_element(*sel.SELECTOR_FRASE_T11)
                            frase_texto_raw = frase_elem.text.strip() # ¡NUEVO!
                            if not frase_texto_raw: raise Exception("Frase T11 vacía.")

                            frase_para_ia = frase_texto_raw + " ___" # Para la clave de memoria
                            print(f"      Tarea {i+1}: Frase='{frase_para_ia}' (Raw='{frase_texto_raw}')")

                            lista_de_tareas_escribir.append({"frase": frase_para_ia, "input_elem": input_elem_actual})
                            lista_frases_t11.append(frase_para_ia)
                            lista_frases_t11_raw.append(frase_texto_raw) # ¡NUEVO!

                        except (NoSuchElementException, TimeoutException) as e_t11:
                             # Use 28 spaces for indentation
                             print(f"WARN TIPO 11: Tarea {i+1} sin frase. Omitiendo. ({e_t11})")
                             continue

                    if not lista_de_tareas_escribir: raise Exception("No se recolectaron tareas TIPO 11 válidas.")

                    titulo_limpio = pregunta_actual_texto.strip()
                    frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                    clave_pregunta = f"T11_BATCH:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (TIPO 11)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

                    respuestas_lote_ia = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN LOTE TIPO 11 ENCONTRADA en memoria.");
                        respuestas_lote_ia = soluciones_correctas[clave_pregunta]
                    else:
                        # --- ¡NUEVA LÓGICA DE BIFURCACIÓN T11! ---
                        titulo_lower = pregunta_actual_texto.lower()
                        if "order the letters" in titulo_lower or "put in order" in titulo_lower:
                            # Use 24 spaces for indentation
                            print("      ¡T11 detectado como ANAGRAMA (T10)! Llamando a IA (Ordenar Palabra Lote)...")
                            # Usamos 'lista_frases_t11_raw' (ej: "NTESNI")
                            respuestas_ia_temp = ia_utils.obtener_palabras_ordenadas_lote(lista_frases_t11_raw)
                            if not respuestas_ia_temp or len(respuestas_ia_temp) != len(lista_de_tareas_escribir):
                                raise Exception("Fallo IA (Ordenar Lote, vía T11) o nº resp no coincide.")
                        
                        else:
                            # Use 24 spaces for indentation
                            print("      Llamando a IA (Escribir Opciones Lote)...")
                            # Usamos 'tareas_para_ia' (ej: "Frase ___")
                            tareas_para_ia = [{"frase": t["frase"]} for t in lista_de_tareas_escribir]
                            respuestas_ia_temp = ia_utils.obtener_respuestas_escribir_opciones_lote(contexto, pregunta_actual_texto, tareas_para_ia)
                            if not respuestas_ia_temp or len(respuestas_ia_temp) != len(lista_de_tareas_escribir):
                                raise Exception("Fallo IA (Escribir Opciones Lote) o nº resp no coincide.")
                        # --- FIN LÓGICA DE BIFURCACIÓN ---
                        
                        respuestas_lote_ia = respuestas_ia_temp
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia

                    print(f"Palabras (Opciones) a escribir: {respuestas_lote_ia}")
                    exito_global = True
                    if len(respuestas_lote_ia) != len(lista_de_tareas_escribir):
                        # Use 24 spaces for indentation
                        print("Error crítico T11: Número de respuestas IA no coincide con tareas.")
                        raise Exception("Fallo TIPO 11 - Mismatch respuestas/tareas")

                    for palabra_correcta, tarea in zip(respuestas_lote_ia, lista_de_tareas_escribir):
                        # Use 24 spaces for indentation
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
                            print(f"Error al escribir in input TIPO 11: {e}");
                            exito_global = False; break
                    if not exito_global: raise Exception("Fallo al escribir en inputs TIPO 11.")

                # --- ¡INICIO TIPO 12! ---
                # --- TIPO 12: DICTADO (ESCRIBIR + AUDIO) ---
                elif tipo_pregunta == "TIPO_12_DICTADO":
                    # Use 20 spaces for indentation
                    print("Tipo: DICTADO (TIPO 12 - Lote).");
                    input_elems = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_INPUT_ESCRIBIR))
                    if not input_elems:
                        raise Exception("Error TIPO 12: No se encontraron inputs.")
                    
                    # ¡NO INTENTAMOS SACAR HASH DE AUDIO! (src="blob:..." es inútil)
                    print("      Audio detectado (T12). El hash de audio se omitirá de la clave.")
                    audio_hash = "" # Dejar vacío.

                    num_tareas = len(input_elems)
                    print(f"Encontradas {num_tareas} tareas TIPO 12.")
                    lista_de_tareas_escribir = []
                    lista_frases_t12 = [] # Usamos t12 para diferenciar de t11

                    for i, input_elem_actual in enumerate(input_elems):
                        # Use 24 spaces for indentation
                        try:
                            # Use 28 spaces for indentation
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", input_elem_actual); time.sleep(0.1)
                            # Reusamos el selector de T11, asumiendo que es un <p> cercano
                            frase_elem = input_elem_actual.find_element(*sel.SELECTOR_FRASE_T11) 
                            frase_texto = frase_elem.text.strip()
                            if not frase_texto: frase_texto = "TYPE_THE_SENTENCE_PLACEHOLDER" # Fallback

                            frase_para_ia = frase_texto + " ___"
                            print(f"      Tarea {i+1}: Frase='{frase_para_ia}'")
                            lista_de_tareas_escribir.append({"frase": frase_para_ia, "input_elem": input_elem_actual})
                            lista_frases_t12.append(frase_para_ia)

                        except (NoSuchElementException, TimeoutException) as e_t12:
                             # Use 28 spaces for indentation
                             print(f"WARN TIPO 12: Tarea {i+1} sin frase (normal). Usando fallback. ({e_t12})")
                             frase_para_ia = "TYPE_THE_SENTENCE_PLACEHOLDER ___"
                             lista_de_tareas_escribir.append({"frase": frase_para_ia, "input_elem": input_elem_actual})
                             lista_frases_t12.append(frase_para_ia)

                    if not lista_de_tareas_escribir: raise Exception("No se recolectaron tareas TIPO 12 válidas.")

                    titulo_limpio = pregunta_actual_texto.strip()
                    frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                    
                    # --- ¡CLAVE BASADA SÓLO EN TEXTO! ---
                    clave_pregunta = f"T12_DICTADO:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"
                    print(f"      Clave T12 generada: {clave_pregunta}")

                    # --- CHEQUEO DE BUCLE ATASCADO (TIPO 12) ---
                    # ¡ELIMINADO! La lógica de rotación maneja esto.
                    # (Como pediste en el mensaje anterior)
                    # --- FIN CHEQUEO DE BUCLE ATASCADO ---

                    # --- ¡INICIO LÓGICA DE ROTACIÓN T12! ---
                    respuestas_lote_ia = [] # Inicializar
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN(ES) T12 ENCONTRADA(S) en memoria.");
                        lista_soluciones = soluciones_correctas[clave_pregunta] # Es una lista de listas, ej: [ ["FRASE A"], ["FRASE B"] ]
                        ultimo_intento = preguntas_ya_vistas.get(clave_pregunta) # Es una lista, ej: ["FRASE A"]

                        # Auto-corrección de memoria antigua (si guardamos mal antes)
                        if not isinstance(lista_soluciones, list) or (lista_soluciones and not isinstance(lista_soluciones[0], list)):
                            # Use 28 spaces for indentation
                            print(f"      WARN: Solución T12 no era lista de listas. Auto-corrigiendo. '{lista_soluciones}'")
                            if isinstance(lista_soluciones, list) and not (lista_soluciones and isinstance(lista_soluciones[0], list)):
                                # Use 32 spaces for indentation
                                lista_soluciones = [lista_soluciones] # Convertir ["A"] a [ ["A"] ]
                            else:
                                # Use 32 spaces for indentation
                                lista_soluciones = [ [str(lista_soluciones)] ] # Convertir "A" a [ ["A"] ]
                            soluciones_correctas[clave_pregunta] = lista_soluciones
                            # No guardar en disco aquí, esperar al aprendizaje si falla
                        
                        if ultimo_intento and ultimo_intento in lista_soluciones:
                            # Use 28 spaces for indentation
                            indice = lista_soluciones.index(ultimo_intento)
                            indice_nuevo = (indice + 1) % len(lista_soluciones) # Rotar
                            respuestas_lote_ia = lista_soluciones[indice_nuevo]
                            print(f"      Rotando. Último intento: '{ultimo_intento[0]}'. Nuevo intento: '{respuestas_lote_ia[0]}'")
                        else:
                            # Use 28 spaces for indentation
                            respuestas_lote_ia = lista_soluciones[0]
                            print(f"      Iniciando desde el principio de la lista. Intentando: '{respuestas_lote_ia[0]}'")
                    
                    else:
                        # Use 24 spaces for indentation
                        print("      No hay solución T12. El bot no puede oír. Escribiendo '???' y esperando aprender.")
                        respuestas_lote_ia = ["???"] * len(lista_de_tareas_escribir) # ej: ["???"]
                    
                    # Guardar el intento actual (que es una lista, ej: ["???"] o ["RESPUESTA A"])
                    preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia
                    # --- FIN LÓGICA DE ROTACIÓN T12 ---

                    print(f"Frases (Dictado) a escribir: {respuestas_lote_ia}")
                    exito_global = True
                    if len(respuestas_lote_ia) != len(lista_de_tareas_escribir):
                        # Use 24 spaces for indentation
                        print("Error crítico T12: Número de respuestas IA no coincide con tareas.")
                        raise Exception("Fallo TIPO 12 - Mismatch respuestas/tareas")

                    for palabra_correcta, tarea in zip(respuestas_lote_ia, lista_de_tareas_escribir):
                        # Use 24 spaces for indentation
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
                            print(f"Error al escribir en input TIPO 12: {e}");
                            exito_global = False; break
                    if not exito_global: raise Exception("Fallo al escribir en inputs TIPO 12.")
                # --- ¡FIN TIPO 12! ---

                # --- TIPO DEFAULT: OPCIÓN MÚLTIPLE ---
                elif tipo_pregunta == "TIPO_DEFAULT_OM":
                    # Use 20 spaces for indentation
                    print("Tipo: OPCIÓN MÚLTIPLE (Default).");
                    opciones_elementos = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_OPCIONES))
                    opciones = [e.text.strip() for e in opciones_elementos if e.text and e.is_displayed()]
                    if not opciones: raise Exception("No opciones visibles.")

                    imagen_hash = ""
                    try:
                        # Use 24 spaces for indentation
                        imagenes_en_pregunta = driver.find_elements(By.XPATH, "//div[contains(@class,'card')]//img")
                        if not imagenes_en_pregunta:
                            # Use 28 spaces for indentation
                            print("      Hash Img (Intento 1) falló. Probando Intento 2 (global)...")
                            imagenes_en_pregunta = driver.find_elements(By.XPATH, "//div[.//button[translate(normalize-space(text()), 'CHECK', 'check')='check']]//img")

                        if imagenes_en_pregunta:
                            # Use 28 spaces for indentation
                            img_elem = imagenes_en_pregunta[0]
                            hash_img_actual = None
                            alt_text = img_elem.get_attribute("alt")
                            alt_text_limpio = alt_text.strip() if alt_text else ""
                            if alt_text_limpio and alt_text_limpio.lower() != "descripción de la imagen":
                                # Use 32 spaces for indentation
                                hash_img_actual = f"IMG_ALT:{alt_text_limpio}"
                                print(f"      Imagen detectada. Usando ALT='{alt_text_limpio}' -> Hash='{hash_img_actual}'")

                            if not hash_img_actual:
                                # Use 32 spaces for indentation
                                try:
                                    # Use 36 spaces for indentation
                                    size = img_elem.size
                                    width = size.get('width', 0)
                                    height = size.get('height', 0)
                                    if width > 0 and height > 0:
                                        # Use 40 spaces for indentation
                                        hash_img_actual = f"IMG_DIM:{width}x{height}"
                                        print(f"      Imagen detectada. ALT genérico/vacío. Usando Dimensiones='{width}x{height}' -> Hash='{hash_img_actual}'")
                                    else:
                                        # Use 40 spaces for indentation
                                        print(f"      WARN: ALT genérico/vacío Y Dimensiones 0x0. Dejando hash vacío.")
                                except Exception as e_size:
                                    # Use 36 spaces for indentation
                                    print(f"      WARN: ALT genérico/vacío. Error obteniendo dimensiones: {e_size}. Dejando hash vacío.")

                            if hash_img_actual:
                                # Use 32 spaces for indentation
                                imagen_hash = hash_img_actual
                        else:
                             # Use 28 spaces for indentation
                            print("      WARN: No se encontró ninguna imagen (Intentos 1 y 2). El hash de imagen estará vacío.")
                    except Exception as e_img:
                        # Use 24 spaces for indentation
                        print(f"      WARN: Excepción al extraer hash de imagen: {e_img}")

                    titulo_limpio_def = pregunta_actual_texto.strip() if "pregunta_sin_titulo" not in pregunta_actual_texto else contexto[:150]
                    opciones_limpias_sorted_def = sorted([o.strip() for o in opciones])
                    clave_pregunta = f"DEFAULT:{titulo_limpio_def}||{contexto_hash}||{body_hash}||{imagen_hash}||" + "|".join(opciones_limpias_sorted_def) # body_hash añadido

                    # --- ¡INICIO CHEQUEO DE BUCLE ATASCADO (DEFAULT)! ---
                    if clave_pregunta and clave_pregunta == ultima_clave_pregunta_procesada:
                        # Use 24 spaces for indentation
                        print(f"      ¡ALERTA! PREGUNTA REPETIDA DETECTADA (Clave: {clave_pregunta[:70]}...)")
                        print("      Se asume que es la última pregunta y está atascada. Refrescando PÁGINA...")
                        try:
                            # Use 28 spaces for indentation
                            driver.refresh()
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                            print("      Página refrescada. Reintentando...")
                            pregunta_actual_texto = ""
                            ultima_clave_pregunta_procesada = ""
                            respuesta_fue_incorrecta = False
                            continue
                        except Exception as e_refresh:
                            # Use 28 spaces for indentation
                            print(f"      ERROR CRÍTICO: No se pudo refrescar tras detectar bucle: {e_refresh}")
                            raise
                    # --- ¡FIN CHEQUEO DE BUCLE ATASCADO! ---

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
                try:
                    # Use 20 spaces for indentation
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_check)
                    time.sleep(0.3) # Pequeña pausa
                except Exception as scroll_e:
                    # Use 20 spaces for indentation
                    print(f"      WARN: No se pudo hacer scroll a CHECK: {scroll_e}")
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

                        # 1. Preparar datos (variables locales que deberían existir)
                        if tipo_pregunta == "TIPO_6_PARAGRAPH": preguntas_para_ia = [idea.split(":", 1)[1] for idea in lista_ideas_texto] if 'lista_ideas_texto' in locals() else None
                        elif tipo_pregunta == "TIPO_7_OM_CARD": preguntas_para_ia = [preg.split(":", 1)[1] for preg in lista_de_preguntas] if 'lista_de_preguntas' in locals() else None
                        elif tipo_pregunta == "TIPO_1_ORDENAR": preguntas_para_ia = lista_de_tareas_ordenar if 'lista_de_tareas_ordenar' in locals() else None
                        elif tipo_pregunta == "TIPO_2_COMPLETAR": preguntas_para_ia = lista_de_tareas_completar if 'lista_de_tareas_completar' in locals() else None
                        elif tipo_pregunta == "TIPO_3_TF_MULTI": preguntas_para_ia = [afirm.split(":", 1)[1] for afirm in lista_afirmaciones_texto] if 'lista_afirmaciones_texto' in locals() else None
                        elif tipo_pregunta in ["TIPO_DEFAULT_OM", "TIPO_9_AUDIO", "TIPO_5_TF_SINGLE"]: opciones_para_ia = opciones if 'opciones' in locals() else None
                        elif tipo_pregunta == "TIPO_10_ESCRIBIR": preguntas_para_ia = lista_palabras_desordenadas_raw if 'lista_palabras_desordenadas_raw' in locals() else None
                        elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES": preguntas_para_ia = [{"frase": f} for f in lista_frases_t11] if 'lista_frases_t11' in locals() else None
                        elif tipo_pregunta == "TIPO_12_DICTADO": preguntas_para_ia = [{"frase": f} for f in lista_frases_t12] if 'lista_frases_t12' in locals() else None # ¡NUEVO T12!
                        elif tipo_pregunta in ["TIPO_4_EMPAREJAR", "TIPO_8_IMAGEN"]:
                            preguntas_para_ia = palabras_clave if 'palabras_clave' in locals() else None
                            opciones_para_ia = definiciones if 'definiciones' in locals() else None

                        # Regenerar clave correcta para aprendizaje
                        clave_pregunta_aprendizaje = None
                        if tipo_pregunta == "TIPO_6_PARAGRAPH" and 'lista_ideas_texto' in locals(): clave_pregunta_aprendizaje = "|".join([p.strip() for p in lista_ideas_texto])
                        elif tipo_pregunta == "TIPO_7_OM_CARD" and 'lista_de_preguntas' in locals(): clave_pregunta_aprendizaje = "|".join([p.strip() for p in lista_de_preguntas])
                        elif tipo_pregunta == "TIPO_1_ORDENAR" and 'lista_de_claves_individuales' in locals(): clave_pregunta_aprendizaje = "|".join([p.strip() for p in lista_de_claves_individuales])
                        elif tipo_pregunta == "TIPO_2_COMPLETAR" and 'lista_de_tareas_completar' in locals():
                             titulo_limpio = pregunta_actual_texto.strip()
                             frases_para_clave = sorted([t["frase"] for t in lista_de_tareas_completar])
                             frases_hash_str = "|".join(frases_para_clave)
                             clave_pregunta_aprendizaje = f"T2_BATCH:{titulo_limpio}||{contexto_hash}||FRASES:{frases_hash_str}"
                        elif tipo_pregunta == "TIPO_3_TF_MULTI" and 'lista_afirmaciones_texto' in locals(): clave_pregunta_aprendizaje = "|".join([p.strip() for p in lista_afirmaciones_texto])
                        elif tipo_pregunta == "TIPO_DEFAULT_OM" and 'opciones' in locals():
                            titulo_limpio = pregunta_actual_texto.strip() if "pregunta_sin_titulo" not in pregunta_actual_texto else contexto[:150]
                            opciones_limpias_sorted = sorted(opciones)
                            clave_pregunta_aprendizaje = f"DEFAULT:{titulo_limpio}||{contexto_hash}||{body_hash}||{imagen_hash}||" + "|".join(opciones_limpias_sorted)
                        elif tipo_pregunta == "TIPO_9_AUDIO" and 'opciones' in locals():
                            titulo_limpio = pregunta_actual_texto.strip() if "pregunta_sin_titulo" not in pregunta_actual_texto else contexto[:150]
                            opciones_limpias_sorted = sorted(opciones)
                            clave_pregunta_aprendizaje = f"T9:{titulo_limpio}||{contexto_hash}||{body_hash}||{audio_hash}||" + "|".join(opciones_limpias_sorted) # T9 Mantiene su lógica original
                        elif tipo_pregunta == "TIPO_5_TF_SINGLE":
                            titulo_limpio = pregunta_actual_texto.strip()
                            clave_pregunta_aprendizaje = f"T5:{titulo_limpio}||{contexto_hash}||True|False"
                        elif tipo_pregunta == "TIPO_10_ESCRIBIR" and 'lista_de_tareas_escribir' in locals():
                             titulo_limpio = pregunta_actual_texto.strip()
                             claves_ordenadas_str = "|".join(sorted([t["letras_clave"] for t in lista_de_tareas_escribir]))
                             clave_pregunta_aprendizaje = f"T10_BATCH:{titulo_limpio}||{claves_ordenadas_str}"
                        elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES" and 'lista_de_tareas_escribir' in locals():
                             titulo_limpio = pregunta_actual_texto.strip()
                             frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                             clave_pregunta_aprendizaje = f"T11_BATCH:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"
                        # --- ¡NUEVO T12 APRENDIZAJE! ---
                        elif tipo_pregunta == "TIPO_12_DICTADO" and 'lista_de_tareas_escribir' in locals():
                             titulo_limpio = pregunta_actual_texto.strip()
                             frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                             # ¡audio_hash OMITIDO INTENCIONALMENTE!
                             clave_pregunta_aprendizaje = f"T12_DICTADO:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"
                        # --- FIN NUEVO T12 ---
                        elif tipo_pregunta == "TIPO_4_EMPAREJAR" and 'definiciones' in locals():
                             titulo_limpio = pregunta_actual_texto.strip()
                             defs_limpias_sorted = sorted(definiciones)
                             clave_pregunta_aprendizaje = f"T4:{titulo_limpio}||" + "|".join(defs_limpias_sorted)
                        elif tipo_pregunta == "TIPO_8_IMAGEN" and 'definiciones' in locals() and 'palabras_clave' in locals():
                             titulo_limpio = pregunta_actual_texto.strip()
                             defs_limpias_sorted = sorted(definiciones)
                             claves_unicas_ordenados_str = "|".join(sorted(palabras_clave))
                             clave_pregunta_aprendizaje = f"T8:{titulo_limpio}||{claves_unicas_ordenados_str}||" + "|".join(defs_limpias_sorted)

                        # 2. Extraer solución
                        if tipo_pregunta in ["TIPO_1_ORDENAR", "TIPO_2_COMPLETAR", "TIPO_3_TF_MULTI", "TIPO_6_PARAGRAPH", "TIPO_7_OM_CARD", "TIPO_10_ESCRIBIR", "TIPO_11_ESCRIBIR_OPCIONES", "TIPO_12_DICTADO"] and clave_pregunta_aprendizaje and contenido_modal and preguntas_para_ia:
                            # Use 28 spaces for indentation
                            solucion_lista_ordenada = None
                            if tipo_pregunta == "TIPO_3_TF_MULTI": solucion_lista_ordenada = ia_utils.extraer_solucion_lote_tf(contenido_modal, preguntas_para_ia)
                            elif tipo_pregunta == "TIPO_2_COMPLETAR":
                                tareas_aprendizaje_t2 = [{"frase": t["frase"], "opciones": t["opciones"]} for t in preguntas_para_ia]
                                solucion_lista_ordenada = ia_utils.extraer_solucion_lote_completar(contenido_modal, tareas_aprendizaje_t2)
                            elif tipo_pregunta == "TIPO_1_ORDENAR":
                                solucion_lote_ordenar = []
                                exito_aprendizaje_lote = True
                                for i, tarea_ind in enumerate(preguntas_para_ia):
                                    sol_individual = ia_utils.extraer_solucion_ordenar(contenido_modal, tarea_ind["frases"])
                                    if not sol_individual: exito_aprendizaje_lote = False; break
                                    solucion_lote_ordenar.append(sol_individual)
                                if exito_aprendizaje_lote: solucion_lista_ordenada = solucion_lote_ordenar
                            elif tipo_pregunta == "TIPO_10_ESCRIBIR": solucion_lista_ordenada = ia_utils.extraer_solucion_lote_escribir(contenido_modal, preguntas_para_ia)
                            
                            # --- ¡INICIO EXTRACCIÓN SEPARADA T11/T12! ---
                            elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES":
                                # --- ¡BIFURCACIÓN T11! ---
                                titulo_lower = pregunta_actual_texto.lower()
                                if "order the letters" in titulo_lower or "put in order" in titulo_lower:
                                    print("      Usando extractor T10 (Anagrama) para T11...")
                                    preguntas_para_ia_raw = lista_frases_t11_raw if 'lista_frases_t11_raw' in locals() else None
                                    if preguntas_para_ia_raw:
                                        solucion_lista_ordenada = ia_utils.extraer_solucion_lote_escribir(contenido_modal, preguntas_para_ia_raw)
                                    else:
                                        print(f"      ERROR APRENDIZAJE: No se encontraron frases raw T11 para la IA.")
                                else:
                                    if preguntas_para_ia:
                                        solucion_lista_ordenada = ia_utils.extraer_solucion_lote_escribir_opciones(contenido_modal, preguntas_para_ia)
                                    else:
                                        print(f"      ERROR APRENDIZAJE: No se encontraron frases T11 para la IA.")

                            elif tipo_pregunta == "TIPO_12_DICTADO":
                                if preguntas_para_ia:
                                    # --- ¡CAMBIO CLAVE! LLAMAR A LA NUEVA FUNCIÓN ---
                                    solucion_lista_ordenada = ia_utils.extraer_solucion_lote_dictado(contenido_modal, preguntas_para_ia) 
                                else:
                                    print(f"      ERROR APRENDIZAJE: No se encontraron frases T12 para la IA.")
                            # --- ¡FIN EXTRACCIÓN SEPARADA! ---
                            
                            else: # T6 y T7
                                solucion = ia_utils.extraer_solucion_del_error(contenido_modal, preguntas_para_ia)
                                if solucion:
                                    solucion_lista_ordenada_temp = []
                                    mapeo_fallido = False
                                    for p_limpio in preguntas_para_ia:
                                        if p_limpio in solucion: solucion_lista_ordenada_temp.append(str(solucion[p_limpio]).strip())
                                        else:
                                            p_alt1 = p_limpio + " "; p_alt2 = p_limpio.strip()
                                            if p_alt1 in solucion: solucion_lista_ordenada_temp.append(str(solucion[p_alt1]).strip())
                                            elif p_alt2 in solucion: solucion_lista_ordenada_temp.append(str(solucion[p_alt2]).strip())
                                            else: mapeo_fallido = True; break
                                    if not mapeo_fallido: solucion_lista_ordenada = solucion_lista_ordenada_temp

                            if solucion_lista_ordenada:
                                # Use 32 spaces for indentation
                                print(f"      ¡SOLUCIÓN LOTE APRENDIDA! -> {solucion_lista_ordenada}");
                                if tipo_pregunta == "TIPO_2_COMPLETAR":
                                    # Use 36 spaces for indentation
                                    frases_clave_aprender = [t["frase"] for t in preguntas_para_ia]
                                    solucion_aprendida = dict(zip(frases_clave_aprender, solucion_lista_ordenada))
                                    print(f"      Guardando como DICT: {solucion_aprendida}")
                                else:
                                    # Use 36 spaces for indentation
                                    solucion_aprendida = solucion_lista_ordenada
                            else:
                                # Use 32 spaces for indentation
                                print("      IA (Lote) no pudo extraer o validar la solución.")


                        elif tipo_pregunta in ["TIPO_4_EMPAREJAR", "TIPO_8_IMAGEN"] and clave_pregunta_aprendizaje and contenido_modal and preguntas_para_ia and opciones_para_ia:
                            # Use 28 spaces for indentation
                            tipo_num_str = ''.join(filter(str.isdigit, tipo_pregunta))
                            print(f"      Enviando texto a IA (Aprendizaje Emparejar TIPO {tipo_num_str}) para extraer solución...");
                            dict_solucion = ia_utils.extraer_solucion_emparejar(contenido_modal, preguntas_para_ia, opciones_para_ia)
                            if dict_solucion:
                                # Use 32 spaces for indentation
                                solucion_aprendida_lista = []
                                for clave_real in preguntas_para_ia:
                                    # Use 36 spaces for indentation
                                    clave_encontrada = None
                                    if clave_real in dict_solucion: clave_encontrada = clave_real
                                    elif clave_real.strip() in dict_solucion: clave_encontrada = clave_real.strip()

                                    if clave_encontrada:
                                        # Use 40 spaces for indentation
                                        solucion_aprendida_lista.append(dict_solucion[clave_encontrada])
                                    else:
                                        # Use 40 spaces for indentation
                                        print(f"      ERROR APRENDIZAJE T{tipo_num_str}: No se encontró la clave '{clave_real}' en el dict de la IA.")
                                        raise Exception(f"Fallo al mapear dict de aprendizaje T{tipo_num_str} a lista.")
                                solucion_aprendida = solucion_aprendida_lista
                            else:
                                # Use 32 spaces for indentation
                                solucion_aprendida = None


                        elif tipo_pregunta in ["TIPO_5_TF_SINGLE", "TIPO_DEFAULT_OM", "TIPO_9_AUDIO"] and clave_pregunta_aprendizaje and contenido_modal and opciones_para_ia:
                            # Use 28 spaces for indentation
                            print(f"      Enviando texto a IA (Simple) para extraer solución (Tipo: {tipo_pregunta})...");
                            solucion_simple = ia_utils.extraer_solucion_simple(contenido_modal, opciones_para_ia)
                            if solucion_simple:
                                # Use 32 spaces for indentation
                                print(f"      ¡SOLUCIÓN SIMPLE APRENDIDA! -> {solucion_simple}");
                                solucion_aprendida = solucion_simple.strip()
                            else: print("      IA (Simple) no pudo extraer solución.")


                        # --- ¡INICIO LÓGICA DE GUARDADO T12! ---
                        if clave_pregunta_aprendizaje and solucion_aprendida:
                           # Use 28 spaces for indentation
                           
                           # 1. Normalizar la solución aprendida
                           solucion_individual_aprendida = None
                           if tipo_pregunta in ["TIPO_9_AUDIO", "TIPO_DEFAULT_OM", "TIPO_5_TF_SINGLE"]:
                                solucion_individual_aprendida = str(solucion_aprendida).strip()
                           else: # T1, T3, T4, T6, T7, T8, T10, T11, T12...
                                solucion_individual_aprendida = solucion_aprendida # Es una lista, ej: ["A", "B"] o ["FRASE"]
                           
                           # 2. Obtener lista de soluciones existente
                           lista_existente = soluciones_correctas.get(clave_pregunta_aprendizaje)
                           
                           # 3. Lógica de guardado
                           if tipo_pregunta == "TIPO_2_COMPLETAR": # T2 usa Dict, lógica especial
                                # Use 32 spaces for indentation
                                if isinstance(lista_existente, dict) and isinstance(solucion_aprendida, dict):
                                    lista_existente.update(solucion_aprendida)
                                    soluciones_correctas[clave_pregunta_aprendizaje] = lista_existente
                                    print(f"      Memoria T2 fusionada: {solucion_aprendida}")
                                else:
                                    soluciones_correctas[clave_pregunta_aprendizaje] = solucion_aprendida
                                    print(f"      Memoria T2 guardada/sobrescrita: {solucion_aprendida}")
                                guardar_memoria_en_disco()
                           
                           elif tipo_pregunta == "TIPO_12_DICTADO":
                                # Use 32 spaces for indentation
                                # ¡LÓGICA DE ROTACIÓN T12!
                                # `solucion_individual_aprendida` es una lista, ej: ["FRASE A"]
                                
                                if not isinstance(lista_existente, list):
                                    # Use 36 spaces for indentation
                                    print(f"      Memoria T12 no era lista. Creando nueva lista.")
                                    lista_existente = []
                                
                                if solucion_individual_aprendida not in lista_existente:
                                    # Use 36 spaces for indentation
                                    print(f"      ¡Nueva solución T12 aprendida! Añadiendo a la lista: {solucion_individual_aprendida}")
                                    lista_existente.append(solucion_individual_aprendida)
                                    soluciones_correctas[clave_pregunta_aprendizaje] = lista_existente
                                    guardar_memoria_en_disco()
                                else:
                                    # Use 36 spaces for indentation
                                    print("      WARN: La solución T12 aprendida ya estaba en la lista. No se guarda.")
                                    
                           else: # T1, T3, T4, T5, T6, T7, T8, T9, T10, T11, DEFAULT
                                # Use 32 spaces for indentation
                                # Lógica de guardado estándar (sobrescribir)
                                soluciones_correctas[clave_pregunta_aprendizaje] = solucion_individual_aprendida
                                print(f"      Memoria guardada (Estándar): {solucion_individual_aprendida}")
                                guardar_memoria_en_disco()
                        
                        else: # No se pudo aprender
                           # Use 28 spaces for indentation
                           print("      WARN: No se pudo aprender la solución (clave o solución vacía).")
                        # --- ¡FIN LÓGICA DE GUARDADO T12! ---


                    # --- CASO 2: RESPUESTA CORRECTA ---
                    elif "correct" in titulo_modal or "great" in titulo_modal:
                        # Use 24 spaces for indentation
                        print(f"      Respuesta CORRECTA detectada (Modal: {titulo_modal}).")
                        clave_pregunta_acierto = None

                        # Regenerar clave correcta para guardar el acierto si es necesario
                        if tipo_pregunta == "TIPO_10_ESCRIBIR":
                             # Use 28 spaces for indentation
                             titulo_limpio = pregunta_actual_texto.strip()
                             if 'lista_de_tareas_escribir' in locals() and lista_de_tareas_escribir:
                                 claves_ordenadas_str = "|".join(sorted([t["letras_clave"] for t in lista_de_tareas_escribir]))
                                 clave_pregunta_acierto = f"T10_BATCH:{titulo_limpio}||{claves_ordenadas_str}"
                        elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES":
                             # Use 28 spaces for indentation
                             titulo_limpio = pregunta_actual_texto.strip()
                             if 'lista_de_tareas_escribir' in locals() and lista_de_tareas_escribir:
                                 frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                                 clave_pregunta_acierto = f"T11_BATCH:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"
                        # --- ¡NUEVO T12 ACIERTO! ---
                        elif tipo_pregunta == "TIPO_12_DICTADO":
                             # Use 28 spaces for indentation
                             titulo_limpio = pregunta_actual_texto.strip()
                             if 'lista_de_tareas_escribir' in locals() and lista_de_tareas_escribir:
                                 # Use 32 spaces for indentation
                                 frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                                 # ¡audio_hash OMITIDO INTENCIONALMENTE!
                                 clave_pregunta_acierto = f"T12_DICTADO:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"
                        # --- FIN NUEVO T12 ---
                        elif tipo_pregunta == "TIPO_8_IMAGEN":
                            # Use 28 spaces for indentation
                            titulo_limpio = pregunta_actual_texto.strip()
                            if 'definiciones' in locals() and 'palabras_clave' in locals():
                                 defs_limpias_sorted = sorted([d.strip() for d in definiciones])
                                 claves_unicas_ordenados_str = "|".join(sorted(palabras_clave))
                                 clave_pregunta_acierto = f"T8:{titulo_limpio}||{claves_unicas_ordenados_str}||" + "|".join(defs_limpias_sorted)
                        elif tipo_pregunta == "TIPO_2_COMPLETAR":
                             # Use 28 spaces for indentation
                             titulo_limpio = pregunta_actual_texto.strip()
                             if 'lista_de_tareas_completar' in locals() and lista_de_tareas_completar:
                                 frases_para_clave = sorted([t["frase"] for t in lista_de_tareas_completar])
                                 frases_hash_str = "|".join(frases_para_clave)
                                 clave_pregunta_acierto = f"T2_BATCH:{titulo_limpio}||{contexto_hash}||FRASES:{frases_hash_str}"
                        elif clave_pregunta: # Usar la clave original generada al inicio si no se regeneró
                            # Use 28 spaces for indentation
                           clave_pregunta_acierto = clave_pregunta.strip()

                        # --- ¡INICIO LÓGICA DE GUARDADO T12 (ACIERTO)! ---
                        if clave_pregunta_acierto:
                            # Use 28 spaces for indentation
                            respuesta_correcta_actual = preguntas_ya_vistas.get(clave_pregunta_acierto)
                            
                            if respuesta_correcta_actual is None:
                               # Use 32 spaces for indentation
                               print(f"      WARN: Acierto, pero no se encontró la respuesta en 'preguntas_ya_vistas' para clave: {clave_pregunta_acierto}")
                            
                            elif tipo_pregunta == "TIPO_2_COMPLETAR":
                               # Use 32 spaces for indentation
                               # (La lógica T2 existente está bien)
                                if not isinstance(respuesta_correcta_actual, dict):
                                    print(f"      ERROR Acierto T2: La respuesta guardada no es un dict: {respuesta_correcta_actual}")
                                elif clave_pregunta_acierto in soluciones_correctas:
                                    memoria_existente = soluciones_correctas[clave_pregunta_acierto]
                                    nuevas_frases_count = 0
                                    if isinstance(memoria_existente, dict):
                                         for frase, respuesta in respuesta_correcta_actual.items():
                                             if frase not in memoria_existente:
                                                 memoria_existente[frase] = respuesta
                                                 print(f"      ¡SOLUCIÓN T2 (frase) APRENDIDA! -> {frase}: {respuesta}")
                                                 nuevas_frases_count += 1
                                         if nuevas_frases_count > 0:
                                             soluciones_correctas[clave_pregunta_acierto] = memoria_existente
                                             guardar_memoria_en_disco()
                                         else:
                                             print("      La solución T2 (frase) ya estaba en memoria. No se necesita guardar.")
                                    else:
                                        print(f"      WARN Acierto T2: Memoria existente no era dict. Sobrescribiendo con: {respuesta_correcta_actual}")
                                        soluciones_correctas[clave_pregunta_acierto] = respuesta_correcta_actual
                                        guardar_memoria_en_disco()
                                else:
                                    print(f"      Guardando nuevo acierto (Lote T2 Completo) en memoria...")
                                    soluciones_correctas[clave_pregunta_acierto] = respuesta_correcta_actual
                                    print(f"      ¡SOLUCIÓN (por acierto T2) APRENDIDA! -> {respuesta_correcta_actual}")
                                    guardar_memoria_en_disco()
                            
                            elif clave_pregunta_acierto not in soluciones_correctas:
                               # Use 32 spaces for indentation
                               # ¡NUEVO ACIERTO! Debemos guardarlo en el formato correcto.
                               try:
                                    # Use 36 spaces for indentation
                                    solucion_a_guardar = None
                                    
                                    # Normalizar respuesta (ej. mayúsculas)
                                    if tipo_pregunta == "TIPO_10_ESCRIBIR" and isinstance(respuesta_correcta_actual, list):
                                         respuesta_correcta_actual = [p.upper() for p in respuesta_correcta_actual]
                                    elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES" and isinstance(respuesta_correcta_actual, list):
                                         respuesta_correcta_actual = [p.upper() for p in respuesta_correcta_actual]
                                    elif tipo_pregunta == "TIPO_12_DICTADO" and isinstance(respuesta_correcta_actual, list): # ¡NUEVO T12!
                                         respuesta_correcta_actual = [p.upper() for p in respuesta_correcta_actual]
                                    elif isinstance(respuesta_correcta_actual, str):
                                         respuesta_correcta_actual = respuesta_correcta_actual.strip()
                                    
                                    # ¡Envolver en lista de listas para T12!
                                    if tipo_pregunta == "TIPO_12_DICTADO":
                                        # Use 40 spaces for indentation
                                        # `respuesta_correcta_actual` es una lista, ej: ["FRASE A"]
                                        # La guardamos como lista de listas: [ ["FRASE A"] ]
                                        solucion_a_guardar = [respuesta_correcta_actual]
                                        print(f"      ¡SOLUCIÓN (por acierto T12) APRENDIDA! Guardando como lista de listas -> {solucion_a_guardar}")
                                    else:
                                        # Use 40 spaces for indentation
                                        # Es otro tipo (T1, T3, T4, T5, T9, T10, T11, DEFAULT...).
                                        solucion_a_guardar = respuesta_correcta_actual
                                        print(f"      ¡SOLUCIÓN (por acierto Estándar) APRENDIDA! -> {solucion_a_guardar}")

                                    soluciones_correctas[clave_pregunta_acierto] = solucion_a_guardar
                                    guardar_memoria_en_disco()
                               except Exception as e_acierto:
                                    # Use 36 spaces for indentation
                                    print(f"      WARN: Error guardando acierto: {e_acierto}")
                            else: # Ya estaba en memoria
                                 # Use 32 spaces for indentation
                                 print("      La solución ya estaba en memoria. No se necesita guardar.")
                        else: # clave_pregunta_acierto es None
                             print("      WARN Acierto: No se pudo generar/obtener clave para guardar el acierto.")
                        # --- ¡FIN LÓGICA DE GUARDADO T12 (ACIERTO)! ---

                except Exception as e:
                    # Use 20 spaces for indentation
                    print(f"      WARN: No se pudo leer modal o aprender. {e}")

                print("Clic OK..."); boton_ok.click()
                print("Respuesta enviada! Esperando que desaparezca modal..."); wait_long.until(EC.invisibility_of_element_located(sel.SELECTOR_OK))

                # --- LÓGICA POST-PREGUNTA ---
                # Usar la clave que se GENERÓ al inicio de la iteración actual para guardarla como "última procesada"
                if clave_pregunta:
                    # Use 20 spaces for indentation
                    ultima_clave_pregunta_procesada = clave_pregunta
                    print(f"      * Guardando última clave: {ultima_clave_pregunta_procesada[:70]}...")
                else:
                    # Use 20 spaces for indentation
                    print("      WARN: No se generó clave_pregunta en esta iteración. Reseteando tracker.")
                    ultima_clave_pregunta_procesada = ""

                respuesta_fue_incorrecta = False # Resetear siempre después de procesar OK
                pregunta_actual_texto = "" # Resetear para forzar relectura del título

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
