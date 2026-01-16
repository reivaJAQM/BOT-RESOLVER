from selenium.webdriver.common.by import By
import time
import bot_memory as mem

def resolver(driver, sel, ia_utils, contexto):
    """
    Resuelve TIPO 4: Emparejar definiciones (Click izquierdo -> Click derecho).
    """
    print("   🔍 [Solver Match] Analizando columnas de emparejamiento...")
    
    # 1. Extraer Definiciones (Columna derecha - Azul)
    # Usamos JS para obtener texto limpio rápido
    js_defs = f"return Array.from(document.querySelectorAll('{sel.SELECTOR_DEFINICIONES_AZULES_CSS}')).map(e => e.innerText.trim());"
    definiciones_txt = driver.execute_script(js_defs)
    definiciones_txt = [d for d in definiciones_txt if d]
    
    if not definiciones_txt:
        print("      ❌ No se encontraron definiciones (columna derecha).")
        return

    # Mapear texto a elemento web para poder hacer click luego
    elems_def = driver.find_elements(*sel.SELECTOR_DEFINICIONES_AZULES_XPATH)
    mapa_defs_elems = {e.text.strip(): e for e in elems_def if e.text.strip()}

    # 2. Extraer Palabras Clave (Columna izquierda)
    js_kws = "return Array.from(document.querySelectorAll('h2.text-gray-800.text-base')).map(e => e.innerText.trim());"
    palabras_txt = driver.execute_script(js_kws)
    palabras_txt = [p for p in palabras_txt if p]

    print(f"      Encontradas: {len(palabras_txt)} palabras y {len(definiciones_txt)} definiciones.")

    # 3. Consultar Solución
    # Clave compuesta para memoria
    clave_memoria = f"T4:{'|'.join(sorted(palabras_txt))}||DEF:{'|'.join(sorted(definiciones_txt))}"
    
    solucion_ordenada = mem.buscar(clave_memoria)
    
    if not solucion_ordenada:
        print("      🧠 Consultando IA para emparejar...")
        # IA devuelve dict {Palabra: Definicion}
        pares = ia_utils.obtener_emparejamientos(palabras_txt, definiciones_txt)
        if pares:
            # Convertimos el dict a una lista ordenada de definiciones según el orden visual de las palabras
            solucion_ordenada = []
            for p in palabras_txt:
                if p in pares: solucion_ordenada.append(pares[p])
            
            if len(solucion_ordenada) == len(palabras_txt):
                mem.registrar(clave_memoria, solucion_ordenada)
    else:
        if isinstance(solucion_ordenada, list) and isinstance(solucion_ordenada[0], list):
             solucion_ordenada = solucion_ordenada[0]
        print(f"      💾 Memoria: {len(solucion_ordenada)} pares recuperados.")

    # 4. Ejecutar Clics
    if solucion_ordenada:
        for i, def_texto in enumerate(solucion_ordenada):
            if def_texto in mapa_defs_elems:
                elem = mapa_defs_elems[def_texto]
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(0.2)
                    elem.click()
                    print(f"      ✅ Click {i+1}: {def_texto[:30]}...")
                    time.sleep(0.8) # Pausa necesaria entre clics para que la web procese
                except Exception as e:
                    print(f"      ❌ Error click: {e}")
            else:
                print(f"      ⚠️ No encuentro elemento para: {def_texto}")