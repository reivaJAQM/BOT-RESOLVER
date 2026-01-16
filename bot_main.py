import time
import sys
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- NUESTROS MÓDULOS ---
import config
import bot_selectors as sel
import bot_login
import ia_utils          
import bot_memory as mem 

# --- LOS ESPECIALISTAS (SOLVERS) ---
import solvers.solver_ordenar as t1_solver   # T1
import solvers.solver_completar as t2_solver # T2
import solvers.solver_match as t4_solver     # T4
import solvers.solver_escribir as t_write_solver # T10, T11, T12
import solvers.solver_inline as t13_solver   # T13
import solvers.solver_tf as tf_solver        # TF

# --- CONFIGURACIÓN ---
print("🚀 Iniciando Bot Modular (Full Support: T1, T2, T4, T10-12, T13, TF)...")
service = EdgeService(executable_path=config.DRIVER_PATH)
driver = webdriver.Edge(service=service)
driver.maximize_window()
wait = WebDriverWait(driver, 15)

try:
    # 1. LOGIN AUTOMÁTICO
    if not bot_login.realizar_login(driver, wait, sel, config):
        print("❌ Falló el login. Terminando.")
        sys.exit()

    # 2. BUCLE PRINCIPAL (BUSCAR LECCIONES)
    while True:
        print("\n📚 --- BUSCANDO LECCIONES ---")
        try:
            # Esperar lista
            try:
                wait.until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
            except TimeoutException:
                print("   ⏳ Esperando lista de lecciones...")
                time.sleep(3); continue

            # Cargar todas
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            lecciones = driver.find_elements(*sel.SELECTOR_LECCION_DISPONIBLE)
            if not lecciones:
                print("   🎉 No hay lecciones visibles. Reintentando en 5s...")
                time.sleep(5); continue
            
            # Abrir primera
            leccion = lecciones[0]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", leccion)
            time.sleep(1)
            
            try: leccion.click()
            except: driver.execute_script("arguments[0].click();", leccion)
            
            print("   🚀 Lección seleccionada. Esperando botón START...")
            try:
                boton_start = wait.until(EC.element_to_be_clickable(sel.SELECTOR_BOTON_START))
                boton_start.click()
                print("   ✅ Lección INICIADA.")
            except TimeoutException:
                print("   ⚠️ No salió START. Asumiendo adentro.")

            # 3. BUCLE DE PREGUNTAS
            while True:
                # A. VERIFICAR FIN
                try:
                    boton_continue = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable(sel.SELECTOR_CONTINUE)
                    )
                    print("   🏁 LECCIÓN TERMINADA. Saliendo...")
                    boton_continue.click()
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located(sel.SELECTOR_LECCION_DISPONIBLE))
                    break 
                except:
                    pass 

                print("\n👀 Analizando pregunta...")
                time.sleep(1.5) 

                # B. DETECCIÓN
                tipo_detectado = None
                
                # --- DETECTORES DE ESTRUCTURA ---
                if len(driver.find_elements(*sel.SELECTOR_CONTENEDOR_ORDENAR)) > 0:
                    tipo_detectado = "T1"
                elif len(driver.find_elements(*sel.SELECTOR_FILAS_EMPAREJAR)) > 0:
                    tipo_detectado = "T4"
                elif len(driver.find_elements(*sel.SELECTOR_TIPO_13_FILAS)) > 0:
                    tipo_detectado = "T13"
                elif len(driver.find_elements(*sel.SELECTOR_CAJAS_TF)) > 0:
                    tipo_detectado = "TF"
                elif len(driver.find_elements(*sel.SELECTOR_LINEAS_COMPLETAR)) > 0:
                    tipo_detectado = "T2"

                # --- DETECTORES DE INPUT/ESCRITURA ---
                # Importante el orden: T12 (Audio+Input) > T10 (Letras+Input) > T11 (Solo Input)
                elif len(driver.find_elements(*sel.SELECTOR_INPUT_ESCRIBIR)) > 0:
                    if len(driver.find_elements(*sel.SELECTOR_AUDIO)) > 0:
                        tipo_detectado = "T12"
                    elif len(driver.find_elements(*sel.SELECTOR_LETRAS_DESORDENADAS)) > 0:
                        tipo_detectado = "T10"
                    else:
                        tipo_detectado = "T11"

                # C. RESOLUCIÓN
                if tipo_detectado:
                    print(f"⚡ Tipo identificado: {tipo_detectado}")
                    
                    try: contexto = driver.find_element(*sel.SELECTOR_CONTEXTO).text 
                    except: contexto = ""

                    # Delegar al especialista
                    if tipo_detectado == "T1":
                        t1_solver.resolver(driver, sel, ia_utils, contexto)
                    elif tipo_detectado == "T2":
                        t2_solver.resolver(driver, sel, ia_utils, contexto)
                    elif tipo_detectado == "T4":
                        t4_solver.resolver(driver, sel, ia_utils, contexto)
                    elif tipo_detectado == "T13":
                        t13_solver.resolver(driver, sel, ia_utils, contexto)
                    elif tipo_detectado == "TF":
                        tf_solver.resolver(driver, sel, ia_utils, contexto, wait)
                    elif tipo_detectado in ["T10", "T11", "T12"]:
                        t_write_solver.resolver(driver, sel, ia_utils, contexto, tipo_detectado)
                    
                    # D. CHECK
                    print("   ✅ Solución aplicada. Buscando CHECK...")
                    try:
                        check = wait.until(EC.element_to_be_clickable(sel.SELECTOR_CHECK))
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", check)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", check)
                        
                        try:
                            ok = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(sel.SELECTOR_OK))
                            ok.click()
                            WebDriverWait(driver, 5).until(EC.invisibility_of_element_located(sel.SELECTOR_OK))
                        except: pass
                        
                    except Exception as e:
                        print(f"   ⚠️ Problema Check/Next: {e}")

                else:
                    print("   💤 Tipo NO SOPORTADO AÚN (o cargando). Esperando...")
                    time.sleep(2)

        except Exception as e:
            print(f"❌ Error bucle principal: {e}")
            time.sleep(5)

except KeyboardInterrupt:
    print("\n🛑 Bot detenido.")
finally:
    driver.quit()