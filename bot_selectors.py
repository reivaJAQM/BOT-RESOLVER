# selectors.py
# Almacena todos los selectores del DOM para mantener el bot principal limpio.

from selenium.webdriver.common.by import By

SELECTOR_CERRAR_POPUP = (By.XPATH, "//i[text()='Cerrar']")
SELECTOR_INICIA_SESION_VERDE = (By.XPATH, "//button[text()='Inicia Sesión']")
SELECTOR_USUARIO_INPUT = (By.ID, "mail-address")
SELECTOR_PASSWORD_INPUT = (By.ID, "password")
SELECTOR_ACCEDER_AMARILLO = (By.XPATH, "//button[text()='Iniciar sesión']")
# --- ¡MODIFICADO! Unificado Reading y Grammar ---
SELECTOR_LECCION_DISPONIBLE = (By.XPATH, "//img[(contains(@src, 'Reading') or contains(@src, 'Grammar')) and ../div[@class='bfill' and not(contains(@style, 'height: 100%'))]]")
SELECTOR_BOTON_START = (By.XPATH, "//a[text()='Start']")
SELECTOR_CONTEXTO = (By.CLASS_NAME, "overflow-y-auto")
SELECTOR_PREGUNTA = (By.XPATH, "//*[contains(@class, 'text-green-700')]")
SELECTOR_OPCIONES = (By.XPATH, "//button[contains(@class, 'md:px-8')]") # Opción Múltiple
SELECTOR_CONTENEDOR_ORDENAR = (By.XPATH, "//div[@data-rbd-droppable-id='droppable']") # Ordenar
SELECTOR_CAJAS_ORDENAR = (By.XPATH, ".//div[@data-rbd-draggable-id]") # Ordenar
SELECTOR_TEXTO_CAJA_ORDENAR = (By.TAG_NAME, "p") # Ordenar (Texto dentro de la caja)
SELECTOR_LINEAS_COMPLETAR = (By.XPATH, "//div[contains(@class,'card') and .//button[contains(@class,'text-gray-700')]]") # Completar
SELECTOR_SPANS_LINEA = (By.XPATH, "./div/span[@class='inline-block']") # Completar (No usado directamente)
SELECTOR_BOTONES_OPCION_COMPLETAR = (By.XPATH, ".//button[contains(@class,'text-gray-700')]") # Completar
SELECTOR_CAJAS_TF = (By.XPATH, "//div[contains(@class, 'card')][.//button[normalize-space()='True']]") # True/False Múltiple
SELECTOR_TEXTO_AFIRMACION_TF = (By.XPATH, ".//span[@class='inline-block'][1]") # True/False Múltiple
SELECTOR_BOTON_TRUE_TF = (By.XPATH, ".//button[normalize-space()='True']") # True/False Múltiple
SELECTOR_BOTON_FALSE_TF = (By.XPATH, ".//button[normalize-space()='False']") # True/False Múltiple
SELECTOR_DEFINICIONES_AZULES_XPATH = (By.XPATH, "//span[contains(@class, 'cardCheck')]") # Emparejar (Spans azules movibles)
SELECTOR_FILAS_EMPAREJAR = (By.XPATH, "//div[contains(@class, 'grid grid-cols-2')][.//button[contains(text(), 'Waiting answer')]]") # Emparejar (Contenedor de palabra y destino)
SELECTOR_PALABRA_CLAVE_TAG = "h2" # Emparejar - Usamos TAG_NAME para palabra clave
# SELECTOR_DESTINO_EMPAREJAR_XPATH = (By.XPATH, ".//button[contains(text(), 'Waiting answer')]") # Emparejar (No necesario con cola)
SELECTOR_CHECK = (By.XPATH, "//button[translate(normalize-space(text()), 'CHECK', 'check')='check']")
# SELECTOR_NUM_PREGUNTA = (By.XPATH, "//span[contains(text(), 'Question')]") # No usado activamente
SELECTOR_CONTINUE = (By.XPATH, "//button[normalize-space()='CONTINUE']")
SELECTOR_PARAGRAPH_CAJAS = (By.XPATH, "//div[contains(@class, 'card')][.//button[normalize-space()='1']]") # TIPO 6: Cajas con botones numéricos
SELECTOR_PARAGRAPH_IDEA_TEXT = (By.XPATH, ".//span[1]") # TIPO 6: El texto de la idea
SELECTOR_ANSWER_Q_CAJAS = (By.XPATH, "//div[contains(@class, 'card')][.//span][count(.//button) > 1 and not(.//button[normalize-space()='True'])]") # TIPO 7: Cajas OM
SELECTOR_ANSWER_Q_TEXTO = (By.XPATH, ".//span[1]") # TIPO 7: El texto de la pregunta dentro de la caja
SELECTOR_ANSWER_Q_BOTONES = (By.XPATH, ".//button") # TIPO 7: Los botones de opciones dentro de la caja
SELECTOR_OK = (By.CLASS_NAME, "swal2-confirm") # Botón OK del modal
SELECTOR_MODAL_TITULO = (By.CLASS_NAME, "swal2-title") # Título (ej. "Correct!" o "Incorrect!")
SELECTOR_MODAL_CONTENIDO = (By.CLASS_NAME, "swal2-html-container") # Contenido (donde suele estar la respuesta)
SELECTOR_SKIP = (By.XPATH, "//button[normalize-space()='SKIP']") # Botón Skip

# Selectores CSS para JavaScript (más simples)
SELECTOR_DEFINICIONES_AZULES_CSS = "span.cardCheck" # Emparejar
SELECTOR_FILAS_EMPAREJAR_CSS = "div.grid.grid-cols-2" # Emparejar
SELECTOR_PALABRA_CLAVE_CSS = "h2" # Emparejar
# SELECTOR_DESTINO_EMPAREJAR_CSS = "button" # Emparejar (No necesario con cola)

# --- Selectores para TIPO 5: Single True/False ("Mark T/F") ---
SELECTOR_MARK_TF_TEXT = (By.XPATH, "//div[contains(@class, 'card')]//span[@class='inline-block'][1]")
SELECTOR_MARK_TF_TRUE = (By.XPATH, "//div[contains(@class, 'card')]//button[normalize-space()='True']")
SELECTOR_MARK_TF_FALSE = (By.XPATH, "//div[contains(@class, 'card')]//button[normalize-space()='False']")
