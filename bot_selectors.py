# bot_selectors.py
from selenium.webdriver.common.by import By

# --- NAVEGACIÓN GENERAL ---
SELECTOR_CERRAR_POPUP = (By.XPATH, "//i[text()='Cerrar'] | //button[contains(text(), 'Cerrar')]")
SELECTOR_INICIA_SESION_VERDE = (By.XPATH, "//button[text()='Inicia Sesión']")
SELECTOR_USUARIO_INPUT = (By.ID, "mail-address")
SELECTOR_PASSWORD_INPUT = (By.ID, "password")
SELECTOR_ACCEDER_AMARILLO = (By.XPATH, "//button[text()='INICIAR SESIÓN']")

# --- MENÚ Y LECCIONES ---
SELECTOR_LECCION_DISPONIBLE = (By.XPATH, "(//img[(contains(@src, 'Reading') or contains(@src, 'Grammar') or contains(@src, 'teacher') or contains(@src, 'Vocabulary')) and ../div[@class='bfill' and not(contains(@style, 'height: 100%'))]]) | (//img[contains(@src, 'Writing') and ../div[@class='bfill' and not(contains(@style, 'height: 100%'))] and ancestor::div[contains(@class, 'tooltip')][1]//h2[normalize-space()='writing']])")
SELECTOR_BOTON_START = (By.XPATH, "//a[text()='Start']")

# --- NAVEGACIÓN DENTRO DEL TEST ---
SELECTOR_CONTEXTO = (By.CLASS_NAME, "overflow-y-auto")
SELECTOR_PREGUNTA = (By.XPATH, "//h2[contains(@class, 'text-gray-800')]")
SELECTOR_CHECK = (By.XPATH, "//button[translate(normalize-space(text()), 'CHECK', 'check')='check' and not(contains(@class, 'text-gray-700'))]")
SELECTOR_CONTINUE = (By.XPATH, "//button[normalize-space()='CONTINUE']")
SELECTOR_OK = (By.CLASS_NAME, "swal2-confirm")
SELECTOR_SKIP = (By.XPATH, "//button[normalize-space()='SKIP']")

# --- TIPO 1: ORDENAR (Drag & Drop) - ¡ARREGLADO! ---
# Usamos 'contains' porque el ID ahora es dinámico (ej: droppable-desktop-0)
SELECTOR_CONTENEDOR_ORDENAR = (By.XPATH, "//div[contains(@data-rbd-droppable-id, 'droppable')]") 

# Los elementos ahora tienen la clase 'cursor-grab' y el atributo draggable
SELECTOR_CAJAS_ORDENAR = (By.XPATH, ".//div[@data-rbd-draggable-id]") 

# El texto está directo en el div o en un hijo simple
SELECTOR_TEXTO_CAJA_ORDENAR = (By.XPATH, ".") 

# --- OTROS TIPOS (Sin cambios) ---
SELECTOR_LINEAS_COMPLETAR = (By.XPATH, "//div[contains(@class,'card') and .//button[contains(@class,'text-gray-700')]]") 
SELECTOR_BOTONES_OPCION_COMPLETAR = (By.XPATH, ".//button[contains(@class,'text-gray-700')]") 
SELECTOR_FILAS_EMPAREJAR = (By.XPATH, "//div[.//h2[contains(@class, 'text-gray-800') and contains(@class, 'text-base')]]")
SELECTOR_DEFINICIONES_AZULES_XPATH = (By.XPATH, "//div[contains(@class, 'cardCheck')] | //span[contains(@class, 'border-b-4')]")
SELECTOR_DEFINICIONES_AZULES_CSS = "div.cardCheck, span.border-b-4"
SELECTOR_IMAGEN_EMPAREJAR = (By.XPATH, "//div[contains(@class, 'shadow-lg') and contains(@class, 'overflow-hidden')][.//img]")
SELECTOR_CAJAS_TF = (By.XPATH, "//div[contains(@class, 'flex') and .//span[contains(@class, 'text-gray-700')] and (.//button[contains(normalize-space(), 'TRUE')] or .//button[contains(normalize-space(), 'True')])] ")
SELECTOR_MARK_TF_TRUE = (By.XPATH, "//div[contains(@class, 'card')]//button[normalize-space()='True']")
SELECTOR_MARK_TF_FALSE = (By.XPATH, "//div[contains(@class, 'card')]//button[normalize-space()='False']")
SELECTOR_TEXTO_AFIRMACION_TF = (By.XPATH, ".//span[1]") 
SELECTOR_PARAGRAPH_CAJAS = (By.XPATH, "//div[contains(@class, 'card')][.//button[normalize-space()='1']]") 
SELECTOR_PARAGRAPH_IDEA_TEXT = (By.XPATH, ".//span[1]")
SELECTOR_ANSWER_Q_CAJAS = (By.XPATH, "//div[contains(@class, 'card')][.//span[1]][count(.//button[not(ancestor::span[contains(@class,'inline-block')])]) > 1 and not(.//button[normalize-space()='True'])]")
SELECTOR_ANSWER_Q_TEXTO = (By.XPATH, ".//span[1]")
SELECTOR_ANSWER_Q_BOTONES = (By.XPATH, ".//button")
SELECTOR_INPUT_ESCRIBIR = (By.XPATH, "//input[@type='text'] | //textarea")
SELECTOR_AUDIO = (By.XPATH, "//button[.//svg] | //audio | //div[contains(@class, 'audio-player')]")
SELECTOR_LETRAS_DESORDENADAS = (By.XPATH, "//div[contains(@class, 'flex')]//span[contains(@class, 'font-bold')] | //p[contains(@class, 'text-justify') and contains(@class, 'uppercase') and contains(., '/')]")
SELECTOR_FRASE_T11 = (By.XPATH, "./preceding-sibling::div | ./parent::div//p | ./ancestor::*[.//span[contains(@class, 'text-gray-700')]][1]//span[contains(@class, 'text-gray-700')]")
SELECTOR_OPCIONES = (By.XPATH, """
    //div[contains(@class, 'cardCheck')] | 
    //div[contains(@class, 'option')] | 
    //button[
        not(.//svg) and 
        not(contains(translate(., 'CHECK', 'check'), 'check')) and 
        not(contains(translate(., 'SKIP', 'skip'), 'skip')) and 
        not(contains(translate(., 'START', 'start'), 'start')) and
        string-length(normalize-space(.)) > 0
    ]
""")

# Aseguramos que el cuerpo de la pregunta capture texto que pueda estar suelto
SELECTOR_CUERPO_PREGUNTA = (By.XPATH, "//div[contains(@class, 'card')]//p | //div[contains(@class, 'card')]//span[contains(@class, 'text-justify')]")
SELECTOR_MODAL_TITULO = (By.CLASS_NAME, "swal2-title")
SELECTOR_MODAL_CONTENIDO = (By.CLASS_NAME, "swal2-html-container")