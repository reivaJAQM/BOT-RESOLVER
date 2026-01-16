from selenium.webdriver.common.by import By
import time
import bot_memory as mem

def resolver(driver, sel, ia_utils, contexto):
    """
    Resuelve TIPO 4: Emparejar definiciones (Click izquierdo -> Click derecho).
    Retorna datos para aprendizaje.
    """
    print("   🔍 [Solver Match] Analizando columnas de emparejamiento...")
    
    # 1. Extraer Definiciones (Columna derecha - Azul)
    js_defs = f"return Array.from(document.querySelectorAll('{sel.SELECTOR_DEFINICIONES_AZULES_CSS}')).map(e => e.innerText.trim());"
    definiciones_txt = []
    try:
        definiciones_txt = driver.execute_script(js_defs)
        definiciones_txt = [d for d in definiciones_txt if d]
    except: pass
    
    if not definiciones_txt:
        print("      ❌ No se encontraron definiciones (columna derecha).")
        return None

    # Mapear texto a elemento web para poder hacer click luego
    elems_def = driver.find_elements(*sel.SELECTOR_DEFINICIONES_AZULES_XPATH)
    mapa_defs_elems = {e.text.strip(): e for e in elems_def if e.text.strip()}

    # 2. Extraer Palabras Clave (Columna izquierda)
    js_kws = "return Array.from(document.querySelectorAll('h2.text-gray-800.text-base')).map(e => e.innerText.trim());"
    palabras_txt = []
    try:
        palabras_txt = driver.execute_script(js_kws)
        palabras_txt = [p for p in palabras_txt if p]
    except: pass

    if not palabras_txt:
        print("      ❌ No se encontraron palabras clave (columna izquierda).")
        return None

    print(f"      Encontradas: {len(palabras_txt)} palabras y {len(definiciones_txt)} definiciones.")

    # --- CLAVE DE MEMORIA ---
    # T4:Titulo||KW:palabra1|palabra2||DEF:def1|def2
    clave_memoria = f"T4:{'|'.join(sorted(palabras_txt))}||DEF:{'|'.join(sorted(definiciones_txt))}"
    
    # --- RESOLUCIÓN ---
    # 1. MEMORIA
    solucion_ordenada = mem.buscar(clave_memoria)
    
    # 2. IA
    if not solucion_ordenada:
        print("      🧠 Consultando IA para emparejar...")
        pares = ia_utils.obtener_emparejamientos(palabras_txt, definiciones_txt)
        if pares:
            # Convertimos dict a lista ordenada según el orden visual de las palabras
            solucion_ordenada = []
            for p in palabras_txt:
                if p in pares: solucion_ordenada.append(pares[p])
            
            if len(solucion_ordenada) == len(palabras_txt):
                mem.registrar(clave_memoria, solucion_ordenada)
    else:
        # Si es lista de listas (formato antiguo), tomamos la primera
        if isinstance(solucion_ordenada, list) and solucion_ordenada and isinstance(solucion_ordenada[0], list):
             solucion_ordenada = solucion_ordenada[0]
        print(f"      💾 Memoria: {len(solucion_ordenada)} pares recuperados.")

    # 3. CLICK
    if solucion_ordenada:
        for i, def_texto in enumerate(solucion_ordenada):
            elem = mapa_defs_elems.get(def_texto)
            if not elem: elem = mapa_defs_elems.get(def_texto.strip())
            
            if elem:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(0.3)
                    elem.click()
                    print(f"      ✅ Click {i+1}: {def_texto[:30]}...")
                    time.sleep(0.8) # Pausa necesaria entre clics
                except Exception as e:
                    print(f"      ❌ Error click: {e}")
            else:
                print(f"      ⚠️ No encuentro elemento para: {def_texto}")

    # --- RETORNO PARA APRENDIZAJE ---
    return {
        "clave": clave_memoria,
        "items": palabras_txt, # Las claves (izq)
        "extra": definiciones_txt # Los valores (der)
    }