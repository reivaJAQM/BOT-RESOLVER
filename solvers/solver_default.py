from selenium.webdriver.common.by import By
import time
import os
from urllib.parse import urlparse
import bot_memory as mem

def resolver(driver, sel, ia_utils, contexto, tipo_detectado):
    """
    Resuelve:
    - TIPO 9: Audio (Escuchar y elegir opción).
    - DEFAULT: Pregunta estándar de opción múltiple con imagen o texto.
    """
    print(f"   🔍 [Solver Default] Analizando {tipo_detectado}...")

    # 1. Obtener Opciones
    opciones_elems = driver.find_elements(*sel.SELECTOR_OPCIONES)
    opciones_txt = [e.text.strip() for e in opciones_elems if e.text.strip()]
    
    if not opciones_txt:
        print("      ❌ No se encontraron opciones.")
        return

    # 2. Generar Clave Única (Hash)
    pregunta_titulo = ""
    try: pregunta_titulo = driver.find_element(*sel.SELECTOR_PREGUNTA).text.strip()
    except: pass
    
    extra_hash = ""
    
    if tipo_detectado == "T9":
        # Hash de Audio
        try:
            audio_src = driver.find_element(*sel.SELECTOR_AUDIO).get_attribute("src")
            if audio_src:
                path = urlparse(audio_src).path
                extra_hash = f"AUD:{os.path.basename(path)}"
        except: pass
    else:
        # Hash de Imagen (si hay)
        try:
            imgs = driver.find_elements(By.TAG_NAME, "img")
            # Filtramos imágenes pequeñas/iconos
            imgs = [i for i in imgs if i.size['width'] > 50]
            if imgs:
                alt = imgs[0].get_attribute("alt")
                extra_hash = f"IMG:{alt}" if alt else f"IMG_DIM:{imgs[0].size['width']}x{imgs[0].size['height']}"
        except: pass

    clave_mem = f"{tipo_detectado}:{pregunta_titulo}||{extra_hash}||{'|'.join(sorted(opciones_txt))}"
    
    # 3. Memoria / IA
    respuesta = mem.buscar(clave_mem)
    
    if not respuesta:
        print(f"      🧠 Consultando IA ({tipo_detectado})...")
        if tipo_detectado == "T9":
             # La IA no puede escuchar, adivinamos o usamos contexto si es visible
             print("      ⚠️ Audio: IA intentará deducir por contexto/opciones.")
        
        # Usamos la función genérica de opción múltiple
        respuesta = ia_utils.obtener_respuesta_opcion_multiple(contexto, pregunta_titulo, opciones_txt)
        
        if respuesta:
            mem.registrar(clave_mem, respuesta)
    else:
        if isinstance(respuesta, list): respuesta = respuesta[0]
        print(f"      💾 Memoria: {respuesta}")

    # 4. Click
    if respuesta:
        clic_hecho = False
        # Normalización agresiva
        resp_norm = " ".join(str(respuesta).split()).lower()
        
        for btn in opciones_elems:
            btn_norm = " ".join(btn.text.split()).lower()
            if btn_norm == resp_norm:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.3)
                    btn.click()
                    print(f"      ✅ Click: {btn.text}")
                    clic_hecho = True; break
                except: pass
        
        if not clic_hecho:
            print(f"      ⚠️ No encontré botón exacto para: {respuesta}")