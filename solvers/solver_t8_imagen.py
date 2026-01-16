from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from collections import defaultdict
import time
import bot_memory as mem

def resolver(driver, sel, ia_utils, contexto):
    """Resuelve TIPO 8: Emparejar Imágenes con Definiciones."""
    print("   🔍 [Solver T8] Analizando Imágenes...")
    
    # 1. Extraer Definiciones (Columna derecha)
    js_defs = f"return Array.from(document.querySelectorAll('{sel.SELECTOR_DEFINICIONES_AZULES_CSS}')).map(e => e.innerText.trim());"
    definiciones = [d for d in driver.execute_script(js_defs) if d]
    
    # Mapear texto a elemento web
    elems_def = driver.find_elements(*sel.SELECTOR_DEFINICIONES_AZULES_XPATH)
    mapa_defs = {e.text.strip(): e for e in elems_def if e.text.strip()}
    
    # 2. Extraer Imágenes y generar Hashes (Columna izquierda)
    filas_img = driver.find_elements(*sel.SELECTOR_IMAGEN_EMPAREJAR)
    claves_img = []
    hash_counts = defaultdict(int)
    
    for i, fila in enumerate(filas_img):
        try:
            img = fila.find_element(By.TAG_NAME, "img")
            alt = img.get_attribute("alt")
            alt = alt.strip() if alt else ""
            
            # Generar Hash único
            hash_base = ""
            if alt and alt.lower() != "descripción de la imagen":
                hash_base = f"IMG_ALT:{alt}"
            else:
                # Si no hay ALT útil, usamos dimensiones
                size = img.size
                hash_base = f"IMG_DIM:{size['width']}x{size['height']}"
            
            # Manejo de duplicados
            count = hash_counts[hash_base]
            hash_final = f"{hash_base}_{count}" if count > 0 else hash_base
            hash_counts[hash_base] += 1
            
            claves_img.append(hash_final)
            print(f"      Img {i+1}: {hash_final}")
        except:
            claves_img.append(f"error_img_{i}")

    if not definiciones or not claves_img:
        print("      ❌ Faltan datos (defs o imgs).")
        return

    # 3. Memoria / IA
    clave_mem = f"T8:{'|'.join(sorted(claves_img))}||{'|'.join(sorted(definiciones))}"
    solucion = mem.buscar(clave_mem)
    
    if not solucion:
        print("      🧠 Consultando IA (Emparejar Imágenes)...")
        # Le pasamos los ALTs/Hashes a la IA para que intente relacionarlos
        pares = ia_utils.obtener_emparejamientos(claves_img, definiciones)
        if pares:
            solucion = []
            for k in claves_img:
                if k in pares: solucion.append(pares[k])
            
            if len(solucion) == len(claves_img):
                mem.registrar(clave_mem, solucion)
    else:
        if isinstance(solucion, list) and isinstance(solucion[0], list): solucion = solucion[0]
        print(f"      💾 Memoria: {len(solucion)} pares.")

    # 4. Click
    if solucion:
        for def_txt in solucion:
            elem = mapa_defs.get(def_txt)
            if not elem: elem = mapa_defs.get(def_txt.strip())
            
            if elem:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(0.3)
                    elem.click()
                    print(f"      ✅ Click: {def_txt[:20]}...")
                    time.sleep(1)
                except Exception as e: print(f"      ❌ Error click: {e}")