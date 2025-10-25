# bot_main.py
# Script principal que orquesta el bot.
# ¡Refactorizado con "Plan Maestro" y "Plan S"!
# Doble chequeo de indentación TIPO 3 vs CHECK.

import time
import json
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
    wait_short = WebDriverWait(driver, 5)
    wait_long = WebDriverWait(driver, 15)
    wait_extra_long = WebDriverWait(driver, 25)
    print("Navegador Listo!")
except Exception as e:
    print(f"Error iniciando navegador: {e}"); exit()

# --- INICIO DE LA MEMORIA DEL BOT ---
preguntas_ya_vistas = {}
opciones_ya_vistas = {}
soluciones_correctas = {} # --- NUEVA MEMORIA PARA RESPUESTAS APRENDIDAS ---
# --- FIN DE LA MEMORIA DEL BOT ---

if ia_utils.model is None:
    print("ERROR FATAL: El modelo de IA no se pudo inicializar.")
    driver.quit()
    exit()

# --- INICIO DEL SCRIPT ---
try:
    print(f"Navegando: {config.URL_INICIAL}"); driver.get(config.URL_INICIAL)

    # --- LOGIN ---
    try:
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

        # --- 1. ENCONTRAR Y EMPEZAR LA SIGUIENTE LECCIÓN ---
        try:
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
            print("\n" + "#"*40); print("¡NO SE ENCONTRARON MÁS LECCIONES DISPONIBLES!"); print("¡Bot ha completado todo el trabajo! Terminando..."); break
        except Exception as e:
            print(f"Error al intentar empezar la siguiente lección: {e}"); break

        # --- BUCLE DE PREGUNTAS (INTERNO) ---
        pregunta_actual_texto = ""
        tipo_pregunta = ""; clave_pregunta = None; lista_ideas_texto = []; lista_de_preguntas = []; lista_afirmaciones_texto = []

        while True:
            print("\n" + "="*30)
            try:
                # --- DETECCIÓN FIN ---
                print("Verificando fin...")
                try:
                    boton_continue = wait_short.until(EC.element_to_be_clickable(sel.SELECTOR_CONTINUE))
                    print("FIN DE LA LECCIÓN! Clic CONTINUE..."); boton_continue.click()
                    print("Esperando regreso a la página de lecciones..."); wait_long.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
                    print("Página de lecciones cargada. Buscando siguiente lección..."); time.sleep(2); break
                except TimeoutException:
                    print("Test continúa...")

                # --- LÓGICA DE ESPERA (PLAN MAESTRO) ---
                print("Esperando nueva pregunta..."); current_url = driver.current_url
                try:
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
                elif len(driver.find_elements(*sel.SELECTOR_FILAS_EMPAREJAR)) > 0: print("      Contenido detectado: [TIPO 4]"); tipo_pregunta = "TIPO_4_EMPAREJAR"
                else: print("      No se detectó contenido especial. Se asume [DEFAULT]"); tipo_pregunta = "TIPO_DEFAULT_OM"

                print("Leyendo datos (Contexto y Título)...")
                try: contexto = wait_short.until(EC.visibility_of_element_located(sel.SELECTOR_CONTEXTO)).text
                except TimeoutException: print("Warn: No contexto."); contexto = ""
                try:
                    pregunta_elemento = wait_short.until(EC.presence_of_element_located(sel.SELECTOR_PREGUNTA)); pregunta = pregunta_elemento.text.strip()
                    WebDriverWait(driver, 3).until(lambda d: d.find_element(*sel.SELECTOR_PREGUNTA).text.strip() != pregunta_actual_texto)
                    pregunta_actual_texto = pregunta; print(f"      Título detectado: '{pregunta}'")
                except TimeoutException:
                    print("Warn: No se encontró/actualizó el título."); pregunta = f"pregunta_sin_titulo_{contexto[:50]}"; pregunta_actual_texto = pregunta

                # --- TIPO 1: ORDENAR ---
                if tipo_pregunta == "TIPO_1_ORDENAR":
                    print("Tipo: ORDENAR."); # ... (código TIPO 1) ...
                    contenedor = wait_long.until(EC.presence_of_element_located(sel.SELECTOR_CONTENEDOR_ORDENAR))
                    cajas_inicial = contenedor.find_elements(*sel.SELECTOR_CAJAS_ORDENAR)
                    frases_des = []; ids = []; map_id_a_texto = {}
                    for i, c in enumerate(cajas_inicial):
                        try:
                            t = c.text.strip()
                            d_id = c.get_attribute("data-rbd-draggable-id")
                            if t and d_id: frases_des.append(t); ids.append(d_id); map_id_a_texto[d_id] = t; print(f" Caja {i}(ID:{d_id}):'{t}'")
                        except NoSuchElementException: continue
                    if not frases_des: raise Exception("No frases ord.")
                    print(f"Frases: {frases_des}"); print("IA (Ord)...")
                    orden_ia = ia_utils.obtener_orden_correcto(contexto, frases_des)
                    if not orden_ia: raise Exception("IA (Ord) falló.")
                    print(f"Orden IA: {orden_ia}"); print("Reordenando JS...")
                    map_texto_a_id = {v: k for k, v in map_id_a_texto.items()}
                    ids_ok = [map_texto_a_id.get(t) for t in orden_ia if map_texto_a_id.get(t)]
                    if len(ids_ok) != len(frases_des): raise Exception("Fallo mapeo IDs JS.")
                    js = "var c=arguments[0],ids=arguments[1],m={};for(let i=0;i<c.children.length;i++){let o=c.children[i],d=o.firstElementChild;if(d&&d.getAttribute('data-rbd-draggable-id')){m[d.getAttribute('data-rbd-draggable-id')]=o;}}while(c.firstChild)c.removeChild(c.firstChild);ids.forEach(id=>{if(m[id])c.appendChild(m[id]);else console.error('JS Err ID:',id);});console.log('JS OK.');"
                    try: driver.execute_script(js, contenedor, ids_ok); print("JS OK."); time.sleep(1)
                    except JavascriptException as e: print(f"Error JS: {e}"); raise Exception("Fallo JS.")

                #--- TIPO 2: COMPLETAR PALABRAS ---
                elif tipo_pregunta == "TIPO_2_COMPLETAR":
                    print("Tipo: COMPLETAR PALABRAS."); # ... (código TIPO 2 con memoria Plan S) ...
                    lineas = wait_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_LINEAS_COMPLETAR))
                    if not lineas: raise Exception("No se encontraron líneas.")
                    print(f"Encontradas {len(lineas)} líneas.")
                    exito_global = True
                    for i, linea in enumerate(lineas):
                        print(f"\nProcesando línea {i+1}...")
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", linea); time.sleep(0.3)
                        spans = linea.find_elements(By.XPATH, "./div/span[@class='inline-block']")
                        grupo_actual_botones = []; indice_grupo = 0; span_indices_grupo = []
                        for j, span in enumerate(spans):
                            botones_en_span = span.find_elements(*sel.SELECTOR_BOTONES_OPCION_COMPLETAR)
                            if botones_en_span: grupo_actual_botones.extend(botones_en_span); span_indices_grupo.append(j)
                            if (not botones_en_span and grupo_actual_botones) or (j == len(spans) - 1 and grupo_actual_botones):
                                indice_grupo += 1
                                opciones_palabra = [b.text.strip() for b in grupo_actual_botones if b.text.strip()]
                                if not opciones_palabra: print(f"Warn: Grupo {indice_grupo} vacío."); grupo_actual_botones = []; span_indices_grupo = []; continue
                                frase_para_ia = ""; placeholder_colocado = False
                                for idx_s, s_temp in enumerate(spans):
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
                                    if b.text.strip() == palabra_correcta_ia: boton_clic = b; break
                                if boton_clic:
                                    try: print(f"      Clic en '{palabra_correcta_ia}'..."); driver.execute_script("arguments[0].click();", boton_clic); time.sleep(0.4)
                                    except Exception as e: print(f"Error clic: {e}"); exito_global = False
                                else: print(f"Error CRÍTICO: Botón '{palabra_correcta_ia}' no encontrado."); exito_global = False
                                grupo_actual_botones = []; span_indices_grupo = []
                    if not exito_global: raise Exception("Fallo al completar palabras.")

                # --- TIPO 3: TRUE/FALSE MÚLTIPLE [CORREGIDO] ---
                elif tipo_pregunta == "TIPO_3_TF_MULTI":
                    print("Tipo: TRUE/FALSE MÚLTIPLE.")
                    cajas_afirmacion = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_CAJAS_TF))
                    if not cajas_afirmacion: raise Exception("No se encontraron cajas True/False.")
                    print(f"Encontradas {len(cajas_afirmacion)} afirmaciones.")

                    lista_afirmaciones_texto = [] # Reiniciar para esta pregunta
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
                                lista_afirmaciones_texto.append(texto_afirmacion)
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
                        for texto_afirmacion in lista_afirmaciones_texto:
                            clave_individual = texto_afirmacion; opciones_ya_vistas[clave_individual]=["True","False"]
                            respuesta_tf_ia = None
                            if clave_individual in preguntas_ya_vistas:
                                respuesta_anterior = preguntas_ya_vistas[clave_individual]; respuesta_tf_ia = "False" if respuesta_anterior == "True" else "True"
                                print(f"      WARN: Afirmación '{texto_afirmacion[:30]}...' repetida. Forzando: '{respuesta_tf_ia}'")
                            else:
                                print(f"      IA (T/F) para '{texto_afirmacion[:30]}...'?"); respuesta_tf_ia = ia_utils.obtener_true_false(contexto, texto_afirmacion)
                            if respuesta_tf_ia:
                                preguntas_ya_vistas[clave_individual] = respuesta_tf_ia; respuestas_tf_lote_temporal.append(respuesta_tf_ia)
                            else: print(f"Error IA T/F para afirmación: {texto_afirmacion}"); exito_ia_individual = False; break
                        if not exito_ia_individual: raise Exception("Fallo IA al obtener respuesta T/F individual.")
                        respuestas_tf_lote = respuestas_tf_lote_temporal
                        preguntas_ya_vistas[clave_pregunta] = respuestas_tf_lote

                    print(f"Respuestas T/F a usar: {respuestas_tf_lote}")

                    exito_global = True
                    print(">>> DEBUG: Entrando al bucle de clics TIPO 3")
                    for i, (respuesta_tf_ia, (caja, boton_true, boton_false)) in enumerate(zip(respuestas_tf_lote, elementos_cajas_botones)):
                        print(f"\n>>> DEBUG: Inicio clic iteración {i+1}")
                        try:
                            boton_a_clicar = boton_true if respuesta_tf_ia == "True" else boton_false
                            print(f"      Clic en '{respuesta_tf_ia}' para afirmación {i+1}...")
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                            wait_short.until(EC.element_to_be_clickable(boton_a_clicar))
                            driver.execute_script("arguments[0].click();", boton_a_clicar); time.sleep(0.3)
                            print(f">>> DEBUG: Clic OK en iteración {i+1}")
                        except Exception as e_inner:
                            print(f"Error en clic T/F iteración {i+1}: {e_inner}"); exito_global = False; break
                        print(f">>> DEBUG: Fin clic iteración {i+1}")

                    print(">>> DEBUG: Saliendo del bucle de clics TIPO 3") # Esta línea DEBE imprimirse siempre al final
                    if not exito_global: raise Exception("Fallo durante los clics de T/F Múltiple.")

                # --- TIPO 6: MATCH IDEA TO PARAGRAPH ---
                elif tipo_pregunta == "TIPO_6_PARAGRAPH":
                    print("Tipo: MATCH IDEA TO PARAGRAPH."); # ... (código TIPO 6 con memoria Plan S)...
                    cajas_ideas = wait_extra_long.until(EC.presence_of_all_elements_located(sel.SELECTOR_PARAGRAPH_CAJAS))
                    if not cajas_ideas: raise Exception("No cajas ideas.")
                    print(f"Encontradas {len(cajas_ideas)} ideas."); lista_ideas_texto = []; elementos_cajas = []
                    print("Recolectando ideas...");
                    for k, caja in enumerate(cajas_ideas):
                        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", caja); time.sleep(0.1)
                        try:
                            idea_elem = caja.find_element(*sel.SELECTOR_PARAGRAPH_IDEA_TEXT); idea_texto = idea_elem.text.strip()
                            if idea_texto: lista_ideas_texto.append(idea_texto); elementos_cajas.append(caja); print(f"      Idea {k+1}: '{idea_texto}'")
                            else: print(f"Warn: Caja {k+1} sin texto.")
                        except (NoSuchElementException, TimeoutException) as e: print(f"Error leyendo idea {k+1}: {e}"); continue
                    if not lista_ideas_texto: raise Exception("No ideas recolectadas.")
                    clave_pregunta = "|".join(lista_ideas_texto)
                    if clave_pregunta in soluciones_correctas: print("      SOLUCIÓN ENCONTRADA."); respuestas_lote_ia = soluciones_correctas[clave_pregunta]
                    else:
                        respuesta_anterior_incorrecta = None
                        if clave_pregunta in preguntas_ya_vistas: respuesta_anterior_incorrecta = preguntas_ya_vistas[clave_pregunta]; print(f"      WARN: Pregunta repetida. Anterior: {respuesta_anterior_incorrecta}.")
                        print(f"Enviando {len(lista_ideas_texto)} ideas a IA..."); respuestas_lote_ia = ia_utils.obtener_numeros_parrafo_lote(contexto, lista_ideas_texto, respuesta_anterior_incorrecta)
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

                # --- TIPO 4: EMPAREJAR ---
                elif tipo_pregunta == "TIPO_4_EMPAREJAR":
                    print("Tipo: EMPAREJAR PALABRAS."); # ... (código TIPO 4) ...
                    exito_global = True; print("      Extrayendo definiciones (JS)...")
                    js_get_defs = f"return Array.from(document.querySelectorAll('{sel.SELECTOR_DEFINICIONES_AZULES_CSS}')).map(el => el.innerText.trim());"
                    try:
                        definiciones = driver.execute_script(js_get_defs); definiciones = [d for d in definiciones if d]
                        if not definiciones: raise Exception("JS no encontró texto def.")
                        map_texto_def_a_elemento = {}
                        spans_defs_selenium = wait_long.until(EC.presence_of_all_elements_located((sel.SELECTOR_DEFINICIONES_AZULES_XPATH)))
                        for s in spans_defs_selenium:
                            texto = s.text.strip();
                            if texto in definiciones: map_texto_def_a_elemento[texto] = s
                        if len(map_texto_def_a_elemento) != len(definiciones): print("Warn: No se mapearon elementos def.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo def: {e}")
                    print(f"      Definiciones encontradas: {definiciones}"); print("      Extrayendo palabras clave (en orden)...")
                    js_get_keywords = f"let k=[];document.querySelectorAll('{sel.SELECTOR_FILAS_EMPAREJAR_CSS}').forEach(r=>{{let e=r.querySelector('{sel.SELECTOR_PALABRA_CLAVE_CSS}');if(e)k.push(e.innerText.replace(/_/g,'').trim());}});return k;"
                    try:
                        palabras_clave = driver.execute_script(js_get_keywords); palabras_clave = [p for p in palabras_clave if p]
                        if not palabras_clave: raise Exception("JS no encontró palabras clave.")
                    except (JavascriptException, TimeoutException) as e: raise Exception(f"Error extrayendo palabras: {e}")
                    print(f"      Palabras clave encontradas (en orden): {palabras_clave}"); print("      IA (Emparejar)...")
                    pares_ia = ia_utils.obtener_emparejamientos(palabras_clave, definiciones)
                    if not pares_ia: raise Exception("IA (Emparejar) falló.")
                    print(f"      Pares IA: {pares_ia}"); print("      Clickeando en orden (Sistema de Cola)...")
                    for palabra in palabras_clave:
                        definicion_correcta = pares_ia.get(palabra)
                        if not definicion_correcta: print(f"Error: No par IA para '{palabra}'"); exito_global = False; continue
                        elemento_origen = map_texto_def_a_elemento.get(definicion_correcta)
                        if not elemento_origen: print(f"Error: No WebElement para def '{definicion_correcta}'"); exito_global = False; continue
                        print(f"            Clic en '{definicion_correcta}' (para '{palabra}')...");
                        try:
                            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", elemento_origen); time.sleep(0.3)
                            wait_long.until(EC.element_to_be_clickable(elemento_origen)).click(); print("                  Clic OK."); time.sleep(1.0)
                        except Exception as e: print(f"                  Error CRÍTICO (Click) en '{definicion_correcta}': {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo emparejar (Clic en orden).")

                # --- TIPO 5: MARK TRUE/FALSE (SINGLE) ---
                elif tipo_pregunta == "TIPO_5_TF_SINGLE":
                    print("Tipo: MARK TRUE/FALSE (Single)."); # ... (código TIPO 5 con memoria Plan S)...
                    try:
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
                    print("Tipo: ANSWER THE QUESTION (OM in Card)."); # ... (código TIPO 7 refactorizado con memoria Plan S)...
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
                            print(f"      Tarea {k+1}: '{real_pregunta}' Ops: {opciones}"); lista_de_tareas.append({"pregunta": real_pregunta, "opciones": opciones}); lista_de_preguntas.append(real_pregunta); elementos_cajas.append(caja)
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
                        try:
                            opciones_elementos_caja = caja.find_elements(*sel.SELECTOR_ANSWER_Q_BOTONES); boton_encontrado = None
                            for b in opciones_elementos_caja:
                                if b.text.strip() == respuesta_ia: boton_encontrado = b; break
                            if boton_encontrado: print(f"      Clic en '{boton_encontrado.text}'..."); driver.execute_script("arguments[0].click();", boton_encontrado); time.sleep(0.3)
                            else: print(f"Error CRÍTICO: Botón '{respuesta_ia}' no encontrado."); exito_global = False
                        except Exception as e: print(f"Error bucle clics T7: {e}"); exito_global = False
                    if not exito_global: raise Exception("Fallo al resolver 'Answer Question'.")

                # --- TIPO DEFAULT: OPCIÓN MÚLTIPLE ---
                elif tipo_pregunta == "TIPO_DEFAULT_OM":
                    print("Tipo: OPCIÓN MÚLTIPLE (Default)."); # ... (código TIPO DEFAULT con memoria Plan S)...
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
                        t_b = ' '.join(b.text.split()); t_ia = ' '.join(respuesta_ia.split())
                        if t_b == t_ia: boton_encontrado = b; break
                    if boton_encontrado: print(f"Clic en '{boton_encontrado.text}'..."); driver.execute_script("arguments[0].scrollIntoView(true);",boton_encontrado); time.sleep(0.2); boton_encontrado.click(); time.sleep(0.5)
                    else: raise Exception(f"Botón '{respuesta_ia}' no encontrado.")
                # --- FIN TIPOS ---

                # --- Común: CHECK y OK (Con Lógica de Aprendizaje) ---
                print(">>> DEBUG: Antes de Clic CHECK")
                print("Clic CHECK...");
                boton_check = wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_CHECK))
                boton_check.click(); time.sleep(0.5)
                print(">>> DEBUG: Después de Clic CHECK")

                # --- LÓGICA DE APRENDIZAJE (Plan S) ---
                print("Esperando modal de respuesta...")
                boton_ok = wait_long.until(EC.element_to_be_clickable(sel.SELECTOR_OK))
                try:
                    titulo_modal = driver.find_element(*sel.SELECTOR_MODAL_TITULO).text.lower()
                    if "incorrect" in titulo_modal or "oops" in titulo_modal:
                        print("      Respuesta INCORRECTA detectada. Buscando solución...")
                        contenido_modal = driver.find_element(*sel.SELECTOR_MODAL_CONTENIDO).text
                        preguntas_para_ia = None; opciones_para_ia = None
                        if tipo_pregunta == "TIPO_6_PARAGRAPH": clave_pregunta = "|".join(lista_ideas_texto); preguntas_para_ia = lista_ideas_texto
                        elif tipo_pregunta == "TIPO_7_OM_CARD": clave_pregunta = "|".join(lista_de_preguntas); preguntas_para_ia = lista_de_preguntas
                        elif tipo_pregunta == "TIPO_DEFAULT_OM" and clave_pregunta in opciones_ya_vistas: opciones_para_ia = opciones_ya_vistas[clave_pregunta]
                        elif tipo_pregunta == "TIPO_5_TF_SINGLE": opciones_para_ia = ["True", "False"] # clave_pregunta ya está definida
                        elif tipo_pregunta == "TIPO_3_TF_MULTI": clave_pregunta = "|".join(lista_afirmaciones_texto); preguntas_para_ia = lista_afirmaciones_texto
                        elif tipo_pregunta == "TIPO_2_COMPLETAR" and clave_pregunta in opciones_ya_vistas: opciones_para_ia = opciones_ya_vistas[clave_pregunta]

                        if clave_pregunta and preguntas_para_ia and contenido_modal:
                            if tipo_pregunta == "TIPO_3_TF_MULTI":
                                print("      Enviando texto a IA (Lote T/F) para extraer solución..."); solucion_lista_ordenada = ia_utils.extraer_solucion_lote_tf(contenido_modal, preguntas_para_ia)
                            else: # Para T6 y T7
                                print("      Enviando texto a IA (Lote Genérico) para extraer solución..."); solucion = ia_utils.extraer_solucion_del_error(contenido_modal, preguntas_para_ia)
                                if solucion:
                                    solucion_lista_ordenada = [str(solucion.get(p)).strip() for p in preguntas_para_ia]
                                    if None in solucion_lista_ordenada or 'none' in [s.lower() for s in solucion_lista_ordenada]: print(f"      IA (Lote Genérico) no pudo mapear solución: {solucion}"); solucion_lista_ordenada = None
                                else: solucion_lista_ordenada = None
                            if solucion_lista_ordenada: print(f"      ¡SOLUCIÓN LOTE APRENDIDA! -> {solucion_lista_ordenada}"); soluciones_correctas[clave_pregunta] = solucion_lista_ordenada
                            else: print("      IA (Lote) no pudo extraer o validar la solución.")
                        elif clave_pregunta and opciones_para_ia and contenido_modal:
                            print("      Enviando texto a IA (Simple) para extraer solución..."); solucion = ia_utils.extraer_solucion_simple(contenido_modal, opciones_para_ia)
                            if solucion: print(f"      ¡SOLUCIÓN SIMPLE APRENDIDA! -> {solucion}"); soluciones_correctas[clave_pregunta] = solucion
                            else: print("      IA (Simple) no pudo extraer solución.")
                        else: print(f"      No se implementó aprendizaje para ({tipo_pregunta}) o clave/opciones no encontradas.")
                    elif "correct" in titulo_modal: print("      Respuesta CORRECTA detectada.")
                except Exception as e: print(f"      WARN: No se pudo leer modal o aprender. {e}")

                print("Clic OK..."); boton_ok.click()
                print("Respuesta enviada! Esperando que desaparezca modal..."); wait_long.until(EC.invisibility_of_element_located(sel.SELECTOR_OK))
                print("Modal desaparecido. Cargando siguiente pregunta..."); time.sleep(0.5)

            except (TimeoutException, Exception) as e:
                # --- PLAN V: SKIP EN LUGAR DE REFRESH ---
                print(f"Error inesperado o Timeout: {e}")
                try:
                    wait_short.until(EC.element_to_be_clickable(sel.SELECTOR_CONTINUE)).click(); print("      FIN detectado tras error! Yendo a siguiente lección."); wait_long.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE)); break
                except (TimeoutException, NoSuchElementException):
                    print("      El test no ha terminado. Intentando 'SKIP'...");
                    try:
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