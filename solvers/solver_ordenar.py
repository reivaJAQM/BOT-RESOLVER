from selenium.webdriver.common.by import By
import time
import copy
import bot_memory as mem

def resolver(driver, sel, ia_utils, contexto):
    """
    Resuelve TIPO 1: Ordenar frases (Drag & Drop con JS).
    """
    print("   🔍 [Solver Ordenar] Analizando contenedores Drag & Drop...")

    contenedores = driver.find_elements(*sel.SELECTOR_CONTENEDOR_ORDENAR)
    if not contenedores:
        print("      ❌ No se encontraron contenedores de ordenar.")
        return

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

    # 2. Obtener Soluciones (Memoria o IA)
    for tarea in tareas_ordenar:
        frases_orig = tarea['frases']
        # Clave única: las frases ordenadas alfabéticamente para evitar duplicados por orden visual
        clave_memoria = "ORD:" + "|".join(sorted(frases_orig))
        
        orden_correcto = mem.buscar(clave_memoria)
        
        if not orden_correcto:
            print(f"      🧠 Consultando IA para ordenar {len(frases_orig)} elementos...")
            orden_correcto = ia_utils.obtener_orden_correcto(contexto, frases_orig)
            if orden_correcto:
                mem.registrar(clave_memoria, orden_correcto)
        else:
             if isinstance(orden_correcto, list) and isinstance(orden_correcto[0], list):
                 orden_correcto = orden_correcto[0] # Manejo de listas anidadas
             print(f"      💾 Memoria: {orden_correcto}")

        # 3. Ejecutar Movimiento (JavaScript)
        if orden_correcto:
            # Mapear el texto de la solución a los IDs reales del HTML
            ids_ordenados = []
            mapa_copia = copy.deepcopy(tarea['mapa_ids'])
            
            # Crear mapa inverso temporal para búsqueda rápida (texto -> [ids])
            texto_a_ids = {}
            for did, dtxt in mapa_copia.items():
                t_low = dtxt.lower().strip()
                if t_low not in texto_a_ids: texto_a_ids[t_low] = []
                texto_a_ids[t_low].append(did)

            fallo_mapeo = False
            for frase_sol in orden_correcto:
                f_low = str(frase_sol).lower().strip()
                if f_low in texto_a_ids and texto_a_ids[f_low]:
                    ids_ordenados.append(texto_a_ids[f_low].pop(0))
                else:
                    print(f"      ❌ Error: No encontré ID para '{frase_sol}'")
                    fallo_mapeo = True; break
            
            if not fallo_mapeo:
                print(f"      ⚡ Reordenando con JS...")
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
                ids.forEach(function(id){
                    if(map[id]) c.appendChild(map[id]);
                });
                """
                driver.execute_script(js_script, tarea['contenedor'], ids_ordenados)
                time.sleep(0.5)