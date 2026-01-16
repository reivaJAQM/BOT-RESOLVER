import time
import sys
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- MÓDULOS PROPIOS ---
import config
import bot_selectors as sel
import bot_login
import ia_utils          
import bot_memory as mem 

# --- SOLVERS (LOS ESPECIALISTAS) ---
import solvers.solver_ordenar as t1_solver
import solvers.solver_completar as t2_solver
import solvers.solver_match as t4_solver
import solvers.solver_escribir as t_write_solver
import solvers.solver_inline as t13_solver
import solvers.solver_tf as tf_solver
import solvers.solver_seleccion as t_select_solver
import solvers.solver_t8_imagen as t8_solver
import solvers.solver_default as t_default_solver

# --- FUNCIÓN DE APRENDIZAJE ---
def aprender_de_errores(driver, ia_utils, mem, tipo, datos_contexto):
    """
    Si la respuesta fue incorrecta, lee el modal, extrae la solución y la guarda.
    """
    try:
        # 1. Verificar título del modal
        try:
            modal_titulo = driver.find_element(*sel.SELECTOR_MODAL_TITULO).text.lower()
        except:
            return # No hay título, quizá no cargó el modal

        if "incorrect" not in modal_titulo and "oops" not in modal_titulo:
            return # Fue correcta

        print("      ⚠️ Respuesta INCORRECTA. Intentando aprender...")
        try:
            contenido_modal = driver.find_element(*sel.SELECTOR_MODAL_CONTENIDO).text
        except:
            print("      ❌ No pude leer el contenido del modal.")
            return

        solucion_aprendida = None
        clave_memoria = datos_contexto.get("clave")
        items = datos_contexto.get("items")

        if not clave_memoria:
            return

        # 2. Extraer solución según el tipo
        if tipo == "T1": # Ordenar
             sol_temp = []
             if items:
                 for frase_list in items: 
                     s = ia_utils.extraer_solucion_ordenar(contenido_modal, frase_list)
                     if s: sol_temp.append(s)
                 if sol_temp: solucion_aprendida = sol_temp

        elif tipo == "T2": # Completar
            solucion_aprendida = ia_utils.extraer_solucion_lote_completar(contenido_modal, items)
            if solucion_aprendida:
                mem_existente = mem.buscar(clave_memoria)
                if isinstance(mem_existente, dict):
                    mem_existente.update(solucion_aprendida)
                    solucion_aprendida = mem_existente

        elif tipo == "TF": # True/False
            if datos_contexto.get("es_multi"):
                 solucion_aprendida = ia_utils.extraer_solucion_lote_tf(contenido_modal, items)
            else: 
                 solucion_aprendida = ia_utils.extraer_solucion_simple(contenido_modal, ["True", "False"])

        elif tipo == "T4" or tipo == "T8": # Emparejar
            claves = items
            defs = datos_contexto.get("extra")
            dic_sol = ia_utils.extraer_solucion_emparejar(contenido_modal, claves, defs)
            if dic_sol:
                lista_sol = []
                for k in claves:
                    if k in dic_sol: lista_sol.append(dic_sol[k])
                    elif k.strip() in dic_sol: lista_sol.append(dic_sol[k.strip()])
                if lista_sol: solucion_aprendida = lista_sol

        elif tipo in ["T6", "T7"]: # Selección
            dic_sol = ia_utils.extraer_solucion_del_error(contenido_modal, items)
            if dic_sol:
                lista_sol = []
                for preg in items:
                    if preg in dic_sol: lista_sol.append(dic_sol[preg])
                if lista_sol: solucion_aprendida = lista_sol

        elif tipo in ["T10", "T11", "T12"]: # Escribir
            if tipo == "T11" and datos_contexto.get("es_anagrama"):
                 solucion_aprendida = ia_utils.extraer_solucion_lote_escribir(contenido_modal, items)
            elif tipo == "T11":
                 solucion_aprendida = ia_utils.extraer_solucion_lote_escribir_opciones(contenido_modal, items)
            elif tipo == "T12":
                 solucion_aprendida = ia_utils.extraer_solucion_lote_dictado(contenido_modal, items)
            else: # T10
                 solucion_aprendida = ia_utils.extraer_solucion_lote_escribir(contenido_modal, items)

        elif tipo in ["T9", "DEFAULT", "T13"]:
            solucion_aprendida = ia_utils.extraer_solucion_simple(contenido_modal, items)

        # 3. Guardar
        if solucion_aprendida:
            print(f"      🎓 ¡APRENDIDO! Guardando...")
            mem.registrar(clave_memoria, solucion_aprendida)

    except Exception as e:
        print(f"      Error aprendizaje: {e}")

# --- CONFIGURACIÓN E INICIO ---
print("🚀 Iniciando Bot COMPLETO (Auto-Aprendizaje)...")
service = EdgeService(executable_path=config.DRIVER_PATH)
driver = webdriver.Edge(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 15)

