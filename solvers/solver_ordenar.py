from selenium.webdriver.common.by import By
import time
import copy
import bot_memory as mem

def resolver(driver, sel, ia_utils, contexto):
    """
    Resuelve TIPO 1: Ordenar frases (Drag & Drop con JS).
    Retorna datos para aprendizaje.
    """
    print("   🔍 [Solver Ordenar] Analizando contenedores Drag & Drop...")

    contenedores = driver.find_elements(*sel.SELECTOR_CONTENEDOR_ORDENAR)
    if not contenedores:
        print("      ❌ No se encontraron contenedores de ordenar.")
        return None

    tareas_ordenar = []
    
    # 1. Recolectar frases desordenadas
    for k, contenedor in enumerate(contenedores):
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", contenedor)
        cajas = contenedor.find_elements(*sel.SELECTOR_CAJAS_ORDENAR)
        
        frases_ids = {} # Mapa {id_draggable: texto}
        frases_lista = []
        
        for c in cajas:
            try:
                txt = c.find_element(*sel.SELECTOR_TEXTO_CAJA_ORDENAR).text.strip()
                d_id = c.get_attribute("data-rbd-draggable-id")
                if txt and d_id:
                    frases_ids[d_id] = txt
                    frases_lista.append(txt)
            except: pass
            
        if frases_lista:
            tareas_ordenar.append({
                "id": k, 
                "contenedor": contenedor,
                "frases": frases_lista,
                "mapa_ids": frases_ids
            })
            print(f"      Tarea {k+1}: {frases_lista}")

    if not tareas_ordenar: return None

    # --- CLAVE DE MEMORIA ---
    claves_ind = []
    for t in tareas_ordenar:
        # Ordenamos alfabéticamente para crear una firma única independiente del orden visual
        claves_ind.append("|".join(sorted(t['frases'])))
    clave_memoria = "ORD:" + "||".join(claves_ind)

    # --- RESOLUCIÓN ---
    # 1. MEMORIA
    orden_correcto_lote = mem.buscar(clave_memoria)
    
    # 2. IA (Si no hay memoria)
    if not orden_correcto_lote:
        print(f"      🧠 Consultando IA...")
        # La IA debe devolver una lista de listas (un orden para cada tarea)
        orden_correcto_lote = []
        for t in tareas_ordenar:
            orden = ia_utils.obtener_orden_correcto(contexto, t['frases'])
            if orden: orden_correcto_lote.append(orden)
        
        if len(orden_correcto_lote) == len(tareas_ordenar):
            mem.registrar(clave_memoria, orden_correcto_lote)
    else:
        print(f"      💾 Memoria: {orden_correcto_lote}")

    # 3. EJECUTAR MOVIMIENTO (JS)
    if orden_correcto_lote and len(orden_correcto_lote) == len(tareas_ordenar):
        for i, tarea in enumerate(tareas_ordenar):
            orden_objetivo = orden_correcto_lote[i]
            
            # Mapear texto -> IDs
            ids_ordenados = []
            mapa_copia = copy.deepcopy(tarea['mapa_ids'])
            
            # Crear mapa inverso temporal (texto -> [ids])
            texto_a_ids = {}
            for did, dtxt in mapa_copia.items():
                t_low = dtxt.lower().strip()
                if t_low not in texto_a_ids: texto_a_ids[t_low] = []
                texto_a_ids[t_low].append(did)

            fallo_mapeo = False
            for frase_sol in orden_objetivo:
                f_low = str(frase_sol).lower().strip()
                if f_low in texto_a_ids and texto_a_ids[f_low]:
                    ids_ordenados.append(texto_a_ids[f_low].pop(0))
                else:
                    print(f"      ❌ Error: No encontré ID para '{frase_sol}'")
                    fallo_mapeo = True; break
            
            if not fallo_mapeo:
                print(f"      ⚡ Reordenando con JS (Tarea {i+1})...")
                js_script = """
                var c = arguments[0];
                var ids = arguments[1];
                var map = {};
                for(var i=0; i<c.children.length; i++){
                    var child = c.children[i];
                    var draggable = child.querySelector('[data-rbd-draggable-id]');
                    if(draggable){
                        map[draggable.getAttribute('data-rbd-draggable-id')] = child;
                    }
                }
                while (c.firstChild) { c.removeChild(c.firstChild); }
                ids.forEach(function(id){
                    if(map[id]) c.appendChild(map[id]);
                });
                """ 
                driver.execute_script(js_script, tarea['contenedor'], ids_ordenados)
                time.sleep(0.5)

    # --- RETORNO PARA APRENDIZAJE ---
    return {
        "clave": clave_memoria,
        "items": [t['frases'] for t in tareas_ordenar] # Retornamos las frases originales
    }