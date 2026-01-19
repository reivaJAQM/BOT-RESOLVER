import time
import json
import random
import copy
import os # Para basename en fallback
import hashlib # <--- ¡AGREGA ESTO!
from urllib.parse import urlparse # Mantener para fallback de audio
from collections import defaultdict # Para contador de desambiguación
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, JavascriptException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import ActionChains

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
    wait_manual = WebDriverWait(driver, 300) # ¡NUEVO! 5 minutos para intervención manual
    print("Navegador Listo!")
except Exception as e:
    # Use 4 spaces for indentation
    print(f"Error iniciando navegador: {e}"); exit()

# --- INICIO DE LA MEMORIA DEL BOT ---
preguntas_ya_vistas = {}
opciones_ya_vistas = {}
soluciones_correctas = {}
tracker_colisiones_t8 = defaultdict(int)
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
        lista_tareas_multi_om = [] # <--- ¡AGREGA ESTO!
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
                    wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CHECK))
                    print("      Botón 'CHECK' detectado. Página cargada.")
                except TimeoutException:
                    # Use 20 spaces for indentation
                    # --- ¡PROTOCOLO DE ESCAPE V2 (CON AUTO-LOGIN)! ---
                    print("\n" + "!"*50)
                    print("      ALERTA: Bot atascado (Sin CHECK/CONTINUE).")
                    print(f"      Ejecutando ESCAPE -> Ir a: {config.URL_INICIAL}")
                    print("!"*50 + "\n")
                    
                    try:
                        driver.get(config.URL_INICIAL)
                        print("      Navegación forzada. Verificando estado de sesión...")
                        
                        # 1. Comprobar si la sesión sigue viva (¿Vemos las lecciones?)
                        try:
                            WebDriverWait(driver, 5).until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
                            print("      ¡Sesión activa! Lista de lecciones encontrada.")
                            break # Todo bien, salimos al menú principal para buscar la siguiente lección
                        except TimeoutException:
                            print("      WARN: No se ven las lecciones. ¿Sesión cerrada? Verificando...")

                        # 2. Si no vemos lecciones, intentamos RE-LOGUEAR
                        try:
                            # A) Intentar cerrar Pop-up (si existe)
                            try:
                                wait_short.until(EC.element_to_be_clickable(sel.SELECTOR_CERRAR_POPUP)).click()
                                print("      (Re-Login) Pop-up cerrado.")
                                time.sleep(1)
                            except TimeoutException:
                                pass # No había pop-up o ya se cerró
                            
                            # B) Buscar botón verde 'Inicia Sesión'
                            boton_login = wait_short.until(EC.element_to_be_clickable(sel.SELECTOR_INICIA_SESION_VERDE))
                            print("      ¡DETECTADO CIERRE DE SESIÓN! Iniciando re-login automático...")
                            boton_login.click()
                            
                            # C) Rellenar credenciales
                            print("      (Re-Login) Poniendo usuario/pass...")
                            wait_long.until(EC.visibility_of_element_located(sel.SELECTOR_USUARIO_INPUT)).send_keys(config.TU_USUARIO_EMAIL)
                            wait_long.until(EC.visibility_of_element_located(sel.SELECTOR_PASSWORD_INPUT)).send_keys(config.TU_CONTRASENA)
                            
                            # D) Enviar
                            wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_ACCEDER_AMARILLO)).click()
                            print("      (Re-Login) Enviado. Esperando acceso...")
                            
                            # E) Confirmar que entramos
                            wait_long.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
                            print("      ¡RECUPERACIÓN COMPLETA! Sesión restaurada.")
                            break # Éxito, salimos al menú principal

                        except Exception as e_login:
                            print(f"      FALLO CRÍTICO en Auto-Login: {e_login}")
                            print("      No se pudo recuperar la sesión. El bot se detendrá.")
                            raise # Si falla el login, no hay nada que hacer

                    except Exception as e_rec:
                        print(f"      Fallo crítico al navegar al inicio: {e_rec}")
                        raise

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
                
                # --- ¡NUEVO ORDEN DE DETECCIÓN! ---
                # Priorizar los tipos estructurales (Emparejar, Ordenar) antes que los tipos de contenido (Audio)
                
                elif len(driver.find_elements(*sel.SELECTOR_ANSWER_Q_CAJAS)) > 0: print("      Contenido detectado: [TIPO 7]"); tipo_pregunta = "TIPO_7_OM_CARD"
                elif len(driver.find_elements(*sel.SELECTOR_PARAGRAPH_CAJAS)) > 0: print("      Contenido detectado: [TIPO 6]"); tipo_pregunta = "TIPO_6_PARAGRAPH"
                
                
                elif len(driver.find_elements(*sel.SELECTOR_CAJAS_TF)) > 0:
                    num_cajas_tf = len(driver.find_elements(*sel.SELECTOR_CAJAS_TF))
                    if num_cajas_tf >= 1:
                        print(f"      Contenido detectado: [TIPO 3] ({num_cajas_tf} cajas)");
                        tipo_pregunta = "TIPO_3_TF_MULTI"
                    else:
                        print(f"      Contenido detectado: [TIPO 5] ({num_cajas_tf} caja)");
                        tipo_pregunta = "TIPO_5_TF_SINGLE"
                # ¡MOVER TIPO 8 y TIPO 4 AQUÍ! (ANTES DE TIPO 9)
                elif len(driver.find_elements(*sel.SELECTOR_IMAGEN_EMPAREJAR)) > 0 and len(driver.find_elements(*sel.SELECTOR_DEFINICIONES_AZULES_XPATH)) > 0: 
                    print("      Contenido detectado: [TIPO 8]"); tipo_pregunta = "TIPO_8_IMAGEN"
                elif len(driver.find_elements(*sel.SELECTOR_FILAS_EMPAREJAR)) > 0: 
                    print("      Contenido detectado: [TIPO 4]"); tipo_pregunta = "TIPO_4_EMPAREJAR"
                elif len(driver.find_elements(*sel.SELECTOR_CONTENEDOR_ORDENAR)) > 0: print("      Contenido detectado: [TIPO 1]"); tipo_pregunta = "TIPO_1_ORDENAR"

                # TIPO 9 (Audio) ahora va DESPUÉS de los tipos de emparejar
                # (Así, si una pregunta es T4 + Audio, se detecta como T4, que es correcto)
                elif len(audio_elem) > 0: 
                    print("      Contenido detectado: [TIPO 9]"); tipo_pregunta = "TIPO_9_AUDIO"

                
                
                elif len(driver.find_elements(*sel.SELECTOR_LINEAS_COMPLETAR)) > 0: print("      Contenido detectado: [TIPO 2]"); tipo_pregunta = "TIPO_2_COMPLETAR"
                
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
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", contenedor); time.sleep(0.1)
                        
                        # --- FIX: Guardar ID único del contenedor ---
                        contenedor_id = contenedor.get_attribute("data-rbd-droppable-id")
                        # --------------------------------------------

                        cajas_inicial = contenedor.find_elements(*sel.SELECTOR_CAJAS_ORDENAR)
                        frases_des_individual = []
                        map_id_a_texto_individual = {}
                        for i, c in enumerate(cajas_inicial):
                            try:
                                text_element = c.find_element(*sel.SELECTOR_TEXTO_CAJA_ORDENAR)
                                t = text_element.text.strip()
                                d_id = c.get_attribute("data-rbd-draggable-id")
                                if t and d_id:
                                    frases_des_individual.append(t)
                                    map_id_a_texto_individual[d_id] = t
                            except NoSuchElementException: continue
                        if not frases_des_individual:
                            print(f"Warn: Contenedor {k+1} sin frases. Omitiendo.")
                            continue
                        print(f"      Tarea {k+1} Frases: {frases_des_individual}")
                        frases_ordenadas_para_clave = sorted(frases_des_individual)
                        clave_ind = "|".join(frases_ordenadas_para_clave)
                        lista_de_claves_individuales.append(f"{k}:{clave_ind}")
                        
                        # Guardamos contenedor_id en la tarea
                        lista_de_tareas_ordenar.append({
                            "frases": frases_des_individual,
                            "map_id_a_texto": map_id_a_texto_individual,
                            "contenedor_elem": contenedor,
                            "contenedor_id": contenedor_id 
                        })
                    if not lista_de_tareas_ordenar: raise Exception("No se recolectaron tareas TIPO 1 válidas.")
                    clave_pregunta = "|".join(lista_de_claves_individuales)

                    # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 1) ELIMINADO! ---

                    lista_ordenes_ia = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN(ES) LOTE TIPO 1 ENCONTRADA(S) en memoria.");
                        # --- INICIO LÓGICA DE ROTACIÓN (LOTE) ---
                        lista_soluciones_lote = soluciones_correctas[clave_pregunta] # Es una lista de listas, ej: [ [["A"],["B"]], [["C"],["D"]] ]
                        ultimo_intento_lote = preguntas_ya_vistas.get(clave_pregunta) # Es una lista, ej: [["A"],["B"]]

                        # Auto-corrección de memoria antigua (si guardamos mal antes)
                        is_old_format = False
                        if (isinstance(lista_soluciones_lote, list) and 
                            lista_soluciones_lote and 
                            isinstance(lista_soluciones_lote[0], list) and 
                            lista_soluciones_lote[0] and 
                            isinstance(lista_soluciones_lote[0][0], str)):
                        
                            is_old_format = True # Detecta formato antiguo: list[list[str]]

                        if not isinstance(lista_soluciones_lote, list) or is_old_format:
                            # Use 28 spaces for indentation
                            print(f"      WARN: Solución Lote T1 no era lista de listas (o era formato antiguo). Auto-corrigiendo.")
                            # La única corrección necesaria es envolverla
                            lista_soluciones_lote = [lista_soluciones_lote] 
                            soluciones_correctas[clave_pregunta] = lista_soluciones_lote
                        
                        if ultimo_intento_lote and ultimo_intento_lote in lista_soluciones_lote:
                            # Use 28 spaces for indentation
                            indice = lista_soluciones_lote.index(ultimo_intento_lote)
                            indice_nuevo = (indice + 1) % len(lista_soluciones_lote) # Rotar
                            lista_ordenes_ia = lista_soluciones_lote[indice_nuevo]
                            print(f"      Rotando Lote T1. Último intento: '{ultimo_intento_lote}'. Nuevo intento: '{lista_ordenes_ia}'")
                        else:
                            # Use 28 spaces for indentation
                            lista_ordenes_ia = lista_soluciones_lote[0]
                            print(f"      Iniciando desde el principio de la lista Lote T1. Intentando: '{lista_ordenes_ia}'")
                        
                        preguntas_ya_vistas[clave_pregunta] = lista_ordenes_ia # Guardar este intento (lista)
                        # --- FIN LÓGICA DE ROTACIÓN (LOTE) ---
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
                    
                    # --- INICIO REEMPLAZO: EJECUCIÓN VÍA JAVASCRIPT (DOM APPEND) CON ID ROBUSTO ---
                    print(f"      Órdenes a aplicar (JS): {lista_ordenes_ia}")
                    
                    for i_cont, solucion in enumerate(lista_ordenes_ia):
                        print(f"      Ordenando contenedor {i_cont+1} con JS...")
                        try:
                            # 1. Obtener el contenedor fresco USANDO SU ID (Más robusto que el índice)
                            target_id = lista_de_tareas_ordenar[i_cont].get("contenedor_id")
                            contenedor_actual = None
                            
                            if target_id:
                                try:
                                    # Buscamos específicamente el div con ese droppable-id
                                    contenedor_actual = driver.find_element(By.XPATH, f"//div[@data-rbd-droppable-id='{target_id}']")
                                except NoSuchElementException:
                                    print(f"      WARN: No se pudo re-encontrar contenedor por ID '{target_id}'. Intentando fallback por índice.")
                            
                            # Fallback: Si no hay ID o falla, usamos la lógica antigua de índice
                            if not contenedor_actual:
                                contenedores_frescos = driver.find_elements(*sel.SELECTOR_CONTENEDOR_ORDENAR)
                                if i_cont < len(contenedores_frescos):
                                    contenedor_actual = contenedores_frescos[i_cont]

                            if not contenedor_actual:
                                print(f"      ERR: Contenedor {i_cont+1} perdido definitivamente.")
                                continue

                            # Scroll al contenedor actual para asegurar carga
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", contenedor_actual)

                            # 2. Iterar sobre la solución CORRECTA
                            for palabra_objetivo in solucion:
                                # Buscar la caja que contiene esa palabra DENTRO del contenedor actual fresco
                                cajas_en_contenedor = contenedor_actual.find_elements(*sel.SELECTOR_CAJAS_ORDENAR)
                                elemento_a_mover = None
                                
                                for caja in cajas_en_contenedor:
                                    # Normalizamos texto para comparación
                                    if caja.text.strip() == palabra_objetivo:
                                        elemento_a_mover = caja
                                        break
                                
                                if elemento_a_mover:
                                    # 3. MOVER AL FINAL (appendChild)
                                    driver.execute_script("arguments[0].appendChild(arguments[1]);", contenedor_actual, elemento_a_mover)
                                    time.sleep(0.05) 
                                else:
                                    print(f"      WARN: No se encontró la caja '{palabra_objetivo}' para mover en Contenedor {i_cont+1}.")
                            
                            time.sleep(0.5) 

                        except Exception as e_js:
                             print(f"      Error ordenando contenedor {i_cont+1} con JS: {e_js}")

                    print("      Ordenamiento JS finalizado.")
                    # --- FIN REEMPLAZO ---

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

                    # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 2) ELIMINADO! ---

                    respuestas_lote_ia = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN LOTE TIPO 2 ENCONTRADA en memoria (Dict).");
                        # TIPO 2 usa un DICT, no una lista de rotación, porque las claves (frases) son únicas.
                        # La lógica de rotación no aplica aquí.
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
                    # 1. Recolectamos TODAS las cajas (incluso las ocultas/duplicadas)
                    todas_cajas = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_CAJAS_TF))
                    
                    # 2. FILTRO ANTI-FANTASMAS: Solo usamos las visibles
                    cajas_afirmacion = [c for c in todas_cajas if c.is_displayed()]
                    
                    # Fallback de seguridad: si todas parecen ocultas (raro), usamos la primera lista cruda
                    if not cajas_afirmacion and todas_cajas:
                        print("      WARN: Todas las cajas parecen ocultas. Usando lista sin filtrar.")
                        cajas_afirmacion = todas_cajas
                        
                    if not cajas_afirmacion: raise Exception("No se encontraron cajas True/False visibles.")
                    print(f"Encontradas {len(cajas_afirmacion)} afirmaciones VISIBLES (de {len(todas_cajas)} detectadas en total).")
                    lista_afirmaciones_texto = []
                    elementos_cajas_botones = []
                    textos_vistos_en_bloque = set() # Set para rastrear duplicados
                    
                    print("Recolectando afirmaciones...")
                    for k, caja in enumerate(cajas_afirmacion):
                        # Use 24 spaces for indentation
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            # 1. BUSCAR EL TEXTO (AFIRMACIÓN)
                            # Buscamos el span con texto gris (clase típica de las preguntas)
                            try:
                                texto_afirmacion_elem = caja.find_element(By.XPATH, ".//span[contains(@class, 'text-gray-700')]")
                            except NoSuchElementException:
                                # Fallback por si cambia la clase
                                texto_afirmacion_elem = caja.find_element(By.XPATH, ".//span")
                                
                            wait_short.until(EC.visibility_of(texto_afirmacion_elem))
                            texto_afirmacion = texto_afirmacion_elem.text.strip()
                            
                            # --- FILTRO ANTI-DUPLICADOS ---
                            # Si ya leímos este texto exacto en este lote, saltamos la caja
                            if texto_afirmacion in textos_vistos_en_bloque:
                                print(f"      [Filtro] Ignorando duplicado visual #{k+1} ('{texto_afirmacion[:15]}...')")
                                continue
                            textos_vistos_en_bloque.add(texto_afirmacion)
                            # ------------------------------
                            
                            # 2. BUSCAR EL BOTÓN TRUE (Flexible: TRUE o True)
                            try:
                                boton_true = caja.find_element(By.XPATH, ".//button[contains(normalize-space(), 'TRUE')]")
                            except NoSuchElementException:
                                boton_true = caja.find_element(By.XPATH, ".//button[contains(normalize-space(), 'True')]")
                            
                            # 3. BUSCAR EL BOTÓN FALSE (Flexible: FALSE o False)
                            try:
                                boton_false = caja.find_element(By.XPATH, ".//button[contains(normalize-space(), 'FALSE')]")
                            except NoSuchElementException:
                                boton_false = caja.find_element(By.XPATH, ".//button[contains(normalize-space(), 'False')]")

                            if texto_afirmacion:
                                # Use 32 spaces for indentation
                                clave_unica_afirmacion = f"{k}:{texto_afirmacion}"
                                lista_afirmaciones_texto.append(clave_unica_afirmacion)
                                elementos_cajas_botones.append((caja, boton_true, boton_false))
                                print(f"      Afirmación {len(lista_afirmaciones_texto)}: '{texto_afirmacion[:30]}...'")
                            else: print(f"Warn: Caja {k+1} sin texto.")
                        
                        except (NoSuchElementException, TimeoutException) as e_inner:
                            # Use 28 spaces for indentation
                            print(f"      [Info] Saltando caja {k+1} por error de lectura (probablemente oculta): {e_inner}")
                            continue
                    if not lista_afirmaciones_texto: raise Exception("No se pudieron recolectar afirmaciones T/F.")
                    clave_pregunta = "|".join(lista_afirmaciones_texto)

                    # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 3) ELIMINADO! ---

                    respuestas_tf_lote = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN(ES) LOTE T/F ENCONTRADA(S) en memoria.");
                        # --- INICIO LÓGICA DE ROTACIÓN (LOTE) ---
                        lista_soluciones_lote = soluciones_correctas[clave_pregunta] # Es una lista de listas, ej: [ ["T","F"], ["F","T"] ]
                        ultimo_intento_lote = preguntas_ya_vistas.get(clave_pregunta) # Es una lista, ej: ["T","F"]

                        # Auto-corrección de memoria antigua (si guardamos mal antes)
                        if not isinstance(lista_soluciones_lote, list) or (lista_soluciones_lote and not isinstance(lista_soluciones_lote[0], list)):
                            # Use 28 spaces for indentation
                            print(f"      WARN: Solución Lote T3 no era lista de listas. Auto-corrigiendo. '{lista_soluciones_lote}'")
                            if isinstance(lista_soluciones_lote, list) and not (lista_soluciones_lote and isinstance(lista_soluciones_lote[0], list)):
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [lista_soluciones_lote] # Convertir ["T","F"] a [ ["T","F"] ]
                            else:
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [ [str(lista_soluciones_lote)] ] # Fallback
                            soluciones_correctas[clave_pregunta] = lista_soluciones_lote
                        
                        if ultimo_intento_lote and ultimo_intento_lote in lista_soluciones_lote:
                            # Use 28 spaces for indentation
                            indice = lista_soluciones_lote.index(ultimo_intento_lote)
                            indice_nuevo = (indice + 1) % len(lista_soluciones_lote) # Rotar
                            respuestas_tf_lote = lista_soluciones_lote[indice_nuevo]
                            print(f"      Rotando Lote T3. Último intento: '{ultimo_intento_lote}'. Nuevo intento: '{respuestas_tf_lote}'")
                        else:
                            # Use 28 spaces for indentation
                            respuestas_tf_lote = lista_soluciones_lote[0]
                            print(f"      Iniciando desde el principio de la lista Lote T3. Intentando: '{respuestas_tf_lote}'")
                        
                        preguntas_ya_vistas[clave_pregunta] = respuestas_tf_lote # Guardar este intento (lista)
                        # --- FIN LÓGICA DE ROTACIÓN (LOTE) ---
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

                    # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 6) ELIMINADO! ---

                    if clave_pregunta in soluciones_correctas: 
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN(ES) LOTE T6 ENCONTRADA(S).")
                        # --- INICIO LÓGICA DE ROTACIÓN (LOTE) ---
                        lista_soluciones_lote = soluciones_correctas[clave_pregunta] # Es una lista de listas, ej: [ ["1","2"], ["2","1"] ]
                        ultimo_intento_lote = preguntas_ya_vistas.get(clave_pregunta) # Es una lista, ej: ["1","2"]

                        # Auto-corrección de memoria antigua (si guardamos mal antes)
                        if not isinstance(lista_soluciones_lote, list) or (lista_soluciones_lote and not isinstance(lista_soluciones_lote[0], list)):
                            # Use 28 spaces for indentation
                            print(f"      WARN: Solución Lote T6 no era lista de listas. Auto-corrigiendo. '{lista_soluciones_lote}'")
                            if isinstance(lista_soluciones_lote, list) and not (lista_soluciones_lote and isinstance(lista_soluciones_lote[0], list)):
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [lista_soluciones_lote] # Convertir ["1","2"] a [ ["1","2"] ]
                            else:
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [ [str(lista_soluciones_lote)] ] # Fallback
                            soluciones_correctas[clave_pregunta] = lista_soluciones_lote
                        
                        if ultimo_intento_lote and ultimo_intento_lote in lista_soluciones_lote:
                            # Use 28 spaces for indentation
                            indice = lista_soluciones_lote.index(ultimo_intento_lote)
                            indice_nuevo = (indice + 1) % len(lista_soluciones_lote) # Rotar
                            respuestas_lote_ia = lista_soluciones_lote[indice_nuevo]
                            print(f"      Rotando Lote T6. Último intento: '{ultimo_intento_lote}'. Nuevo intento: '{respuestas_lote_ia}'")
                        else:
                            # Use 28 spaces for indentation
                            respuestas_lote_ia = lista_soluciones_lote[0]
                            print(f"      Iniciando desde el principio de la lista Lote T6. Intentando: '{respuestas_lote_ia}'")
                        
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia # Guardar este intento (lista)
                        # --- FIN LÓGICA DE ROTACIÓN (LOTE) ---
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
                    js_get_keywords = "return Array.from(document.querySelectorAll('h2.text-gray-800.text-base')).map(e => e.innerText.replace(/_/g,'').replace(/:/g,'').replace(/'/g,'').replace(/\\s+/g, ' ').trim());"
                    try:
                        # Use 24 spaces for indentation
                        palabras_clave = driver.execute_script(js_get_keywords); palabras_clave = [p.strip() for p in palabras_clave if p]
                        if not palabras_clave: raise Exception("JS no encontró palabras clave.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo palabras: {e}")
                    print(f"      Palabras clave encontradas (en orden): {palabras_clave}");
                    
                    # --- ¡INICIO SOLUCIÓN AUTOMÁTICA MEJORADA (Fertilizer/Environment)! ---
                    titulo_problematico = 'READ THE SENTENCES AND MATCH THE WORDS FROM THE BOX WITH THEM.'
                    defs_problematicas = ['Fertilizer', 'Environment']
        
                    if (pregunta_actual_texto.strip() == titulo_problematico and 
                        sorted(definiciones) == sorted(defs_problematicas)):
            
                        print("\n" + "!"*60)
                        print("      ¡¡¡PREGUNTA PROBLEMÁTICA DETECTADA (Fertilizer/Environment)!!!")
                        print("      Aplicando solución forzada: 1. Environment -> 2. Fertilizer")
                        print("!"*60 + "\n")
            
                        orden_forzado = ["Environment", "Fertilizer"]
                        exito_forzado = True
            
                        for def_correcta in orden_forzado:
                            elemento_origen = map_texto_def_a_elemento.get(def_correcta)
                            if not elemento_origen:
                                print(f"      Error: No se encontró el elemento para '{def_correcta}'")
                                exito_forzado = False
                                break
                
                            try:
                                print(f"            Clic en '{def_correcta}'...");
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento_origen)
                                time.sleep(0.5)
                                wait_long.until(EC.element_to_be_clickable(elemento_origen)).click()
                                time.sleep(1.0) 
                            except Exception as e:
                                print(f"                  Error en clic forzado: {e}")
                                exito_forzado = False; break

                        if exito_forzado:
                            print("      Selección completada. Forzando clic en CHECK...")
                            try:
                                # Buscamos el botón CHECK específicamente después de los clics
                                time.sleep(1) # Pausa de seguridad
                                boton_check_forzado = wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_CHECK))
                                driver.execute_script("arguments[0].click();", boton_check_forzado)
                                print("      ¡CHECK clickeado con éxito!")
                                
                                # Importante: No ponemos 'continue' aquí para que el código 
                                # siga naturalmente hacia la lógica de aprendizaje y el botón OK
                            except Exception as e_check:
                                print(f"      Error al intentar dar clic en CHECK tras solución forzada: {e_check}")
                        else:
                            print("      Fallo en solución forzada. Intentando SKIP...")
                            try:
                                driver.find_element(*sel.SELECTOR_SKIP).click()
                            except:
                                driver.refresh()
                            continue # Solo reintentamos si falló la selección
                    # --- ¡FIN SOLUCIÓN AUTOMÁTICA! ---

                    titulo_limpio = pregunta_actual_texto.strip()
                    defs_limpias_sorted = sorted([d.strip() for d in definiciones])
                    
                    # --- ¡INICIO CORRECCIÓN CLAVE T4! ---
                    # Añadimos las palabras clave (ordenadas) a la clave para diferenciar preguntas
                    # con el mismo título pero diferentes frases.
                    palabras_clave_limpias_sorted = sorted([p.strip() for p in palabras_clave])
                    clave_pregunta = f"T4:{titulo_limpio}||KW:" + "|".join(palabras_clave_limpias_sorted) + "||DEF:" + "|".join(defs_limpias_sorted)
                    # --- ¡FIN CORRECCIÓN CLAVE T4! ---

                    # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 4) ELIMINADO! ---

                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN(ES) LOTE T4 ENCONTRADA(S) en memoria.");
                        # --- INICIO LÓGICA DE ROTACIÓN (LOTE) ---
                        lista_soluciones_lote = soluciones_correctas[clave_pregunta] # Es una lista de listas, ej: [ ["A","B"], ["B","A"] ]
                        ultimo_intento_lote = preguntas_ya_vistas.get(clave_pregunta) # Es una lista, ej: ["A","B"]

                        # Auto-corrección de memoria antigua (si guardamos mal antes)
                        if not isinstance(lista_soluciones_lote, list) or (lista_soluciones_lote and not isinstance(lista_soluciones_lote[0], list)):
                            # Use 28 spaces for indentation
                            print(f"      WARN: Solución Lote T4 no era lista de listas. Auto-corrigiendo. '{lista_soluciones_lote}'")
                            if isinstance(lista_soluciones_lote, list) and not (lista_soluciones_lote and isinstance(lista_soluciones_lote[0], list)):
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [lista_soluciones_lote] # Convertir ["A","B"] a [ ["A","B"] ]
                            else:
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [ [str(lista_soluciones_lote)] ] # Fallback
                            soluciones_correctas[clave_pregunta] = lista_soluciones_lote
                        
                        if ultimo_intento_lote and ultimo_intento_lote in lista_soluciones_lote:
                            # Use 28 spaces for indentation
                            indice = lista_soluciones_lote.index(ultimo_intento_lote)
                            indice_nuevo = (indice + 1) % len(lista_soluciones_lote) # Rotar
                            lista_definiciones_ordenadas = lista_soluciones_lote[indice_nuevo]
                            print(f"      Rotando Lote T4. Último intento: '{ultimo_intento_lote}'. Nuevo intento: '{lista_definiciones_ordenadas}'")
                        else:
                            # Use 28 spaces for indentation
                            lista_definiciones_ordenadas = lista_soluciones_lote[0]
                            print(f"      Iniciando desde el principio de la lista Lote T4. Intentando: '{lista_definiciones_ordenadas}'")
                        
                        preguntas_ya_vistas[clave_pregunta] = lista_definiciones_ordenadas # Guardar este intento (lista)
                        # --- FIN LÓGICA DE ROTACIÓN (LOTE) ---
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
                        # --- ¡INICIO CORRECCIÓN T5 (Intento 3)! ---
                        # 1. Encontrar la tarjeta T/F
                        caja_tf_single = wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CAJAS_TF))
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja_tf_single); time.sleep(0.1)

                        # 2. Encontrar el texto (Lógica Robusta con Fallbacks)
                        texto_afirmacion = ""
                        try:
                            # Use 32 spaces for indentation
                            # Intento A: Selector estándar (span[1], usado por T3, T6, T7)
                            texto_afirmacion_elem = caja_tf_single.find_element(*sel.SELECTOR_TEXTO_AFIRMACION_TF) # .//span[1]
                            print("      Texto encontrado (Intento A: span[1])")
                            wait_short.until(EC.visibility_of(texto_afirmacion_elem))
                            texto_afirmacion = texto_afirmacion_elem.text.strip()
                        except NoSuchElementException:
                            # Use 32 spaces for indentation
                            print("      WARN: .//span[1] (Selector T3) falló. Intentando .//p[normalize-space(.)]...")
                            try:
                                # Use 36 spaces for indentation
                                # Intento B: Primer párrafo <p> con texto
                                texto_afirmacion_elem = caja_tf_single.find_element(By.XPATH, ".//p[normalize-space(.)]")
                                print("      Texto encontrado (Intento B: p[normalize-space(.)])")
                                wait_short.until(EC.visibility_of(texto_afirmacion_elem))
                                texto_afirmacion = texto_afirmacion_elem.text.strip()
                            except NoSuchElementException:
                                # Use 36 spaces for indentation
                                print("      WARN: No se encontró texto (span/p) DENTRO de la tarjeta.")
                                # ¡FALLBACK! Usar el título de la página que ya leímos.
                                if pregunta_actual_texto:
                                    # Use 40 spaces for indentation
                                    print(f"      Usando FALLBACK: Título de la página ('{pregunta_actual_texto}')")
                                    texto_afirmacion = pregunta_actual_texto
                                    # Limpiar prefijos comunes que vienen en el título
                                    if texto_afirmacion.lower().startswith("true or false:"):
                                        # Use 44 spaces for indentation
                                        texto_afirmacion = texto_afirmacion[14:].strip()
                                else:
                                    # Use 40 spaces for indentation
                                    print("      ERROR: No se encontró texto en tarjeta NI en Título de página.")
                                    raise # Lanzar el error si nada funciona
                        
                        # 3. Extraer botones (siempre están en la caja)
                        if not texto_afirmacion: raise Exception("No se pudo leer el texto de la afirmación TIPO 5 (ni en tarjeta ni en título).")
                        
                        boton_true = caja_tf_single.find_element(*sel.SELECTOR_BOTON_TRUE_TF)
                        boton_false = caja_tf_single.find_element(*sel.SELECTOR_BOTON_FALSE_TF)
                        # --- FIN CORRECCIÓN T5! ---

                        print(f"      Afirmación (Final): '{texto_afirmacion}'");
                        opciones_t5 = ["True", "False"]
                        titulo_limpio_t5 = texto_afirmacion.strip()
                        clave_pregunta = f"T5:{titulo_limpio_t5}||{contexto_hash}||" + "|".join(sorted(opciones_t5))

                        # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 5) ELIMINADO! ---

                        opciones_ya_vistas[clave_pregunta] = opciones_t5
                        
                        respuesta_tf_ia = None # Inicializar
                        if clave_pregunta in soluciones_correctas: 
                            # Use 28 spaces for indentation
                            print("      SOLUCIÓN(ES) T5 ENCONTRADA(S).")
                            # --- INICIO LÓGICA DE ROTACIÓN (SIMPLE) ---
                            lista_soluciones = soluciones_correctas[clave_pregunta]
                            ultimo_intento = preguntas_ya_vistas.get(clave_pregunta)

                            # Auto-corrección de memoria antigua (si guardamos un string en lugar de una lista)
                            if not isinstance(lista_soluciones, list):
                                # Use 32 spaces for indentation
                                print(f"      WARN: Memoria T5 no era lista. Auto-corrigiendo. '{lista_soluciones}'")
                                lista_soluciones = [lista_soluciones] # Convertir "True" a ["True"]
                                soluciones_correctas[clave_pregunta] = lista_soluciones
                            
                            if ultimo_intento and ultimo_intento in lista_soluciones:
                                # Use 32 spaces for indentation
                                indice = lista_soluciones.index(ultimo_intento)
                                indice_nuevo = (indice + 1) % len(lista_soluciones) # Rotar
                                respuesta_tf_ia = lista_soluciones[indice_nuevo]
                                print(f"      Rotando T5. Último intento: '{ultimo_intento}'. Nuevo intento: '{respuesta_tf_ia}'")
                            else:
                                # Use 32 spaces for indentation
                                respuesta_tf_ia = lista_soluciones[0]
                                print(f"      Iniciando desde el principio de la lista T5. Intentando: '{respuesta_tf_ia}'")
                            
                            preguntas_ya_vistas[clave_pregunta] = respuesta_tf_ia # Guardar este intento
                            # --- FIN LÓGICA DE ROTACIÓN (SIMPLE) ---
                        else:
                            # Use 28 spaces for indentation
                            if clave_pregunta in preguntas_ya_vistas:
                                # Use 32 spaces for indentation
                                # Esta lógica de re-intento simple sigue siendo válida si no hay memoria guardada
                                respuesta_anterior = preguntas_ya_vistas[clave_pregunta]; respuesta_tf_ia = "False" if respuesta_anterior == "True" else "True"
                                print(f"      WARN: Pregunta repetida (T5). Anterior: '{respuesta_anterior}'. Forzando: '{respuesta_tf_ia}'")
                            else: 
                                # Use 32 spaces for indentation
                                print("      IA (T/F)..."); respuesta_tf_ia = ia_utils.obtener_true_false(contexto, texto_afirmacion)
                            
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

                    # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 7) ELIMINADO! ---

                    if clave_pregunta in soluciones_correctas: 
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN(ES) LOTE T7 ENCONTRADA(S).")
                        # --- INICIO LÓGICA DE ROTACIÓN (LOTE) ---
                        lista_soluciones_lote = soluciones_correctas[clave_pregunta] # Es una lista de listas, ej: [ ["A","B"], ["B","A"] ]
                        ultimo_intento_lote = preguntas_ya_vistas.get(clave_pregunta) # Es una lista, ej: ["A","B"]

                        # Auto-corrección de memoria antigua (si guardamos mal antes)
                        if not isinstance(lista_soluciones_lote, list) or (lista_soluciones_lote and not isinstance(lista_soluciones_lote[0], list)):
                            # Use 28 spaces for indentation
                            print(f"      WARN: Solución Lote T7 no era lista de listas. Auto-corrigiendo. '{lista_soluciones_lote}'")
                            if isinstance(lista_soluciones_lote, list) and not (lista_soluciones_lote and isinstance(lista_soluciones_lote[0], list)):
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [lista_soluciones_lote] # Convertir ["A","B"] a [ ["A","B"] ]
                            else:
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [ [str(lista_soluciones_lote)] ] # Fallback
                            soluciones_correctas[clave_pregunta] = lista_soluciones_lote
                        
                        if ultimo_intento_lote and ultimo_intento_lote in lista_soluciones_lote:
                            # Use 28 spaces for indentation
                            indice = lista_soluciones_lote.index(ultimo_intento_lote)
                            indice_nuevo = (indice + 1) % len(lista_soluciones_lote) # Rotar
                            respuestas_lote_ia = lista_soluciones_lote[indice_nuevo]
                            print(f"      Rotando Lote T7. Último intento: '{ultimo_intento_lote}'. Nuevo intento: '{respuestas_lote_ia}'")
                        else:
                            # Use 28 spaces for indentation
                            respuestas_lote_ia = lista_soluciones_lote[0]
                            print(f"      Iniciando desde el principio de la lista Lote T7. Intentando: '{respuestas_lote_ia}'")
                        
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia # Guardar este intento (lista)
                        # --- FIN LÓGICA DE ROTACIÓN (LOTE) ---
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
                        # --- LÓGICA DE COLISIONES TIPO 8 (OPTIMIZADA V5 - MEMORY FIRST) ---
                        titulo_check = pregunta_actual_texto.strip()
                        opciones_check_str = "|".join(sorted(definiciones))
                        firma_logica = f"{titulo_check}||{opciones_check_str}"
                        
                        # 1. Consultar Memoria
                        # Verificamos si ya tenemos una solución guardada para este texto+opciones
                        # y si esa solución usa hashes visuales o estándares (IMG_DIM/ALT).
                        tiene_solucion_estandar = False
                        tiene_solucion_visual = False
                        
                        for key in soluciones_correctas:
                            # Chequeo de subcadena para encontrar la firma
                            if titulo_check in key and opciones_check_str in key:
                                if "IMG_VISUAL" in key:
                                    tiene_solucion_visual = True
                                else:
                                    tiene_solucion_estandar = True
                        
                        # 2. Decidir Estrategia
                        activar_modo_visual = False
                        
                        if tiene_solucion_estandar:
                            # PRIORIDAD 1: Si ya funciona con dimensiones (estándar), NO activamos visual.
                            # Esto evita que una "colisión de sesión" fuerce capturas innecesarias cuando ya sabemos la respuesta.
                            print(f"      [i] Memoria Estándar (IMG_DIM/ALT) detectada. Bloqueando Hash Visual para usar solución existente.")
                            activar_modo_visual = False
                            
                        elif tiene_solucion_visual:
                            # PRIORIDAD 2: Si la memoria dice explícitamente que requiere visual, lo activamos.
                            print(f"      [!] Memoria Visual detectada. Activando Hash Visual.")
                            activar_modo_visual = True
                            
                        else:
                            # PRIORIDAD 3: Sin memoria. Chequeamos colisiones en la sesión actual.
                            veces_vistas = tracker_colisiones_t8[firma_logica]
                            tracker_colisiones_t8[firma_logica] += 1
                            
                            if veces_vistas > 0:
                                print(f"      [!] Colisión detectada en sesión (Sin memoria). Activando HASH VISUAL.")
                                activar_modo_visual = True
                            else:
                                print(f"      [i] Pregunta Nueva (Sin memoria). Hash Visual DESACTIVADO.")
                                activar_modo_visual = False
                        # -------------------------------------------------------

                        for i, fila in enumerate(filas_imagenes):
                            # Use 28 spaces for indentation
                            img_elem = fila.find_element(By.TAG_NAME, "img")
                            hash_base = None
                            hash_final = None

                            # 1. ESTRATEGIA: Texto ALT (Prioridad Absoluta - Sin captura)
                            alt_text = img_elem.get_attribute("alt")
                            alt_text_limpio = alt_text.strip() if alt_text else ""
                            if alt_text_limpio and \
                               alt_text_limpio.lower() not in ["descripción de la imagen", "image description", ""]:
                                hash_base = f"IMG_ALT:{alt_text_limpio}"
                                print(f"      Fila {i+1}: Usando ALT='{alt_text_limpio}'", end="")

                            # 2. ESTRATEGIA: Nombre de Archivo (Si es estable - Sin captura)
                            if not hash_base:
                                try:
                                    src_text = img_elem.get_attribute("src")
                                    if src_text and "blob:" not in src_text:
                                        parsed_path = urlparse(src_text).path
                                        filename = os.path.basename(parsed_path)
                                        if filename and len(filename) > 3:
                                            hash_base = f"IMG_SRC:{filename}"
                                            print(f"      Fila {i+1}: Usando SRC='{filename}'", end="")
                                except Exception: pass

                            # 3. ESTRATEGIA: HASH VISUAL (SOLO SI ES REPETIDA + COLISIÓN)
                            if not hash_base and activar_modo_visual:
                                try:
                                    time.sleep(0.1) # Breve espera técnica
                                    b64_data = img_elem.screenshot_as_base64
                                    if b64_data:
                                        md5_hash = hashlib.md5(b64_data.encode('utf-8')).hexdigest()
                                        short_hash = md5_hash[:12]
                                        hash_base = f"IMG_VISUAL:{short_hash}"
                                        print(f"      Fila {i+1}: HASH VISUAL='{short_hash}' (Por Colisión)", end="")
                                except Exception as e_md5:
                                    print(f"      ErrMD5:{e_md5}", end="")

                            # 4. ESTRATEGIA: DIMENSIONES (Estándar para preguntas nuevas)
                            if not hash_base:
                                try:
                                    size = img_elem.size
                                    width = size.get('width', 0)
                                    height = size.get('height', 0)
                                    if width > 0 and height > 0:
                                        hash_base = f"IMG_DIM:{width}x{height}"
                                        print(f"      Fila {i+1}: Usando DIM='{width}x{height}'", end="")
                                    else:
                                        # Si dimensions es 0x0, intentamos Blob como último recurso
                                        src_text = img_elem.get_attribute("src")
                                        if src_text and "blob:" in src_text:
                                            unique_id = src_text[-20:]
                                            hash_base = f"IMG_BLOB:{unique_id}"
                                            print(f" -> WARN: 0x0. Usando BLOB='...{unique_id}'", end="")
                                except Exception: pass

                            # Fallback final
                            if not hash_base:
                                hash_base = f"imagen_error_{i}_nodim"
                                print(f" -> Error ID", end="")

                            # Manejo de duplicados internos
                            if hash_base:
                                count = hash_counts[hash_base]
                                if count > 0:
                                    hash_final = f"{hash_base}_{count}"
                                else:
                                    hash_final = hash_base
                                hash_counts[hash_base] += 1
                            else:
                                hash_final = f"imagen_error_{i}_final"

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

                    # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 8) ELIMINADO! ---

                    print(f"DEBUG: Generated Key T8: '{clave_pregunta}'")
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN(ES) LOTE T8 ENCONTRADA(S) en memoria.");
                        # --- INICIO LÓGICA DE ROTACIÓN (LOTE) ---
                        lista_soluciones_lote = soluciones_correctas[clave_pregunta] # Es una lista de listas, ej: [ ["A","B"], ["B","A"] ]
                        ultimo_intento_lote = preguntas_ya_vistas.get(clave_pregunta) # Es una lista, ej: ["A","B"]

                        # Auto-corrección de memoria antigua (si guardamos mal antes)
                        if not isinstance(lista_soluciones_lote, list) or (lista_soluciones_lote and not isinstance(lista_soluciones_lote[0], list)):
                            # Use 28 spaces for indentation
                            print(f"      WARN: Solución Lote T8 no era lista de listas. Auto-corrigiendo. '{lista_soluciones_lote}'")
                            if isinstance(lista_soluciones_lote, list) and not (lista_soluciones_lote and isinstance(lista_soluciones_lote[0], list)):
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [lista_soluciones_lote] # Convertir ["A","B"] a [ ["A","B"] ]
                            else:
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [ [str(lista_soluciones_lote)] ] # Fallback
                            soluciones_correctas[clave_pregunta] = lista_soluciones_lote
                        
                        if ultimo_intento_lote and ultimo_intento_lote in lista_soluciones_lote:
                            # Use 28 spaces for indentation
                            indice = lista_soluciones_lote.index(ultimo_intento_lote)
                            indice_nuevo = (indice + 1) % len(lista_soluciones_lote) # Rotar
                            lista_definiciones_ordenadas = lista_soluciones_lote[indice_nuevo]
                            print(f"      Rotando Lote T8. Último intento: '{ultimo_intento_lote}'. Nuevo intento: '{lista_definiciones_ordenadas}'")
                        else:
                            # Use 28 spaces for indentation
                            lista_definiciones_ordenadas = lista_soluciones_lote[0]
                            print(f"      Iniciando desde el principio de la lista Lote T8. Intentando: '{lista_definiciones_ordenadas}'")
                        
                        preguntas_ya_vistas[clave_pregunta] = lista_definiciones_ordenadas # Guardar este intento (lista)
                        # --- FIN LÓGICA DE ROTACIÓN (LOTE) ---
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

                    # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 9) ELIMINADO! ---

                    print(f"Resolviendo: {pregunta_actual_texto}\nOpciones: {opciones}");
                    opciones_ya_vistas[clave_pregunta] = opciones
                    
                    respuesta_adivinada = None # Inicializar
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN(ES) T9 ENCONTRADA(S).");
                        # --- INICIO LÓGICA DE ROTACIÓN (SIMPLE) ---
                        lista_soluciones = soluciones_correctas[clave_pregunta]
                        ultimo_intento = preguntas_ya_vistas.get(clave_pregunta)

                        # Auto-corrección de memoria antigua (si guardamos un string en lugar de una lista)
                        if not isinstance(lista_soluciones, list):
                            # Use 28 spaces for indentation
                            print(f"      WARN: Memoria T9 no era lista. Auto-corrigiendo. '{lista_soluciones}'")
                            lista_soluciones = [lista_soluciones] # Convertir "Opcion A" a ["Opcion A"]
                            soluciones_correctas[clave_pregunta] = lista_soluciones
                        
                        if ultimo_intento and ultimo_intento in lista_soluciones:
                            # Use 28 spaces for indentation
                            indice = lista_soluciones.index(ultimo_intento)
                            indice_nuevo = (indice + 1) % len(lista_soluciones) # Rotar
                            respuesta_adivinada = lista_soluciones[indice_nuevo]
                            print(f"      Rotando T9. Último intento: '{ultimo_intento}'. Nuevo intento: '{respuesta_adivinada}'")
                        else:
                            # Use 28 spaces for indentation
                            respuesta_adivinada = lista_soluciones[0]
                            print(f"      Iniciando desde el principio de la lista T9. Intentando: '{respuesta_adivinada}'")
                        
                        preguntas_ya_vistas[clave_pregunta] = respuesta_adivinada # Guardar este intento
                        # --- FIN LÓGICA DE ROTACIÓN (SIMPLE) ---
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

                    # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 10) ELIMINADO! ---

                    respuestas_lote_ia = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN(ES) LOTE TIPO 10 ENCONTRADA(S) en memoria.");
                        # --- INICIO LÓGICA DE ROTACIÓN (LOTE) ---
                        lista_soluciones_lote = soluciones_correctas[clave_pregunta] # Es una lista de listas, ej: [ ["A","B"], ["B","A"] ]
                        ultimo_intento_lote = preguntas_ya_vistas.get(clave_pregunta) # Es una lista, ej: ["A","B"]

                        # Auto-corrección de memoria antigua (si guardamos mal antes)
                        if not isinstance(lista_soluciones_lote, list) or (lista_soluciones_lote and not isinstance(lista_soluciones_lote[0], list)):
                            # Use 28 spaces for indentation
                            print(f"      WARN: Solución Lote T10 no era lista de listas. Auto-corrigiendo. '{lista_soluciones_lote}'")
                            if isinstance(lista_soluciones_lote, list) and not (lista_soluciones_lote and isinstance(lista_soluciones_lote[0], list)):
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [lista_soluciones_lote] # Convertir ["A","B"] a [ ["A","B"] ]
                            else:
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [ [str(lista_soluciones_lote)] ] # Fallback
                            soluciones_correctas[clave_pregunta] = lista_soluciones_lote
                        
                        if ultimo_intento_lote and ultimo_intento_lote in lista_soluciones_lote:
                            # Use 28 spaces for indentation
                            indice = lista_soluciones_lote.index(ultimo_intento_lote)
                            indice_nuevo = (indice + 1) % len(lista_soluciones_lote) # Rotar
                            respuestas_lote_ia = lista_soluciones_lote[indice_nuevo]
                            print(f"      Rotando Lote T10. Último intento: '{ultimo_intento_lote}'. Nuevo intento: '{respuestas_lote_ia}'")
                        else:
                            # Use 28 spaces for indentation
                            respuestas_lote_ia = lista_soluciones_lote[0]
                            print(f"      Iniciando desde el principio de la lista Lote T10. Intentando: '{respuestas_lote_ia}'")
                        
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia # Guardar este intento (lista)
                        # --- FIN LÓGICA DE ROTACIÓN (LOTE) ---
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

                    # --- ¡CHEQUEO DE BUCLE ATASCADO (TIPO 11) ELIMINADO! ---

                    respuestas_lote_ia = []
                    if clave_pregunta in soluciones_correctas:
                        # Use 24 spaces for indentation
                        print("      SOLUCIÓN(ES) LOTE TIPO 11 ENCONTRADA(S) en memoria.");
                        # --- INICIO LÓGICA DE ROTACIÓN (LOTE) ---
                        lista_soluciones_lote = soluciones_correctas[clave_pregunta] # Es una lista de listas, ej: [ ["A","B"], ["B","A"] ]
                        ultimo_intento_lote = preguntas_ya_vistas.get(clave_pregunta) # Es una lista, ej: ["A","B"]

                        # Auto-corrección de memoria antigua (si guardamos mal antes)
                        if not isinstance(lista_soluciones_lote, list) or (lista_soluciones_lote and not isinstance(lista_soluciones_lote[0], list)):
                            # Use 28 spaces for indentation
                            print(f"      WARN: Solución Lote T11 no era lista de listas. Auto-corrigiendo. '{lista_soluciones_lote}'")
                            if isinstance(lista_soluciones_lote, list) and not (lista_soluciones_lote and isinstance(lista_soluciones_lote[0], list)):
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [lista_soluciones_lote] # Convertir ["A","B"] a [ ["A","B"] ]
                            else:
                                # Use 32 spaces for indentation
                                lista_soluciones_lote = [ [str(lista_soluciones_lote)] ] # Fallback
                            soluciones_correctas[clave_pregunta] = lista_soluciones_lote
                        
                        if ultimo_intento_lote and ultimo_intento_lote in lista_soluciones_lote:
                            # Use 28 spaces for indentation
                            indice = lista_soluciones_lote.index(ultimo_intento_lote)
                            indice_nuevo = (indice + 1) % len(lista_soluciones_lote) # Rotar
                            respuestas_lote_ia = lista_soluciones_lote[indice_nuevo]
                            print(f"      Rotando Lote T11. Último intento: '{ultimo_intento_lote}'. Nuevo intento: '{respuestas_lote_ia}'")
                        else:
                            # Use 28 spaces for indentation
                            respuestas_lote_ia = lista_soluciones_lote[0]
                            print(f"      Iniciando desde el principio de la lista Lote T11. Intentando: '{respuestas_lote_ia}'")
                        
                        preguntas_ya_vistas[clave_pregunta] = respuestas_lote_ia # Guardar este intento (lista)
                        # --- FIN LÓGICA DE ROTACIÓN (LOTE) ---
                    else:
                        # --- ¡NUEVA LÓGICA DE BIFURCACIÓN T11! ---
                        titulo_lower = pregunta_actual_texto.lower()
                        # AGREGADO: "complete the word" para detectar anagramas como 'anticrom' -> 'romantic'
                        if "order the letters" in titulo_lower or "put in order" in titulo_lower or "complete the word" in titulo_lower:
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

                    # --- CHEQUEO DE BUCLE ATASCADO (TIPO 12) ELIMINADO ---

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
                    # --- FIN LÓGICA DE ROTACIÓN T12! ---

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
                # --- TIPO DEFAULT: OPCIÓN MÚLTIPLE (V11 - ESCÁNER CON LÍMITE DE LONGITUD) ---
                elif tipo_pregunta == "TIPO_DEFAULT_OM":
                    lista_tareas_multi_om = [] # <--- ¡AGREGA ESTA LÍNEA DE SEGURIDAD AQUÍ!
                    print("Tipo: OPCIÓN MÚLTIPLE (Default - V11 Length Check).")
                    
                    opciones_elementos = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_OPCIONES))
                    opciones_visibles = [e for e in opciones_elementos if e.is_displayed()]
                    if not opciones_visibles: raise Exception("No opciones visibles.")

                    # 1. AGRUPACIÓN PRELIMINAR
                    grupos_base = defaultdict(list)
                    for op in opciones_visibles:
                        try:
                            abuelo = op.find_element(By.XPATH, "./../..")
                            grupos_base[abuelo].append(op)
                        except: pass
                    
                    cajas_candidatas = sorted(grupos_base.items(), key=lambda x: x[0].location['y'] if x[0] else 0)
                    
                    # 2. ESCÁNER DE TEXTO (Mejorado V2: Mayor Rango y Longitud)
                    cajas_confirmadas = []
                    opciones_sin_contexto = []

                    for contenedor_base, ops_grupo in cajas_candidatas:
                        texto_encontrado = ""
                        elemento_actual = contenedor_base

                        # CAMBIO 1: Subimos hasta 5 niveles (antes 3) para encontrar el texto en estructuras anidadas
                        for i in range(5): 
                            try:
                                txt_total = elemento_actual.text.strip()
                                residuo = txt_total
                                for o in ops_grupo: residuo = residuo.replace(o.text.strip(), "")
                                residuo = residuo.replace(pregunta_actual_texto, "") 
                                residuo = " ".join(residuo.split())
                                
                                # --- CORRECCIÓN CRÍTICA ---
                                # CAMBIO 2: Aumentamos límite a 350 chars (antes 120) para aceptar definiciones largas.
                                if len(residuo) > 2 and len(residuo) < 350:
                                    texto_encontrado = residuo
                                    contenedor_base = elemento_actual 
                                    break
                                
                                elemento_actual = elemento_actual.find_element(By.XPATH, "..")
                            except: break
                        
                        if texto_encontrado:
                            print(f"      [Scanner] Contexto hallado: '{texto_encontrado[:40]}...'")
                            cajas_confirmadas.append({
                                "contenedor": contenedor_base, "opciones": ops_grupo, "texto": texto_encontrado
                            })
                        else:
                            opciones_sin_contexto.extend(ops_grupo)

                    # 3. DECISIÓN DE MODO
                    num_preguntas = len(cajas_confirmadas)
                    
                    # ==============================================================================
                    # CASO A: MODO MULTI (Estructura Clara Detectada)
                    # ==============================================================================
                    if num_preguntas > 0: 
                        print(f"      [MODO MULTI/CONTEXTO] {num_preguntas} bloques válidos.")
                        lista_tareas_multi_om = []
                        
                        for i, caja in enumerate(cajas_confirmadas):
                            ctx_local = caja["texto"]
                            ops_txt = [o.text.strip() for o in caja["opciones"]]
                            
                            titulo_clean = pregunta_actual_texto.strip()
                            clave_grupo = f"DEFAULT_MULTI:{titulo_clean}||{ctx_local}||" + "|".join(sorted(ops_txt))
                            
                            lista_tareas_multi_om.append({
                                "clave": clave_grupo, "frase": ctx_local, "opciones": ops_txt
                            })
                            
                            respuesta_ia = None
                            if clave_grupo in soluciones_correctas:
                                sol = soluciones_correctas[clave_grupo]
                                respuesta_ia = sol[0] if isinstance(sol, list) else sol
                                preguntas_ya_vistas[clave_grupo] = respuesta_ia
                            else:
                                respuesta_ia = ia_utils.obtener_respuesta_opcion_multiple(ctx_local, pregunta_actual_texto, ops_txt)
                                if respuesta_ia: preguntas_ya_vistas[clave_grupo] = respuesta_ia
                            
                            if respuesta_ia:
                                boton_clic = None
                                for b in caja["opciones"]:
                                    if ' '.join(b.text.split()) == ' '.join(respuesta_ia.split()):
                                        boton_clic = b; break
                                
                                if boton_clic:
                                    try:
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_clic)
                                        time.sleep(0.1)
                                        # CLIC JS REFORZADO
                                        driver.execute_script("arguments[0].click();", boton_clic)
                                        time.sleep(0.1)
                                    except: pass
                        
                        if num_preguntas > 1: clave_pregunta = "MULTI_BATCH_PROCESSED"
                        else: 
                            item = lista_tareas_multi_om[0]
                            clave_pregunta = item["clave"]
                            

                    # ==============================================================================
                    # CASO B: MODO SIMPLE (Fallback robusto para Párrafos y Grids)
                    # ==============================================================================
                    else:
                        print("      [MODO SIMPLE] Tratando como lista única de opciones.")
                        # Usamos TODAS las opciones visibles si no hay contextos claros
                        opciones_finales = opciones_sin_contexto if opciones_sin_contexto else opciones_visibles
                        opciones = [e.text.strip() for e in opciones_finales if e.text]

                        # Raspado de Emergencia (Solo busca títulos cortos arriba)
                        texto_completo_raspado = ""
                        contexto_extra_key = ""
                        
                        if (not contexto or len(contexto) < 5) and (not body_hash):
                            try:
                                ref = opciones_finales[0]
                                ancestro = ref.find_element(By.XPATH, "./../..")
                                for _ in range(4):
                                    try:
                                        ancestro = ancestro.find_element(By.XPATH, "..")
                                        txt = ancestro.text.strip()
                                        txt_limpio = txt.replace(pregunta_actual_texto, "")
                                        for op in opciones: txt_limpio = txt_limpio.replace(op, "")
                                        txt_limpio = " ".join(txt_limpio.split())
                                        
                                        # --- FILTRO ANTI-RUIDO UNIVERSAL ---
                                        # Ignora cualquier línea que parezca un encabezado de libro/unidad
                                        # Ej: "9/10 READING • BOOK 2 • MOD 1" o "VOCABULARY..."
                                        txt_up = txt_limpio.upper()
                                        if ("BOOK" in txt_up and "UNIT" in txt_up) or \
                                           ("BOOK" in txt_up and "MOD" in txt_up) or \
                                           ("/10" in txt_up and ("READING" in txt_up or "VOCABULARY" in txt_up or "GRAMMAR" in txt_up)):
                                            print(f"      [Scanner] Ignorando header variable: '{txt_limpio[:30]}...'")
                                            continue 
                                        # ----------------------------------------------------

                                        # Solo aceptamos textos cortos/medianos como contexto (Quickly)
                                        if len(txt_limpio) > 2 and len(txt_limpio) < 150: 
                                            texto_completo_raspado = txt_limpio
                                            contexto_extra_key = f"EXTRACT:{txt_limpio[:60]}...{txt_limpio[-20:]}"
                                            print(f"      [Robustez] Contexto recuperado: '{txt_limpio[:40]}...'")
                                            break
                                    except: break
                            except: pass

                        # Clave y Resolución (Con Búsqueda Flexible)
                        titulo_limpio_def = pregunta_actual_texto.strip()
                        opciones_limpias_sorted_def = sorted([o.strip() for o in opciones])
                        img_hash_local = imagen_hash if 'imagen_hash' in locals() else ""
                        
                        clave_pregunta = f"DEFAULT:{titulo_limpio_def}||{contexto_hash}||{body_hash}||{contexto_extra_key}||{img_hash_local}||" + "|".join(opciones_limpias_sorted_def)
                        opciones_ya_vistas[clave_pregunta] = opciones

                        respuesta_ia = None
                        soluciones_halladas = None
                        
                        # 1. Búsqueda Exacta
                        if clave_pregunta in soluciones_correctas:
                            print("      SOLUCIÓN SIMPLE EN MEMORIA (Exacta).")
                            soluciones_halladas = soluciones_correctas[clave_pregunta]
                        
                        # 2. Búsqueda Flexible (Fuzzy) - Si cambió el contexto/scanner
                        else:
                            print("      [Memoria] Clave exacta no hallada. Intentando coincidencia flexible...")
                            part_titulo = f"DEFAULT:{titulo_limpio_def}"
                            part_opciones = "|".join(opciones_limpias_sorted_def)
                            
                            for k_mem in soluciones_correctas:
                                # Coincidencia de Título (inicio) y Opciones (final)
                                if k_mem.startswith(part_titulo) and k_mem.endswith(part_opciones):
                                    soluciones_halladas = soluciones_correctas[k_mem]
                                    print(f"      [Memoria] ¡Recuperada respuesta de clave antigua/sucia!")
                                    clave_pregunta = k_mem # Usamos la clave vieja para que el sistema sepa qué respuesta usar
                                    break
                        
                        # 3. Procesar Solución o Llamar IA
                        if soluciones_halladas:
                            # Manejo de formatos legacy (lista vs string vs lista de listas)
                            if isinstance(soluciones_halladas, list):
                                if soluciones_halladas and isinstance(soluciones_halladas[0], list):
                                    # Si es lista de listas [[A],[B]], tomamos la primera
                                    respuesta_ia = soluciones_halladas[0][0] if soluciones_halladas[0] else None
                                else:
                                    respuesta_ia = soluciones_halladas[0]
                            else:
                                respuesta_ia = soluciones_halladas
                            
                            preguntas_ya_vistas[clave_pregunta] = respuesta_ia
                        
                        else:
                            # No hay memoria -> IA
                            ctx_ia = contexto
                            if not ctx_ia and texto_completo_raspado: ctx_ia = texto_completo_raspado
                            print("      IA (Simple)...")
                            ant = preguntas_ya_vistas.get(clave_pregunta)
                            respuesta_ia = ia_utils.obtener_respuesta_opcion_multiple(ctx_ia, pregunta_actual_texto, opciones, ant)
                            if respuesta_ia: preguntas_ya_vistas[clave_pregunta] = respuesta_ia

                        if respuesta_ia:
                            boton_encontrado = None
                            for b in opciones_finales:
                                if ' '.join(b.text.split()) == ' '.join(respuesta_ia.split()):
                                    boton_encontrado = b; break
                            if boton_encontrado:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_encontrado)
                                time.sleep(0.1)
                                # CLIC JS REFORZADO (Importante para tarjetas grandes)
                                driver.execute_script("arguments[0].click();", boton_encontrado)
                                time.sleep(0.2)
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
                            # Corrección T5: Usar el texto de la afirmación, no el título de la página
                            if 'texto_afirmacion' in locals() and texto_afirmacion:
                                titulo_limpio_t5 = texto_afirmacion.strip()
                                clave_pregunta_aprendizaje = f"T5:{titulo_limpio_t5}||{contexto_hash}||True|False"
                            else:
                                print("      ERROR APRENDIZAJE T5: 'texto_afirmacion' no estaba definido.")
                                clave_pregunta_aprendizaje = None
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
                        
                        # --- ¡INICIO CORRECCIÓN CLAVE T4 (APRENDIZAJE)! ---
                        elif tipo_pregunta == "TIPO_4_EMPAREJAR" and 'definiciones' in locals() and 'palabras_clave' in locals(): # Añadido 'palabras_clave'
                             titulo_limpio = pregunta_actual_texto.strip()
                             defs_limpias_sorted = sorted([d.strip() for d in definiciones])
                             palabras_clave_limpias_sorted = sorted([p.strip() for p in palabras_clave])
                             clave_pregunta_aprendizaje = f"T4:{titulo_limpio}||KW:" + "|".join(palabras_clave_limpias_sorted) + "||DEF:" + "|".join(defs_limpias_sorted)
                        # --- ¡FIN CORRECCIÓN CLAVE T4 (APRENDIZAJE)! ---
                        
                        elif tipo_pregunta == "TIPO_8_IMAGEN" and 'definiciones' in locals() and 'palabras_clave' in locals():
                             titulo_limpio = pregunta_actual_texto.strip()
                             defs_limpias_sorted = sorted([d.strip() for d in definiciones])
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
                                # AGREGADO: "complete the word" para usar el extractor de anagramas
                                if "order the letters" in titulo_lower or "put in order" in titulo_lower or "complete the word" in titulo_lower:
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


                        # --- NUEVO: APRENDIZAJE LOTE OM (Insertar ANTES del bloque simple) ---
                        elif tipo_pregunta == "TIPO_DEFAULT_OM" and lista_tareas_multi_om:
                            print(f"      Aprendiendo Lote OM ({len(lista_tareas_multi_om)} preguntas)...")
                            # Usamos el extractor de 'completar' que entiende el formato (Frase + Opciones)
                            tareas_aprendizaje = [{"frase": t["frase"], "opciones": t["opciones"]} for t in lista_tareas_multi_om]
                            solucion_lista_ordenada = ia_utils.extraer_solucion_lote_completar(contenido_modal, tareas_aprendizaje)
                            
                            if solucion_lista_ordenada and len(solucion_lista_ordenada) == len(lista_tareas_multi_om):
                                for i, resp in enumerate(solucion_lista_ordenada):
                                    c_key = lista_tareas_multi_om[i]["clave"]
                                    soluciones_correctas[c_key] = resp
                                guardar_memoria_en_disco()
                                solucion_aprendida = None # Evitamos que entre en la lógica antigua
                                print(f"      ¡Soluciones Lote OM guardadas!: {solucion_lista_ordenada}")
                        # ---------------------------------------------------------------------
                        elif tipo_pregunta in ["TIPO_5_TF_SINGLE", "TIPO_DEFAULT_OM", "TIPO_9_AUDIO"] and clave_pregunta_aprendizaje and contenido_modal and opciones_para_ia:
                            # Use 28 spaces for indentation
                            print(f"      Enviando texto a IA (Simple) para extraer solución (Tipo: {tipo_pregunta})...");
                            solucion_simple = ia_utils.extraer_solucion_simple(contenido_modal, opciones_para_ia)
                            if solucion_simple:
                                # Use 32 spaces for indentation
                                print(f"      ¡SOLUCIÓN SIMPLE APRENDIDA! -> {solucion_simple}");
                                solucion_aprendida = solucion_simple.strip()
                            else: print("      IA (Simple) no pudo extraer solución.")


                        # --- ¡INICIO NUEVA LÓGICA DE GUARDADO (ROTACIÓN)! ---
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
                           if tipo_pregunta == "TIPO_2_COMPLETAR": # T2 usa Dict, lógica especial (no rota)
                                # Use 32 spaces for indentation
                                if isinstance(lista_existente, dict) and isinstance(solucion_aprendida, dict):
                                    lista_existente.update(solucion_aprendida)
                                    soluciones_correctas[clave_pregunta_aprendizaje] = lista_existente
                                    print(f"      Memoria T2 fusionada: {solucion_aprendida}")
                                else:
                                    soluciones_correctas[clave_pregunta_aprendizaje] = solucion_aprendida
                                    print(f"      Memoria T2 guardada/sobrescrita: {solucion_aprendida}")
                                guardar_memoria_en_disco()
                           
                           # --- ¡NUEVA LÓGICA DE ROTACIÓN PARA CASI TODO! ---
                           elif tipo_pregunta in [
                               "TIPO_DEFAULT_OM", "TIPO_9_AUDIO", "TIPO_5_TF_SINGLE", # Tipos Simples
                               "TIPO_1_ORDENAR", "TIPO_3_TF_MULTI", "TIPO_4_EMPAREJAR", # Tipos Lote (Deterministas pero con IA)
                               "TIPO_6_PARAGRAPH", "TIPO_7_OM_CARD", # Tipos Lote (IA)
                               "TIPO_8_IMAGEN", "TIPO_10_ESCRIBIR", "TIPO_11_ESCRIBIR_OPCIONES", # Tipos Lote (IA)
                               "TIPO_12_DICTADO" # Tipo Lote (Dictado)
                           ]:
                                # Use 32 spaces for indentation
                                
                                # Auto-corrección / Inicialización
                                if not isinstance(lista_existente, list):
                                    # Use 36 spaces for indentation
                                    print(f"      Memoria no era lista. Creando nueva lista.")
                                    lista_existente = []
                                # Validar tipo de contenido (lista de strings vs lista de listas)
                                elif lista_existente and (type(lista_existente[0]) != type(solucion_individual_aprendida)):
                                    # Use 36 spaces for indentation
                                    # Caso especial: la memoria era ["A"] (simple) y aprendimos [["A","B"]] (lote) o viceversa
                                    print(f"      WARN: Tipo de memoria ({type(lista_existente[0])}) no coincide con solución aprendida ({type(solucion_individual_aprendida)}). Reseteando lista.")
                                    lista_existente = []

                                if solucion_individual_aprendida not in lista_existente:
                                    # Use 36 spaces for indentation
                                    print(f"      ¡Nueva solución aprendida! Añadiendo a la lista: {solucion_individual_aprendida}")
                                    lista_existente.append(solucion_individual_aprendida)
                                    soluciones_correctas[clave_pregunta_aprendizaje] = lista_existente
                                    guardar_memoria_en_disco()
                                else:
                                    # Use 36 spaces for indentation
                                    print(f"      WARN: La solución aprendida ({solucion_individual_aprendida}) ya estaba en la lista. No se guarda.")
                           
                           else: # ¿Queda alguno?
                                # Use 32 spaces for indentation
                                # Lógica de guardado estándar (sobrescribir) - fallback
                                soluciones_correctas[clave_pregunta_aprendizaje] = solucion_individual_aprendida
                                print(f"      Memoria guardada (Fallback Estándar): {solucion_individual_aprendida}")
                                guardar_memoria_en_disco()
                        
                        else: # No se pudo aprender
                           # Use 28 spaces for indentation
                           print("      WARN: No se pudo aprender la solución (clave o solución vacía).")
                        # --- ¡FIN LÓGICA DE GUARDADO! ---


                    # --- CASO 2: RESPUESTA CORRECTA ---
                    elif "correct" in titulo_modal or "great" in titulo_modal:
                        # Use 24 spaces for indentation
                        print(f"      Respuesta CORRECTA detectada (Modal: {titulo_modal}).")
                        # --- NUEVO: GUARDAR ACIERTOS LOTE OM ---
                        if tipo_pregunta == "TIPO_DEFAULT_OM" and lista_tareas_multi_om:
                             print("      Guardando Aciertos Lote OM en memoria...")
                             count_saved = 0
                             for item in lista_tareas_multi_om:
                                 c_key = item["clave"]
                                 if c_key in preguntas_ya_vistas:
                                     resp = preguntas_ya_vistas[c_key]
                                     soluciones_correctas[c_key] = resp
                                     count_saved += 1
                             if count_saved > 0:
                                 print(f"      {count_saved} respuestas OM guardadas en disco.")
                                 guardar_memoria_en_disco()
                        # ---------------------------------------
                        clave_pregunta_acierto = None

                        # Regenerar clave correcta para guardar el acierto si es necesario
                        if 'clave_pregunta' in locals() and clave_pregunta:
                             clave_pregunta_acierto = clave_pregunta.strip()
                        
                        if clave_pregunta_acierto is None:
                            # Use 28 spaces for indentation
                            print("      WARN Acierto: 'clave_pregunta' no estaba definida. Regenerando clave para guardar acierto...")
                            # (Regeneración de claves omitida por brevedad, es la misma que ya tienes)
                            if tipo_pregunta == "TIPO_10_ESCRIBIR":
                                 # Use 32 spaces for indentation
                                 titulo_limpio = pregunta_actual_texto.strip()
                                 if 'lista_de_tareas_escribir' in locals() and lista_de_tareas_escribir:
                                     claves_ordenadas_str = "|".join(sorted([t["letras_clave"] for t in lista_de_tareas_escribir]))
                                     clave_pregunta_acierto = f"T10_BATCH:{titulo_limpio}||{claves_ordenadas_str}"
                            elif tipo_pregunta == "TIPO_1_ORDENAR":
                                if 'lista_de_claves_individuales' in locals() and lista_de_claves_individuales:
                                     clave_pregunta_acierto = "|".join([p.strip() for p in lista_de_claves_individuales])
                            elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES":
                                 # Use 32 spaces for indentation
                                 titulo_limpio = pregunta_actual_texto.strip()
                                 if 'lista_de_tareas_escribir' in locals() and lista_de_tareas_escribir:
                                     frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                                     clave_pregunta_acierto = f"T11_BATCH:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"
                            elif tipo_pregunta == "TIPO_12_DICTADO":
                                 # Use 32 spaces for indentation
                                 titulo_limpio = pregunta_actual_texto.strip()
                                 if 'lista_de_tareas_escribir' in locals() and lista_de_tareas_escribir:
                                     frases_clave_str = "|".join(sorted([t["frase"] for t in lista_de_tareas_escribir]))
                                     clave_pregunta_acierto = f"T12_DICTADO:{titulo_limpio}||{contexto_hash}||{frases_clave_str}"
                            elif tipo_pregunta == "TIPO_8_IMAGEN":
                                # Use 32 spaces for indentation
                                titulo_limpio = pregunta_actual_texto.strip()
                                if 'definiciones' in locals() and 'palabras_clave' in locals():
                                     defs_limpias_sorted = sorted([d.strip() for d in definiciones])
                                     claves_unicas_ordenados_str = "|".join(sorted(palabras_clave))
                                     clave_pregunta_acierto = f"T8:{titulo_limpio}||{claves_unicas_ordenados_str}||" + "|".join(defs_limpias_sorted)
                            elif tipo_pregunta == "TIPO_2_COMPLETAR":
                                 # Use 32 spaces for indentation
                                 titulo_limpio = pregunta_actual_texto.strip()
                                 if 'lista_de_tareas_completar' in locals() and lista_de_tareas_completar:
                                     frases_para_clave = sorted([t["frase"] for t in lista_de_tareas_completar])
                                     frases_hash_str = "|".join(frases_para_clave)
                                     clave_pregunta_acierto = f"T2_BATCH:{titulo_limpio}||{contexto_hash}||FRASES:{frases_hash_str}"
                            elif tipo_pregunta == "TIPO_4_EMPAREJAR":
                                # Use 32 spaces for indentation
                                titulo_limpio = pregunta_actual_texto.strip()
                                if 'definiciones' in locals() and 'palabras_clave' in locals():
                                     defs_limpias_sorted = sorted([d.strip() for d in definiciones])
                                     palabras_clave_limpias_sorted = sorted([p.strip() for p in palabras_clave])
                                     clave_pregunta_acierto = f"T4:{titulo_limpio}||KW:" + "|".join(palabras_clave_limpias_sorted) + "||DEF:" + "|".join(defs_limpias_sorted)
                        
                        # --- ¡INICIO LÓGICA DE GUARDADO (ACIERTO - ROTACIÓN)! ---
                        if clave_pregunta_acierto:
                            # Use 28 spaces for indentation
                            respuesta_correcta_actual = preguntas_ya_vistas.get(clave_pregunta_acierto)
                            
                            if respuesta_correcta_actual is None:
                               # Use 32 spaces for indentation
                               print(f"      WARN: Acierto, pero no se encontró la respuesta en 'preguntas_ya_vistas' para clave: {clave_pregunta_acierto}")
                            
                            elif tipo_pregunta == "TIPO_2_COMPLETAR":
                               # Use 32 spaces for indentation
                               # (La lógica T2 de "dict update" está bien, no la tocamos)
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
                                             print("      La solución T2 (dict) ya estaba en memoria. No se necesita guardar.")
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
                               # ¡NUEVO ACIERTO! Debemos guardarlo en el formato de LISTA.
                               try:
                                    # Use 36 spaces for indentation
                                    solucion_a_guardar = None
                                    
                                    # Normalizar respuesta (ej. mayúsculas)
                                    if tipo_pregunta == "TIPO_10_ESCRIBIR" and isinstance(respuesta_correcta_actual, list):
                                         solucion_a_guardar = [p.upper() for p in respuesta_correcta_actual]
                                    elif tipo_pregunta == "TIPO_11_ESCRIBIR_OPCIONES" and isinstance(respuesta_correcta_actual, list):
                                         solucion_a_guardar = [p.upper() for p in respuesta_correcta_actual]
                                    elif tipo_pregunta == "TIPO_12_DICTADO" and isinstance(respuesta_correcta_actual, list): # ¡NUEVO T12!
                                         solucion_a_guardar = [p.upper() for p in respuesta_correcta_actual]
                                    elif isinstance(respuesta_correcta_actual, str):
                                         solucion_a_guardar = respuesta_correcta_actual.strip()
                                    else: # Para otros tipos de LOTE (T1, T3, T4, T6, T7, T8)
                                         solucion_a_guardar = respuesta_correcta_actual
                                    
                                    # ¡Envolver en lista!
                                    solucion_a_guardar_final = [solucion_a_guardar]
                                    print(f"      ¡SOLUCIÓN (por acierto Estándar) APRENDIDA! Guardando como lista -> {solucion_a_guardar_final}")

                                    soluciones_correctas[clave_pregunta_acierto] = solucion_a_guardar_final
                                    guardar_memoria_en_disco()
                               except Exception as e_acierto:
                                    # Use 36 spaces for indentation
                                    print(f"      WARN: Error guardando acierto: {e_acierto}")
                            else: # Ya estaba en memoria
                                 # Use 32 spaces for indentation
                                 print("      La solución ya estaba en memoria. No se necesita guardar.")
                        else: # clave_pregunta_acierto es None
                             print("      WARN Acierto: No se pudo generar/obtener clave para guardar el acierto.")
                        # --- ¡FIN LÓGICA DE GUARDADO (ACIERTO - ROTACIÓN)! ---

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

