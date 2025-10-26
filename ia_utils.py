# ia_utils.py
# Contiene toda la lógica para comunicarse con la API de IA.
# ¡ACTUALIZADO CON MANEJO DE ERRORES GLOBAL!

import google.generativeai as genai
import ast
import json
import config # Importamos nuestro archivo de configuración

# --- Configuración de la IA ---
print("Configurando IA...");
model = None
try:
    genai.configure(api_key=config.GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash') 
    print("IA Lista!")
except Exception as e:
    print(f"Error config IA: {e}")
    # model se quedará como None si falla

# --- INICIO DEL NUEVO BLOQUE DE EXTRACCIÓN ROBUSTA ---
# Esta función reemplazará el código repetido en todas las funciones
def obtener_texto_de_respuesta(response):
    """
    Forma robusta de extraer texto de una respuesta de IA, 
    manejando bloques de seguridad y respuestas vacías.
    """
    try:
        # 1. Comprobar si la generación se detuvo correctamente
        if not response.candidates or response.candidates[0].finish_reason.name != "STOP":
            finish_reason = response.candidates[0].finish_reason.name if response.candidates else "NO_CANDIDATES"
            print(f"Error IA: API detuvo la generación. Razón: {finish_reason}")
            return None
        
        # 2. Intentar obtener el texto
        # El error 'Invalid operation' ocurre aquí si .text está vacío
        respuesta_texto = response.text.strip()
        
        if not respuesta_texto:
            print("Error IA: La IA devolvió una respuesta vacía (finish_reason: STOP).")
            return None
            
        return respuesta_texto
        
    except (AttributeError, ValueError, IndexError, Exception) as e:
        # Captura el error "Invalid operation..." y otros
        print(f"Error IA: No se pudo extraer texto de la respuesta. {e}")
        # Imprime la respuesta completa para depurar si es necesario
        # print(f"Respuesta completa (para depurar): {response}") 
        return None
# --- FIN DEL NUEVO BLOQUE DE EXTRACCIÓN ROBUSTA ---


# --- Funciones de IA (Actualizadas) ---

def obtener_respuesta_opcion_multiple(contexto, pregunta, opciones):
    opciones_texto = "\n".join(f"- {opcion}" for opcion in opciones)
    prompt = f"Rol: Experto en tests de lectura.\nAnaliza contexto, pregunta, opciones. Responde SÓLO texto exacto opción correcta.\n---\n[Contexto]\n{contexto}\n\n[Pregunta]\n{pregunta}\n\n[Opciones]\n{opciones_texto}\n---\nRespuesta Correcta:"
    try:
        response = model.generate_content(prompt)
        # --- CORRECCIÓN GLOBAL ---
        respuesta_limpia = obtener_texto_de_respuesta(response)
        if respuesta_limpia is None: return None
        # --- FIN CORRECCIÓN ---

        respuesta_limpia = respuesta_limpia.strip('"\'., ') # Limpieza extra
        if respuesta_limpia in opciones: return respuesta_limpia
        
        print(f"Alerta IA: '{respuesta_limpia}' no exacto. Buscando parecido."); 
        respuesta_ia_lower = respuesta_limpia.lower()
        for op in opciones:
            op_limpia_lower = op.strip('"\'., ').lower() 
            if respuesta_ia_lower == op_limpia_lower:
                print(f"Coincidencia normalizada: '{op}'")
                return op
        
        print("No coincidencia."); return None
    except Exception as e: print(f"Error API (OM): {e}"); return None

def obtener_orden_correcto(contexto, frases):
    frases_texto = "\n".join(f'- "{f}"' for f in frases)
    prompt = f'Rol: Experto en ordenar eventos.\nAnaliza contexto, ordena frases. Responde SÓLO lista Python frases ordenadas (texto exacto).\n---\n[Contexto]\n{contexto}\n\n[Frases desordenadas]\n{frases_texto}\n---\nLista Ordenada:'
    try:
        response = model.generate_content(prompt)
        # --- CORRECCIÓN GLOBAL ---
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None
        # --- FIN CORRECCIÓN ---

        if respuesta_texto.startswith("```python"): respuesta_texto = respuesta_texto[9:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        
        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"): print(f"IA (Ord) no es lista: {respuesta_texto}"); return None
        lista_ordenada = ast.literal_eval(respuesta_texto)
        if isinstance(lista_ordenada, list) and len(lista_ordenada) == len(frases) and all(f in lista_ordenada for f in frases): return lista_ordenada
        else: print(f"IA (Ord) inválida o incompleta."); return None
    except (SyntaxError, ValueError) as e: print(f"Error parse IA (Ord): {e}\nResp: {respuesta_texto}"); return None
    except Exception as e: print(f"Error API (Ord): {e}"); return None

def obtener_palabra_correcta(contexto, frase_incompleta, opciones_palabra):
    opciones_texto = ", ".join(f'"{op}"' for op in opciones_palabra)
    frase_placeholder = frase_incompleta.replace("___", "[PALABRA_FALTANTE]")
    prompt = f"Rol: Experto en completar frases.\nAnaliza contexto/frase. Elige palabra de [Opciones] para [PALABRA_FALTANTE]. Responde SÓLO palabra correcta.\n---\n[Contexto]\n{contexto}\n\n[Frase Incompleta]\n{frase_placeholder}\n\n[Opciones de Palabra]\n{opciones_texto}\n---\nPalabra Correcta:"
    try:
        response = model.generate_content(prompt)
        # --- CORRECCIÓN GLOBAL ---
        respuesta_limpia = obtener_texto_de_respuesta(response)
        if respuesta_limpia is None: return None
        # --- FIN CORRECCIÓN ---
        
        respuesta_limpia = respuesta_limpia.strip('"\'., ')
        if respuesta_limpia in opciones_palabra: return respuesta_limpia
        else:
            resp_lower = respuesta_limpia.lower()
            for op in opciones_palabra:
                if op.strip('"\'., ').lower() == resp_lower: 
                    print(f"Alerta IA (Comp): Coincidencia sin mayús: '{op}'"); return op
            print(f"Error IA (Comp): '{respuesta_limpia}' no en {opciones_palabra}"); return None
    except Exception as e: print(f"Error API (Comp): {e}"); return None

def obtener_true_false(contexto, afirmacion):
    prompt = f"Rol: Experto en evaluar Verdadero (True) o Falso (False).\nAnaliza contexto, determina si afirmación es T/F. Responde SÓLO 'True' o 'False'.\n---\n[Contexto]\n{contexto}\n\n[Afirmación]\n{afirmacion}\n---\nRespuesta (True o False):"
    try:
        response = model.generate_content(prompt)
        # --- CORRECCIÓN GLOBAL ---
        respuesta_limpia = obtener_texto_de_respuesta(response)
        if respuesta_limpia is None: return None
        # --- FIN CORRECCIÓN ---

        respuesta_limpia = respuesta_limpia.strip().capitalize()
        if respuesta_limpia == "True" or respuesta_limpia == "False": return respuesta_limpia
        else:
            if "true" in respuesta_limpia.lower(): return "True"
            if "false" in respuesta_limpia.lower(): return "False"
            print(f"Error IA (T/F): No es True/False: '{respuesta_limpia}'"); return None
    except Exception as e: print(f"Error API IA (T/F): {e}"); return None

def obtener_emparejamientos(palabras, definiciones):
    palabras_texto = "\n".join(f"- {p}" for p in palabras)
    definiciones_texto = "\n".join(f'- "{d}"' for d in definiciones)
    prompt = f"""
Rol: Experto en emparejamientos.
Analiza [Lista_Clave] (los destinos fijos) y [Lista_Opciones] (las opciones movibles).
Determina qué Opción corresponde a cada Clave.
Responde SÓLO con un diccionario Python {{clave_exacta: opcion_correcta_exacta}}.
---
[Lista_Clave]
{palabras_texto}
[Lista_Opciones]
{definiciones_texto}
---
Diccionario de Pares ({{clave: opcion}}):
"""
    try:
        response = model.generate_content(prompt)
        # --- CORRECCIÓN GLOBAL ---
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None
        # --- FIN CORRECCIÓN ---
        
        if respuesta_texto.startswith("```python"): respuesta_texto = respuesta_texto[9:]
        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("{") or not respuesta_texto.endswith("}"): print(f"IA (Emp) no es dicc: {respuesta_texto}"); return None
        pares = json.loads(respuesta_texto)
        if (isinstance(pares, dict) and 
            len(pares) == len(palabras) and 
            all(p in pares for p in palabras) and 
            all(d in definiciones for d in pares.values())): 
            return pares
        else: 
            print(f"IA (Emp) inválido o incompleto. Resp: {respuesta_texto}"); 
            return None
    except json.JSONDecodeError as e: print(f"Error parse JSON IA (Emp): {e}\nResp: {respuesta_texto}"); return None
    except Exception as e: print(f"Error API IA (Emp): {e}"); return None

def obtener_true_false_lote(contexto, afirmaciones_lista):
    print(f"IA (T/F Lote): Enviando {len(afirmaciones_lista)} afirmaciones...")
    afirmaciones_texto = "\n".join(f'- "{a}"' for a in afirmaciones_lista)
    prompt = f"""
Rol: Experto en evaluar Verdadero (True) o Falso (False).
Analiza el [Contexto] y la [Lista de Afirmaciones].
Responde SÓLO con una lista JSON de strings, donde cada string es 'True' o 'False', correspondiendo en orden a cada afirmación de la lista.
Ejemplo de respuesta: ["True", "False", "True"]
---
[Contexto]
{contexto}
[Lista de Afirmaciones]
{afirmaciones_texto}
---
Respuesta (Sólo la lista JSON):
"""
    try:
        response = model.generate_content(prompt)
        # --- CORRECCIÓN GLOBAL ---
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None
        # --- FIN CORRECCIÓN ---
        
        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            print(f"Error IA (T/F Lote): Respuesta no es una lista: {respuesta_texto}")
            return None
        lista_respuestas = json.loads(respuesta_texto)
        if isinstance(lista_respuestas, list) and len(lista_respuestas) == len(afirmaciones_lista):
            respuestas_normalizadas = []
            for r in lista_respuestas:
                if str(r).strip().capitalize() == "True":
                    respuestas_normalizadas.append("True")
                elif str(r).strip().capitalize() == "False":
                    respuestas_normalizadas.append("False")
                else:
                    print(f"Error IA (T/F Lote): Respuesta inválida '{r}' en la lista.")
                    return None
            print(f"IA (T/F Lote): Recibidas {len(respuestas_normalizadas)} respuestas.")
            return respuestas_normalizadas
        else:
            print("Error IA (T/F Lote): La lista no coincide en tamaño.")
            return None
    except json.JSONDecodeError as e:
        print(f"Error parse JSON IA (T/F Lote): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        print(f"Error API IA (T/F Lote): {e}")
        return None

def obtener_palabras_correctas_lote(contexto, tareas_lista):
    print(f"IA (Comp Lote): Enviando {len(tareas_lista)} frases para completar...")
    tareas_texto = ""
    for i, tarea in enumerate(tareas_lista):
        opciones_str = ", ".join(f'"{op}"' for op in tarea['opciones'])
        tareas_texto += f"Tarea {i+1}:\n"
        tareas_texto += f"  Frase: \"{tarea['frase']}\"\n"
        tareas_texto += f"  Opciones: [{opciones_str}]\n\n"
    prompt = f"""
Rol: Experto en completar frases.
Analiza el [Contexto] y cada [Tarea] en la lista.
Para cada Tarea, elige la palabra correcta de sus [Opciones] para rellenar el espacio '___'.
Responde SÓLO con una lista JSON de strings, donde cada string es la palabra correcta, correspondiendo en orden a cada tarea.
Ejemplo de respuesta: ["palabra_tarea_1", "palabra_tarea_2"]
---
[Contexto]
{contexto}
[Lista de Tareas]
{tareas_texto}
---
Respuesta (Sólo la lista JSON de palabras correctas):
"""
    try:
        response = model.generate_content(prompt)
        # --- CORRECCIÓN GLOBAL ---
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None
        # --- FIN CORRECCIÓN ---
        
        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            print(f"Error IA (Comp Lote): Respuesta no es una lista: {respuesta_texto}")
            return None
        lista_respuestas = json.loads(respuesta_texto)
        if isinstance(lista_respuestas, list) and len(lista_respuestas) == len(tareas_lista):
            respuestas_verificadas = []
            for i, palabra_ia in enumerate(lista_respuestas):
                opciones_tarea = tareas_lista[i]['opciones']
                palabra_ia_limpia = str(palabra_ia).strip().strip('"\'., ')
                if palabra_ia_limpia in opciones_tarea:
                    respuestas_verificadas.append(palabra_ia_limpia)
                else:
                    resp_lower = palabra_ia_limpia.lower()
                    encontrado = False
                    for op in opciones_tarea:
                        if op.strip('"\'., ').lower() == resp_lower:
                            respuestas_verificadas.append(op)
                            encontrado = True
                            break
                    if not encontrado:
                        print(f"Error IA (Comp Lote): Tarea {i+1} - '{palabra_ia_limpia}' no en {opciones_tarea}")
                        return None
            print(f"IA (Comp Lote): Recibidas {len(respuestas_verificadas)} respuestas verificadas.")
            return respuestas_verificadas
        else:
            print("Error IA (Comp Lote): La lista no coincide en tamaño.")
            return None
    except json.JSONDecodeError as e:
        print(f"Error parse JSON IA (Comp Lote): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        print(f"Error API IA (Comp Lote): {e}")
        return None

def obtener_numeros_parrafo_lote(contexto, ideas_lista, respuesta_anterior_incorrecta=None):
    print(f"IA (Parag Lote): Enviando {len(ideas_lista)} ideas...")
    ideas_texto = "\n".join(f'- "{idea}"' for idea in ideas_lista)
    seccion_intento_anterior = ""
    if respuesta_anterior_incorrecta:
        respuesta_anterior_str = ", ".join(f'"{r}"' for r in respuesta_anterior_incorrecta)
        seccion_intento_anterior = f"""
[Intento Anterior Incorrecto]
Tu respuesta anterior fue: [{respuesta_anterior_str}]
Esa combinación fue incorrecta. Por favor, analiza el texto de nuevo y proporciona una combinación DIFERENTE.
"""
    prompt = f"""
Rol: Experto en comprensión lectora.
Analiza el [Contexto], que está dividido en párrafos numerados (ej. (1), (2), (3)).
Lee cada [Idea] en la lista y determina a qué número de párrafo (1, 2, 3, etc.) corresponde.
Responde SÓLO con una lista JSON de strings, donde cada string es el NÚMERO del párrafo correcto (ej. "1", "3", "2").
{seccion_intento_anterior}
Ejemplo de respuesta: ["2", "3", "1"]
---
[Contexto]
{contexto}
[Lista de Ideas]
{ideas_texto}
---
Respuesta (Sólo la lista JSON de números como strings):
"""
    try:
        response = model.generate_content(prompt)
        # --- CORRECCIÓN GLOBAL ---
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None
        # --- FIN CORRECCIÓN ---

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            print(f"Error IA (Parag Lote): Respuesta no es una lista: {respuesta_texto}")
            return None
        lista_respuestas_num = json.loads(respuesta_texto)
        if isinstance(lista_respuestas_num, list) and len(lista_respuestas_num) == len(ideas_lista):
            respuestas_verificadas = [str(n).strip() for n in lista_respuestas_num]
            print(f"IA (Parag Lote): Recibidas {len(respuestas_verificadas)} respuestas.")
            return respuestas_verificadas
        else:
            print("Error IA (Parag Lote): La lista no coincide en tamaño.")
            return None
    except json.JSONDecodeError as e:
        print(f"Error parse JSON IA (Parag Lote): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        print(f"Error API IA (Parag Lote): {e}")
        return None

def extraer_solucion_del_error(texto_error_modal, preguntas_lista):
    print(f"IA (Aprendizaje): Analizando texto de error para extraer solución...")
    preguntas_str = ", ".join(f'"{p}"' for p in preguntas_lista)
    prompt = f"""
Rol: Experto en extracción de datos (Data Scraper).
Analiza el [Texto de Error] de un pop-up. Este texto contiene la solución correcta.
Las preguntas que se hicieron fueron: {preguntas_str}.
Tu tarea es devolver SÓLO un diccionario Python que mapee CADA pregunta de la lista a su respuesta correcta (el número o texto).
[Texto de Error]:
"{texto_error_modal}"
---
Diccionario de Solución ({{pregunta: respuesta}}):
"""
    try:
        response = model.generate_content(prompt)
        # --- CORRECCIÓN GLOBAL ---
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None
        # --- FIN CORRECCIÓN ---

        if respuesta_texto.startswith("```python"): respuesta_texto = respuesta_texto[9:]
        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("{") or not respuesta_texto.endswith("}"):
            print(f"IA (Aprendizaje) no es dicc: {respuesta_texto}"); return None
        solucion_dict = json.loads(respuesta_texto)
        if isinstance(solucion_dict, dict) and all(key in preguntas_lista for key in solucion_dict.keys()):
            print(f"IA (Aprendizaje) extrajo: {solucion_dict}")
            return solucion_dict
        else:
            print(f"IA (Aprendizaje) inválido o incompleto: {solucion_dict}"); return None
    except json.JSONDecodeError as e:
        print(f"Error parse JSON IA (Aprendizaje): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        print(f"Error API IA (Aprendizaje): {e}"); return None

def obtener_respuestas_om_lote(contexto, tareas_lista, respuesta_anterior_incorrecta=None):
    print(f"IA (OM Lote): Enviando {len(tareas_lista)} preguntas...")
    tareas_texto = ""
    for i, tarea in enumerate(tareas_lista):
        opciones_str = ", ".join(f'"{op}"' for op in tarea['opciones'])
        tareas_texto += f"Tarea {i+1}:\n"
        tareas_texto += f"  Pregunta: \"{tarea['pregunta']}\"\n"
        tareas_texto += f"  Opciones: [{opciones_str}]\n\n"
    seccion_intento_anterior = ""
    if respuesta_anterior_incorrecta:
        respuesta_anterior_str = ", ".join(f'"{r}"' for r in respuesta_anterior_incorrecta)
        seccion_intento_anterior = f"""
[Intento Anterior Incorrecto]
Tu respuesta anterior fue: [{respuesta_anterior_str}]
Esa combinación fue incorrecta. Por favor, analiza el texto de nuevo y proporciona una combinación DIFERENTE.
"""
    prompt = f"""
Rol: Experto en comprensión lectora.
Analiza el [Contexto] y cada [Tarea] en la lista.
Para cada Tarea, elige la opción correcta de sus [Opciones].
Responde SÓLO con una lista JSON de strings, donde cada string es la respuesta correcta, correspondiendo en orden a cada tarea.
{seccion_intento_anterior}
Ejemplo de respuesta: ["Respuesta_Tarea_1", "Respuesta_Tarea_2"]
---
[Contexto]
{contexto}
[Lista de Tareas]
{tareas_texto}
---
Respuesta (Sólo la lista JSON de respuestas correctas):
"""
    try:
        response = model.generate_content(prompt)
        # --- CORRECCIÓN GLOBAL ---
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None
        # --- FIN CORRECCIÓN ---

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            print(f"Error IA (OM Lote): Respuesta no es una lista: {respuesta_texto}")
            return None
        lista_respuestas = json.loads(respuesta_texto)
        if isinstance(lista_respuestas, list) and len(lista_respuestas) == len(tareas_lista):
            respuestas_verificadas = []
            for i, palabra_ia in enumerate(lista_respuestas):
                opciones_tarea_originales = tareas_lista[i]['opciones']
                palabra_ia_limpia = str(palabra_ia).strip().strip('"\'., ')
                
                # --- CORRECCIÓN DE COMPARACIÓN (PUNTO Y COMA) ---
                opciones_tarea_limpias = [str(op).strip().strip('"\'., ') for op in opciones_tarea_originales]
                if palabra_ia_limpia in opciones_tarea_limpias:
                    match_index = opciones_tarea_limpias.index(palabra_ia_limpia)
                    respuestas_verificadas.append(opciones_tarea_originales[match_index]) # Devolvemos la original
                    continue
                palabra_ia_lower = palabra_ia_limpia.lower()
                encontrado = False
                for j, op_limpia in enumerate(opciones_tarea_limpias):
                    if op_limpia.lower() == palabra_ia_lower:
                        respuestas_verificadas.append(opciones_tarea_originales[j])
                        encontrado = True
                        break
                if not encontrado:
                    print(f"Error IA (OM Lote): Tarea {i+1} - '{palabra_ia_limpia}' no está en opciones {opciones_tarea_originales}")
                    return None
                # --- FIN CORRECCIÓN DE COMPARACIÓN ---
            
            print(f"IA (OM Lote): Recibidas {len(respuestas_verificadas)} respuestas verificadas.")
            return respuestas_verificadas
        else:
            print("Error IA (OM Lote): La lista no coincide en tamaño.")
            return None
    except json.JSONDecodeError as e:
        print(f"Error parse JSON IA (OM Lote): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        print(f"Error API IA (OM Lote): {e}")
        return None

def extraer_solucion_simple(texto_error_modal, opciones_lista):
    """
    Lee el texto de un modal de error y extrae la ÚNICA respuesta correcta.
    'opciones_lista' son las opciones que se mostraron (ej. ["True", "False"] or ["A", "B", "C"])
    Retorna un string con la respuesta correcta.
    """
    print(f"IA (Aprendizaje Simple): Analizando texto de error...")
    opciones_str = ", ".join(f'"{op}"' for op in opciones_lista)
    
    prompt = f"""
Rol: Experto en extracción de datos.
Analiza el [Texto de Error] de un pop-up. Este texto contiene la solución correcta.
Las opciones que se mostraron al usuario fueron: {opciones_str}.
Tu tarea es devolver SÓLO un string con la opción correcta que esté en esa lista.

[Texto de Error]:
"{texto_error_modal}"

---
Respuesta Correcta (Sólo el string de la opción):
"""
    try:
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response) # Usamos el extractor robusto
        if respuesta_texto is None: return None

        respuesta_limpia = respuesta_texto.strip('"\'., ')
        
        # 1. Validar que la respuesta esté en las opciones (limpio vs original)
        if respuesta_limpia in opciones_lista:
            print(f"IA (Aprendizaje Simple) extrajo: '{respuesta_limpia}'")
            return respuesta_limpia
        
        # 2. Validar sin mayúsculas/puntos (limpio-lower vs limpio-lower)
        resp_limpia_lower = respuesta_limpia.lower()
        for op in opciones_lista:
            if op.strip('"\'., ').lower() == resp_limpia_lower:
                print(f"IA (Aprendizaje Simple) extrajo (match normalizado): '{op}'")
                return op # Devolvemos la opción original

        print(f"IA (Aprendizaje Simple) falló. Respuesta '{respuesta_limpia}' no en {opciones_lista}")
        return None
            
    except Exception as e:
        print(f"Error API IA (Aprendizaje Simple): {e}"); return None
    
def extraer_solucion_lote_tf(texto_error_modal, afirmaciones_lista):
    """
    Lee el texto de un modal de error para T/F Múltiple y extrae la secuencia correcta.
    'afirmaciones_lista' es la lista de textos de las afirmaciones.
    Retorna una lista de strings: ["True", "False", "True", ...]
    """
    print(f"IA (Aprendizaje Lote T/F): Analizando texto de error...")
    num_afirmaciones = len(afirmaciones_lista)
    
    prompt = f"""
Rol: Experto en extracción de datos.
Analiza el [Texto de Error] de un pop-up de una pregunta de Verdadero/Falso múltiple.
Este texto indica la secuencia correcta de respuestas para {num_afirmaciones} afirmaciones.
Las afirmaciones originales fueron (en orden):
{chr(10).join(f'- "{a}"' for a in afirmaciones_lista)}

Tu tarea es devolver SÓLO una lista JSON de strings, donde cada string es "True" o "False", representando la secuencia correcta. La lista debe tener exactamente {num_afirmaciones} elementos.

[Texto de Error]:
"{texto_error_modal}"

---
Respuesta (Sólo la lista JSON ["True", "False", ...]):
"""
    try:
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response) # Usamos el extractor robusto
        if respuesta_texto is None: return None

        # Limpieza adicional por si acaso
        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            print(f"IA (Aprendizaje Lote T/F) no es lista: {respuesta_texto}"); return None
        
        solucion_lista = json.loads(respuesta_texto)
        
        # Verificamos longitud y contenido
        if isinstance(solucion_lista, list) and len(solucion_lista) == num_afirmaciones:
            respuestas_normalizadas = []
            for r in solucion_lista:
                r_norm = str(r).strip().capitalize()
                if r_norm == "True" or r_norm == "False":
                    respuestas_normalizadas.append(r_norm)
                else:
                    print(f"IA (Aprendizaje Lote T/F) respuesta inválida '{r}'"); return None
            
            print(f"IA (Aprendizaje Lote T/F) extrajo: {respuestas_normalizadas}")
            return respuestas_normalizadas
        else:
            print(f"IA (Aprendizaje Lote T/F) inválido o incompleto: {solucion_lista}"); return None
            
    except json.JSONDecodeError as e:
        print(f"Error parse JSON IA (Aprendizaje Lote T/F): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        print(f"Error API IA (Aprendizaje Lote T/F): {e}"); return None
    
def extraer_solucion_ordenar(texto_error_modal, frases_desordenadas):
    """
    Lee el texto de un modal de error para TIPO 1 (Ordenar) y extrae la secuencia correcta.
    'frases_desordenadas' es la lista de frases que se mostraron.
    Retorna una lista de strings: ["Frase1", "Frase2", ...]
    """
    print(f"IA (Aprendizaje Ordenar): Analizando texto de error...")
    num_frases = len(frases_desordenadas)
    frases_str = ", ".join(f'"{f}"' for f in frases_desordenadas)
    
    prompt = f"""
Rol: Experto en extracción de datos.
Analiza el [Texto de Error] de un pop-up de una pregunta de ordenar.
Este texto contiene la secuencia correcta para {num_frases} frases/palabras.
Las frases originales desordenadas eran: {frases_str}.

Tu tarea es devolver SÓLO una lista JSON de strings, donde cada string es la palabra/frase en el ORDEN CORRECTO.
La lista debe tener exactamente {num_frases} elementos y usar el texto exacto de las frases originales.

[Texto de Error]:
"{texto_error_modal}"

---
Respuesta (Sólo la lista JSON ["palabra_1", "palabra_2", ...]):
"""
    try:
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response) # Usamos el extractor robusto
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            print(f"IA (Aprendizaje Ordenar) no es lista: {respuesta_texto}"); return None
        
        solucion_lista = json.loads(respuesta_texto)
        
        # Verificamos longitud y contenido
        if (isinstance(solucion_lista, list) and 
            len(solucion_lista) == num_frases and 
            all(f in frases_desordenadas for f in solucion_lista)): # Comprueba que todas las frases extraídas estuvieran en las originales
            
            print(f"IA (Aprendizaje Ordenar) extrajo: {solucion_lista}")
            return solucion_lista
        else:
            print(f"IA (Aprendizaje Ordenar) inválido, incompleto o no coincide con frases original. Resp: {solucion_lista}"); return None
            
    except json.JSONDecodeError as e:
        print(f"Error parse JSON IA (Aprendizaje Ordenar): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        print(f"Error API IA (Aprendizaje Ordenar): {e}"); return None

def extraer_solucion_emparejar(texto_error_modal, claves_lista, definiciones_lista):
    """
    Lee el texto de un modal de error para TIPO 4/8 (Emparejar) y extrae los pares correctos.
    'claves_lista' son las claves (palabras <h2> o IDs de imagen 'alt'/'src')
    'definiciones_lista' son las opciones (los spans azules)
    Retorna un diccionario: {clave: definicion_correcta}
    """
    print(f"IA (Aprendizaje Emparejar): Analizando texto de error...")
    claves_str = ", ".join(f'"{c}"' for c in claves_lista)
    defs_str = ", ".join(f'"{d}"' for d in definiciones_lista)
    
    prompt = f"""
Rol: Experto en extracción de datos.
Analiza el [Texto de Error] de un pop-up. Este texto contiene la solución correcta para un ejercicio de emparejamiento.

Las [Claves] (los elementos de la izquierda) eran: {claves_str}
Las [Opciones] (los elementos de la derecha) eran: {defs_str}

Tu tarea es devolver SÓLO un diccionario JSON que mapee CADA clave de la [Claves] a su opción correcta de [Opciones], basándote en la solución del [Texto de Error].

[Texto de Error]:
"{texto_error_modal}"

---
Diccionario de Solución ({{clave: opcion}}):
"""
    try:
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response) # Usamos el extractor robusto
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("{") or not respuesta_texto.endswith("}"):
            print(f"IA (Aprendizaje Emparejar) no es dicc: {respuesta_texto}"); return None
        
        solucion_dict = json.loads(respuesta_texto)
        
        # Verificamos validez
        if (isinstance(solucion_dict, dict) and 
            len(solucion_dict) == len(claves_lista) and 
            all(c in solucion_dict for c in claves_lista) and 
            all(d in definiciones_lista for d in solucion_dict.values())): 
            
            print(f"IA (Aprendizaje Emparejar) extrajo: {solucion_dict}")
            return solucion_dict
        else:
            # A veces la IA devuelve el GUID con/sin espacio
            claves_lista_alt = [c + " " for c in claves_lista] + [c.strip() for c in claves_lista]
            if (isinstance(solucion_dict, dict) and 
                len(solucion_dict) == len(claves_lista) and 
                all(d in definiciones_lista for d in solucion_dict.values())):
                print(f"IA (Aprendizaje Emparejar) [WARN]: Las claves no coincidían exacto, pero se validó el formato. {solucion_dict}")
                return solucion_dict

            print(f"IA (Aprendizaje Emparejar) inválido o incompleto: {solucion_dict}"); return None
            
    except json.JSONDecodeError as e:
        print(f"Error parse JSON IA (Aprendizaje Emparejar): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        print(f"Error API IA (Aprendizaje Emparejar): {e}"); return None
    
def extraer_solucion_lote_completar(texto_error_modal, tareas_lista):
    """
    Lee el texto de un modal de error para TIPO 2 (Completar Lote) y extrae la secuencia correcta.
    'tareas_lista' es la lista de tareas: [{"frase": "...", "opciones": [...]}, ...]
    Retorna una lista de strings: ["respuesta_1", "respuesta_2", ...]
    """
    print(f"IA (Aprendizaje Lote Completar): Analizando texto de error...")
    
    tareas_str = ""
    for i, tarea in enumerate(tareas_lista):
        opciones_str = ", ".join(f'"{op}"' for op in tarea['opciones'])
        tareas_str += f"Tarea {i+1} (Frase: \"{tarea['frase']}\") - Opciones: [{opciones_str}]\n"
    
    prompt = f"""
Rol: Experto en extracción de datos.
Analiza el [Texto de Error] de un pop-up. Este texto contiene la solución correcta para un ejercicio de completar frases.
Las tareas originales (en orden) y sus opciones eran:
{tareas_str}

Tu tarea es devolver SÓLO una lista JSON de strings, donde cada string es la opción correcta para cada tarea, en el orden correcto.

[Texto de Error]:
"{texto_error_modal}"

---
Respuesta (Sólo la lista JSON ["opcion_correcta_1", "opcion_correcta_2", ...]):
"""
    try:
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response) # Usamos el extractor robusto
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            print(f"IA (Aprendizaje Lote Completar) no es lista: {respuesta_texto}"); return None
        
        solucion_lista = json.loads(respuesta_texto)
        
        # Verificamos longitud
        if isinstance(solucion_lista, list) and len(solucion_lista) == len(tareas_lista):
            # Verificamos que cada respuesta esté en sus opciones
            respuestas_verificadas = []
            for i, respuesta_ia in enumerate(solucion_lista):
                opciones_originales = tareas_lista[i]['opciones']
                respuesta_ia_limpia = str(respuesta_ia).strip().strip('"\'., ')
                
                if respuesta_ia_limpia in opciones_originales:
                    respuestas_verificadas.append(respuesta_ia_limpia)
                else:
                    # Intento de match normalizado
                    resp_lower = respuesta_ia_limpia.lower()
                    encontrado = False
                    for op in opciones_originales:
                        if op.strip('"\'., ').lower() == resp_lower:
                            respuestas_verificadas.append(op) # Guardamos la original
                            encontrado = True; break
                    if not encontrado:
                        print(f"IA (Aprendizaje Lote Completar) Tarea {i+1}: '{respuesta_ia}' no en {opciones_originales}"); return None
            
            print(f"IA (Aprendizaje Lote Completar) extrajo: {respuestas_verificadas}")
            return respuestas_verificadas
        else:
            print(f"IA (Aprendizaje Lote Completar) inválido o incompleto: {solucion_lista}"); return None
            
    except json.JSONDecodeError as e:
        print(f"Error parse JSON IA (Aprendizaje Lote Completar): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        print(f"Error API IA (Aprendizaje Lote Completar): {e}"); return None