try:
    if not bot_login.realizar_login(driver, wait, sel, config): sys.exit()

    while True: # BUCLE LECCIONES
        print("\n📚 --- BUSCANDO LECCIONES ---")
        try:
            try: wait.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
            except: time.sleep(3); continue

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"); time.sleep(1)
            lecciones = driver.find_elements(*sel.SELECTOR_LECCION_DISPONIBLE)
            if not lecciones: time.sleep(5); continue
            
            # Seleccionar lección
            leccion = lecciones[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", leccion); time.sleep(1)
            try: leccion.click()
            except: driver.execute_script("arguments[0].click();", leccion)
            
            try: wait.until(EC.element_to_be_clickable(sel.SELECTOR_BOTON_START)).click()
            except: pass
            print("   ✅ Lección INICIADA.")

            while True: # BUCLE PREGUNTAS
                try:
                    boton_continue = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(sel.SELECTOR_CONTINUE))
                    print("   🏁 LECCIÓN TERMINADA."); boton_continue.click()
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
                    break 
                except: pass 

                print("\n👀 Analizando pregunta...")
                time.sleep(1.5) 

                tipo = None
                # --- DETECCIÓN ---
                if len(driver.find_elements(*sel.SELECTOR_CONTENEDOR_ORDENAR)) > 0: tipo = "T1"
                elif len(driver.find_elements(*sel.SELECTOR_IMAGEN_EMPAREJAR)) > 0 and len(driver.find_elements(*sel.SELECTOR_DEFINICIONES_AZULES_XPATH)) > 0: tipo = "T8"
                elif len(driver.find_elements(*sel.SELECTOR_FILAS_EMPAREJAR)) > 0: tipo = "T4"
                elif len(driver.find_elements(*sel.SELECTOR_TIPO_13_FILAS)) > 0: tipo = "T13"
                elif len(driver.find_elements(*sel.SELECTOR_LINEAS_COMPLETAR)) > 0: tipo = "T2"
                elif len(driver.find_elements(*sel.SELECTOR_PARAGRAPH_CAJAS)) > 0: tipo = "T6"
                elif len(driver.find_elements(*sel.SELECTOR_ANSWER_Q_CAJAS)) > 0: tipo = "T7"
                elif len(driver.find_elements(*sel.SELECTOR_CAJAS_TF)) > 0: tipo = "TF"
                elif len(driver.find_elements(*sel.SELECTOR_MARK_TF_TRUE)) > 0: tipo = "TF"
                elif len(driver.find_elements(*sel.SELECTOR_INPUT_ESCRIBIR)) > 0:
                    if len(driver.find_elements(*sel.SELECTOR_AUDIO)) > 0: tipo = "T12"
                    elif len(driver.find_elements(*sel.SELECTOR_LETRAS_DESORDENADAS)) > 0: tipo = "T10"
                    else: tipo = "T11"
                elif len(driver.find_elements(*sel.SELECTOR_AUDIO)) > 0: tipo = "T9"
                elif len(driver.find_elements(*sel.SELECTOR_OPCIONES)) > 0: tipo = "DEFAULT"

                # --- RESOLUCIÓN ---
                datos_contexto = None
                if tipo:
                    print(f"⚡ Tipo identificado: {tipo}")
                    try: ctx = driver.find_element(*sel.SELECTOR_CONTEXTO).text 
                    except: ctx = ""

                    if tipo == "T1": datos_contexto = t1_solver.resolver(driver, sel, ia_utils, ctx)
                    elif tipo == "T2": datos_contexto = t2_solver.resolver(driver, sel, ia_utils, ctx)
                    elif tipo == "T4": datos_contexto = t4_solver.resolver(driver, sel, ia_utils, ctx)
                    elif tipo == "T8": datos_contexto = t8_solver.resolver(driver, sel, ia_utils, ctx)
                    elif tipo == "T13": datos_contexto = t13_solver.resolver(driver, sel, ia_utils, ctx)
                    elif tipo == "TF": datos_contexto = tf_solver.resolver(driver, sel, ia_utils, ctx, wait)
                    elif tipo in ["T6", "T7"]: datos_contexto = t_select_solver.resolver(driver, sel, ia_utils, ctx, tipo)
                    elif tipo in ["T10", "T11", "T12"]: datos_contexto = t_write_solver.resolver(driver, sel, ia_utils, ctx, tipo)
                    elif tipo in ["T9", "DEFAULT"]: datos_contexto = t_default_solver.resolver(driver, sel, ia_utils, ctx, tipo)

                    print("   ✅ Check...")
                    try:
                        check = wait.until(EC.element_to_be_clickable(sel.SELECTOR_CHECK))
                        driver.execute_script("arguments[0].click();", check)
                        
                        # Manejo del Modal (Aprendizaje)
                        try:
                            ok_btn = wait.until(EC.element_to_be_clickable(sel.SELECTOR_OK))
                            if datos_contexto:
                                aprender_de_errores(driver, ia_utils, mem, tipo, datos_contexto)
                            ok_btn.click()
                            time.sleep(1)
                            wait.until(EC.invisibility_of_element_located(sel.SELECTOR_OK))
                        except: pass
                    except Exception as e:
                        print(f"   ⚠️ Problema Check/Next: {e}")
                else:
                    print("   💤 Aún no detecto nada... Esperando...")
                    time.sleep(2)

        except Exception as e:
            print(f"❌ Error bucle: {e}")
            time.sleep(5)

except KeyboardInterrupt: driver.quit()