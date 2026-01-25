# ia_utils.py
# Contiene toda la lógica para comunicarse con la API de IA.
# ¡ACTUALIZADO CON MANEJO DE ERRORES GLOBAL!
# ¡ACTUALIZADO CON VALIDACIÓN OM MEJORADA PARA PREFIJOS (a), 1.) + DEBUG!

import google.generativeai as genai
import ast
import json
import re # ¡NUEVO! Importar expresiones regulares
import config # Importamos nuestro archivo de configuración

# --- Configuración de la IA ---
print("Configurando IA...");
model = None
try:
    # Use 4 spaces for indentation
    genai.configure(api_key=config.GOOGLE_API_KEY)
    # --- ¡CAMBIO MODELO! Usaremos Flash para mejor velocidad/costo ---
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("IA Lista!")
except Exception as e:
    # Use 4 spaces for indentation
    print(f"Error config IA: {e}")
    # model se quedará como None si falla

# --- INICIO DEL NUEVO BLOQUE DE EXTRACCIÓN ROBUSTA ---
def obtener_texto_de_respuesta(response):
    """
    Forma robusta de extraer texto de una respuesta de IA,
    manejando bloques de seguridad y respuestas vacías.
    """
    try:
        # Use 8 spaces for indentation
        # 1. Comprobar si la generación se detuvo correctamente
        if not response.candidates or response.candidates[0].finish_reason.name != "STOP":
            # Use 12 spaces for indentation
            finish_reason = response.candidates[0].finish_reason.name if response.candidates else "NO_CANDIDATES"
            print(f"Error IA: API detuvo la generación. Razón: {finish_reason}")
            # Considerar imprimir response.prompt_feedback si hay bloques de seguridad
            # Corrección: Usar hasattr para verificar si prompt_feedback existe
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                 print(f"      Block Reason: {response.prompt_feedback.block_reason}")
            return None

        # 2. Intentar obtener el texto
        respuesta_texto = response.text.strip()

        if not respuesta_texto:
            # Use 12 spaces for indentation
            print("Error IA: La IA devolvió una respuesta vacía (finish_reason: STOP).")
            return None

        return respuesta_texto

    except (AttributeError, ValueError, IndexError, Exception) as e:
        # Use 8 spaces for indentation
        print(f"Error IA: No se pudo extraer texto de la respuesta. {e}")
        # print(f"Respuesta completa (para depurar): {response}") # Descomentar para depurar
        return None
# --- FIN DEL NUEVO BLOQUE DE EXTRACCIÓN ROBUSTA ---


# --- Funciones de IA (Actualizadas) ---

def obtener_respuesta_opcion_multiple(contexto, pregunta, opciones, respuesta_anterior_incorrecta=None): # <-- 1. Añadir parámetro
    """Obtiene la respuesta correcta para una pregunta de opción múltiple."""
    opciones_texto = "\n".join(f"- {opcion}" for opcion in opciones)
    
    # --- 2. Añadir sección de intento anterior ---
    seccion_intento_anterior = ""
    if respuesta_anterior_incorrecta:
        # Use 8 spaces for indentation
        seccion_intento_anterior = f"""
[Intento Anterior Incorrecto]
Tu respuesta anterior fue: "{respuesta_anterior_incorrecta}"
Esa opción fue incorrecta. Por favor, analiza de nuevo y elige una opción DIFERENTE de la lista.
"""
    # --- Fin de la adición ---

    # --- 3. Actualizar el prompt ---
    prompt = f"""Rol: Experto en tests de lectura.
Analiza contexto, pregunta, opciones. Responde SÓLO texto exacto de la opción correcta.
{seccion_intento_anterior}
---
[Contexto]
{contexto}

[Pregunta]
{pregunta}

[Opciones]
{opciones_texto}
---
Respuesta Correcta:"""
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_limpia_ia = obtener_texto_de_respuesta(response)
        if respuesta_limpia_ia is None: return None

        respuesta_limpia_ia = respuesta_limpia_ia.strip('"\'., ') # Limpieza inicial IA

        # --- ¡INICIO LÓGICA DE VALIDACIÓN MEJORADA! ---
        # 1. Intento de Coincidencia Exacta (como antes)
        if respuesta_limpia_ia in opciones:
             # Use 12 spaces for indentation
             return respuesta_limpia_ia

        print(f"Alerta IA: '{respuesta_limpia_ia}' no exacto en {opciones}. Buscando parecido sin prefijo...");
        respuesta_ia_lower = respuesta_limpia_ia.lower()

        # 2. Intento de Coincidencia Ignorando Prefijos Comunes (a), 1., etc.)
        #    Regex para buscar prefijos como "a) ", "1. ", "A. " al inicio de la opción
        prefix_regex = re.compile(r"^\s*([a-zA-Z]|\d+)\s*[\.\)]\s*")

        for opcion_original in opciones:
            # Use 12 spaces for indentation
            # Eliminar el prefijo si existe
            opcion_sin_prefijo = prefix_regex.sub("", opcion_original).strip()
            opcion_sin_prefijo_lower = opcion_sin_prefijo.lower()

            # Normalizar espacios (replace multiple spaces with one) y limpiar puntuación/ends
            respuesta_ia_compare = ' '.join(respuesta_ia_lower.split()).rstrip('.?! ').strip()
            opcion_compare = ' '.join(opcion_sin_prefijo_lower.split()).rstrip('.?! ').strip()

            # --- DEBUGGING ---
            print(f"      DEBUG Compare:")
            print(f"      IA (len {len(respuesta_ia_compare)}): '{respuesta_ia_compare}'")
            print(f"      Opt (len {len(opcion_compare)}): '{opcion_compare}'")
            print(f"      Son iguales?: {respuesta_ia_compare == opcion_compare}")
            # --- FIN DEBUGGING ---

            # Comparar las versiones limpias
            if respuesta_ia_compare == opcion_compare:
                # Use 16 spaces for indentation
                print(f"Coincidencia sin prefijo/puntuación/espacios encontrada: IA='{respuesta_limpia_ia}' -> Opción='{opcion_original}'")
                # ¡Devolver la OPCIÓN ORIGINAL con prefijo para que el bot principal la encuentre!
                return opcion_original

        # 3. Fallback: Intento de Coincidencia Normalizada (sin prefijos, solo limpieza básica)
        #    (Esto es menos probable que funcione si el paso 2 falló, pero por si acaso)
        print(f"No hubo coincidencia sin prefijo. Intentando coincidencia normalizada simple...");
        for opcion_original in opciones:
             # Use 12 spaces for indentation
             opcion_limpia_lower = opcion_original.strip('"\'., ').lower()
             # Añadimos normalización de espacios aquí también por si acaso
             respuesta_ia_norm_simple = ' '.join(respuesta_ia_lower.split()).rstrip('.?! ').strip()
             opcion_norm_simple = ' '.join(opcion_limpia_lower.split()).rstrip('.?! ').strip()

             if respuesta_ia_norm_simple == opcion_norm_simple:
                  # Use 16 spaces for indentation
                  print(f"Coincidencia normalizada simple encontrada: '{opcion_original}'")
                  return opcion_original # Devolvemos la original

        # 4. Si nada funcionó
        print(f"Error IA (OM): No se encontró coincidencia para '{respuesta_limpia_ia}' en {opciones} (ni con prefijos).");
        return None
        # --- ¡FIN LÓGICA DE VALIDACIÓN MEJORADA! ---

    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API (OM) o Regex: {e}");
        return None

def obtener_orden_correcto(contexto, frases, titulo_pregunta=""):
    """Obtiene el orden correcto para una lista de frases."""
    frases_texto = "\n".join(f'- "{f}"' for f in frases)
    contexto_real = contexto if contexto else titulo_pregunta
    if not contexto_real: contexto_real = "Forma una oración coherente."
    prompt = f"""Rol: Reordenador de listas.
Tu única tarea es reordenar los elementos de la [Lista Desordenada] para formar una oración coherente, basada en la [Instrucción].
Responde SÓLO con una lista Python.

REGLAS ESTRICTAS:
1.  La lista de respuesta debe contener el TEXTO EXACTO de los elementos de la [Lista Desordenada].
2.  NO alteres, añadas, omitas o modifiques NINGÚN string (ej. si la lista te da "the stadium", DEBES usar "the stadium", NO "to the stadium").
3.  La lista de respuesta debe tener exactamente {len(frases)} elementos.
---
[Instrucción]
{contexto_real}

[Lista Desordenada]
{frases_texto}
---
Lista Ordenada (Responde SÓLO con la lista Python):"""
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```python"): respuesta_texto = respuesta_texto[9:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"): print(f"IA (Ord) no es lista: {respuesta_texto}"); return None

        lista_ordenada = ast.literal_eval(respuesta_texto)

        if not isinstance(lista_ordenada, list):
            # Use 12 spaces for indentation
            print(f"IA (Ord) no es lista."); return None

        if len(lista_ordenada) != len(frases):
            # Use 12 spaces for indentation
            print(f"IA (Ord) longitud no coincide: {len(lista_ordenada)} vs {len(frases)}"); return None

        frases_lower_sorted = sorted([f.lower().strip() for f in frases])
        lista_ordenada_lower_sorted = sorted([str(l).lower().strip() for l in lista_ordenada]) # Asegurar string con str()

        if frases_lower_sorted == lista_ordenada_lower_sorted:
            # Use 12 spaces for indentation
            return lista_ordenada # Devolver la lista original de la IA
        else:
            # Use 12 spaces for indentation
            print(f"IA (Ord) inválida o incompleta. Frases: {frases_lower_sorted} vs Resp: {lista_ordenada_lower_sorted}");
            return None

    except (SyntaxError, ValueError) as e: print(f"Error parse IA (Ord): {e}\nResp: {respuesta_texto}"); return None
    except Exception as e: print(f"Error API (Ord): {e}"); return None

def obtener_palabra_correcta(contexto, frase_incompleta, opciones_palabra):
    """Obtiene la palabra correcta para completar una frase."""
    opciones_texto = ", ".join(f'"{op}"' for op in opciones_palabra)
    frase_placeholder = frase_incompleta.replace("___", "[PALABRA_FALTANTE]")
    prompt = f"Rol: Experto en completar frases.\nAnaliza contexto/frase. Elige palabra de [Opciones] para [PALABRA_FALTANTE]. Responde SÓLO palabra correcta.\n---\n[Contexto]\n{contexto}\n\n[Frase Incompleta]\n{frase_placeholder}\n\n[Opciones de Palabra]\n{opciones_texto}\n---\nPalabra Correcta:"
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_limpia = obtener_texto_de_respuesta(response)
        if respuesta_limpia is None: return None

        respuesta_limpia = respuesta_limpia.strip('"\'., ')
        if respuesta_limpia in opciones_palabra: return respuesta_limpia
        else:
            # Use 12 spaces for indentation
            resp_lower = respuesta_limpia.lower()
            for op in opciones_palabra:
                # Use 16 spaces for indentation
                if op.strip('"\'., ').lower() == resp_lower:
                    # Use 20 spaces for indentation
                    print(f"Alerta IA (Comp): Coincidencia sin mayús: '{op}'"); return op
            print(f"Error IA (Comp): '{respuesta_limpia}' no en {opciones_palabra}"); return None
    except Exception as e: print(f"Error API (Comp): {e}"); return None


def obtener_true_false(contexto, afirmacion):
    """Determina si una afirmación es True o False según el contexto."""
    prompt = f"Rol: Experto en evaluar Verdadero (True) o Falso (False).\nAnaliza contexto, determina si afirmación es T/F. Responde SÓLO 'True' o 'False'.\n---\n[Contexto]\n{contexto}\n\n[Afirmación]\n{afirmacion}\n---\nRespuesta (True o False):"
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_limpia = obtener_texto_de_respuesta(response)
        if respuesta_limpia is None: return None

        respuesta_limpia = respuesta_limpia.strip().capitalize()
        if respuesta_limpia == "True" or respuesta_limpia == "False": return respuesta_limpia
        else:
            # Use 12 spaces for indentation
            if "true" in respuesta_limpia.lower(): return "True"
            if "false" in respuesta_limpia.lower(): return "False"
            print(f"Error IA (T/F): No es True/False: '{respuesta_limpia}'"); return None
    except Exception as e: print(f"Error API IA (T/F): {e}"); return None

def obtener_emparejamientos(palabras, definiciones):
    """Obtiene los emparejamientos correctos (Robusto ante listas y errores gramaticales)."""
    palabras_texto = "\n".join(f'- "{p}"' for p in palabras)
    definiciones_texto = "\n".join(f'- "{d}"' for d in definiciones)
    
    prompt = f"""
OBJETIVO: Generar un diccionario de mapeo Python {{clave: valor}}.
SITUACIÓN: Tienes una [LISTA_CLAVE] (izquierda) y una [LISTA_OPCIONES] (derecha).
TU TAREA: Asignar a CADA clave de la izquierda una opción de la derecha.

REGLAS ABSOLUTAS (SI LAS ROMPES, FALLAS):
1. DEBES devolver un diccionario donde las 'keys' sean COPIAS EXACTAS, CARÁCTER POR CARÁCTER, de [LISTA_CLAVE].
2. NO corrijas nada. Si la clave es "IMG_DIM:443x85" o tiene errores, ÚSALA TAL CUAL.
3. OBLIGATORIO: Todas las claves de [LISTA_CLAVE] deben estar en el diccionario. Si no sabes la respuesta lógica, ASIGNA CUALQUIER OPCIÓN DISPONIBLE. No dejes claves huérfanas.
4. Si hay menos claves que opciones, simplemente elige la mejor opción para cada clave y descarta las opciones sobrantes.

[LISTA_CLAVE]
{palabras_texto}

[LISTA_OPCIONES]
{definiciones_texto}
---
Diccionario de Pares (Responde SÓLO el diccionario Python):
"""
    try:
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        # Limpieza básica
        if respuesta_texto.startswith("```python"): respuesta_texto = respuesta_texto[9:]
        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        # Parseo seguro
        try:
            pares = ast.literal_eval(respuesta_texto)
        except:
            try:
                pares = json.loads(respuesta_texto)
            except:
                print(f"IA (Emp) error de formato: {respuesta_texto}")
                return None
        
        if not isinstance(pares, dict):
            print(f"IA (Emp) no devolvió un dict: {type(pares)}")
            return None

        # --- SANITIZACIÓN DE VALORES ---
        pares_limpios = {}
        for k, v in pares.items():
            valor_final = v
            if isinstance(v, list):
                valor_final = v[0] if v else ""
            pares_limpios[k] = str(valor_final)
        pares = pares_limpios
        # -------------------------------

        # Validación Estricta (Tal como pediste)
        claves_esperadas_set = set(palabras)
        claves_recibidas_set = set(pares.keys())
        
        if claves_recibidas_set == claves_esperadas_set:
            return pares
        else:
            # Si faltan claves o sobran, fallamos (porque el prompt les obligó a ser exactos)
            print(f"IA (Emp) claves incorrectas. Esperaba: {claves_esperadas_set}, Recibió: {claves_recibidas_set}")
            return None

    except Exception as e:
        print(f"Error API IA (Emp): {e}")
        return None

def obtener_true_false_lote(contexto, afirmaciones_lista):
    """Obtiene respuestas True/False para una lista de afirmaciones."""
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
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"Error IA (T/F Lote): Respuesta no es una lista: {respuesta_texto}")
            return None
        lista_respuestas = json.loads(respuesta_texto)
        if isinstance(lista_respuestas, list) and len(lista_respuestas) == len(afirmaciones_lista):
            # Use 12 spaces for indentation
            respuestas_normalizadas = []
            for r in lista_respuestas:
                # Use 16 spaces for indentation
                if str(r).strip().capitalize() == "True":
                    # Use 20 spaces for indentation
                    respuestas_normalizadas.append("True")
                elif str(r).strip().capitalize() == "False":
                    # Use 20 spaces for indentation
                    respuestas_normalizadas.append("False")
                else:
                    # Use 20 spaces for indentation
                    print(f"Error IA (T/F Lote): Respuesta inválida '{r}' en la lista.")
                    return None
            print(f"IA (T/F Lote): Recibidas {len(respuestas_normalizadas)} respuestas.")
            return respuestas_normalizadas
        else:
            # Use 12 spaces for indentation
            print("Error IA (T/F Lote): La lista no coincide en tamaño.")
            return None
    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (T/F Lote): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (T/F Lote): {e}")
        return None

def obtener_palabras_correctas_lote(contexto, tareas_lista):
    """Obtiene las palabras correctas para una lista de tareas de completar."""
    print(f"IA (Comp Lote): Enviando {len(tareas_lista)} frases para completar...")
    tareas_texto = ""
    for i, tarea in enumerate(tareas_lista):
        # Use 8 spaces for indentation
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
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"Error IA (Comp Lote): Respuesta no es una lista: {respuesta_texto}")
            return None
        lista_respuestas = json.loads(respuesta_texto)
        if isinstance(lista_respuestas, list) and len(lista_respuestas) == len(tareas_lista):
            # Use 12 spaces for indentation
            respuestas_verificadas = []
            for i, palabra_ia in enumerate(lista_respuestas):
                # Use 16 spaces for indentation
                opciones_tarea = tareas_lista[i]['opciones']
                palabra_ia_limpia = str(palabra_ia).strip().strip('"\'., ')
                if palabra_ia_limpia in opciones_tarea:
                    # Use 20 spaces for indentation
                    respuestas_verificadas.append(palabra_ia_limpia)
                else:
                    # Use 20 spaces for indentation
                    resp_lower = palabra_ia_limpia.lower()
                    encontrado = False
                    for op in opciones_tarea:
                        # Use 24 spaces for indentation
                        if op.strip('"\'., ').lower() == resp_lower:
                            # Use 28 spaces for indentation
                            respuestas_verificadas.append(op)
                            encontrado = True
                            break
                    if not encontrado:
                        # Use 24 spaces for indentation
                        print(f"Error IA (Comp Lote): Tarea {i+1} - '{palabra_ia_limpia}' no en {opciones_tarea}")
                        return None
            print(f"IA (Comp Lote): Recibidas {len(respuestas_verificadas)} respuestas verificadas.")
            return respuestas_verificadas
        else:
            # Use 12 spaces for indentation
            print("Error IA (Comp Lote): La lista no coincide en tamaño.")
            return None
    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (Comp Lote): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Comp Lote): {e}")
        return None

def obtener_numeros_parrafo_lote(contexto, ideas_lista, respuesta_anterior_incorrecta=None):
    """Obtiene los números de párrafo correspondientes a una lista de ideas."""
    print(f"IA (Parag Lote): Enviando {len(ideas_lista)} ideas...")
    ideas_texto = "\n".join(f'- "{idea}"' for idea in ideas_lista)
    seccion_intento_anterior = ""
    if respuesta_anterior_incorrecta:
        # Use 8 spaces for indentation
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
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"Error IA (Parag Lote): Respuesta no es una lista: {respuesta_texto}")
            return None
        lista_respuestas_num = json.loads(respuesta_texto)
        if isinstance(lista_respuestas_num, list) and len(lista_respuestas_num) == len(ideas_lista):
            # Use 12 spaces for indentation
            respuestas_verificadas = [str(n).strip() for n in lista_respuestas_num]
            print(f"IA (Parag Lote): Recibidas {len(respuestas_verificadas)} respuestas.")
            return respuestas_verificadas
        else:
            # Use 12 spaces for indentation
            print("Error IA (Parag Lote): La lista no coincide en tamaño.")
            return None
    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (Parag Lote): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Parag Lote): {e}")
        return None

def extraer_solucion_del_error(texto_error_modal, preguntas_lista):
    """Extrae la solución (dict {pregunta: respuesta}) del texto de error del modal."""
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
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```python"): respuesta_texto = respuesta_texto[9:]
        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("{") or not respuesta_texto.endswith("}"):
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje) no es dicc: {respuesta_texto}"); return None
        # Usar json.loads es más seguro si la IA devuelve JSON válido
        solucion_dict = json.loads(respuesta_texto)
        # Validación: ¿Están todas las preguntas originales como claves?
        if isinstance(solucion_dict, dict) and all(p in solucion_dict for p in preguntas_lista):
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje) extrajo: {solucion_dict}")
            return solucion_dict
        else:
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje) inválido o incompleto. Faltan claves o no es dict: {solucion_dict}"); return None
    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        # Intentar con ast.literal_eval como fallback si JSON falla
        try:
            # Use 12 spaces for indentation
            solucion_dict = ast.literal_eval(respuesta_texto)
            if isinstance(solucion_dict, dict) and all(p in solucion_dict for p in preguntas_lista):
                 # Use 16 spaces for indentation
                 print(f"IA (Aprendizaje) [Fallback AST] extrajo: {solucion_dict}")
                 return solucion_dict
            else:
                 # Use 16 spaces for indentation
                 print(f"IA (Aprendizaje) [Fallback AST] inválido o incompleto: {solucion_dict}"); return None
        except (SyntaxError, ValueError) as e_ast:
             # Use 12 spaces for indentation
             print(f"Error parse JSON y AST IA (Aprendizaje): JSON({e}), AST({e_ast})\nResp: {respuesta_texto}")
             return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Aprendizaje): {e}"); return None

def obtener_respuestas_om_lote(contexto, tareas_lista, respuesta_anterior_incorrecta=None):
    """Obtiene respuestas para una lista de tareas de opción múltiple."""
    print(f"IA (OM Lote): Enviando {len(tareas_lista)} preguntas...")
    tareas_texto = ""
    for i, tarea in enumerate(tareas_lista):
        # Use 8 spaces for indentation
        opciones_str = ", ".join(f'"{op}"' for op in tarea['opciones'])
        tareas_texto += f"Tarea {i+1}:\n"
        tareas_texto += f"  Pregunta: \"{tarea['pregunta']}\"\n"
        tareas_texto += f"  Opciones: [{opciones_str}]\n\n"
    seccion_intento_anterior = ""
    if respuesta_anterior_incorrecta:
        # Use 8 spaces for indentation
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
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()
        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"Error IA (OM Lote): Respuesta no es una lista: {respuesta_texto}")
            return None
        lista_respuestas = json.loads(respuesta_texto)
        if isinstance(lista_respuestas, list) and len(lista_respuestas) == len(tareas_lista):
            # Use 12 spaces for indentation
            respuestas_verificadas = []
            prefix_regex_om = re.compile(r"^\s*([a-zA-Z]|\d+)\s*[\.\)]\s*")

            for i, palabra_ia in enumerate(lista_respuestas):
                # Use 16 spaces for indentation
                opciones_tarea_originales = tareas_lista[i]['opciones']
                palabra_ia_limpia = str(palabra_ia).strip().strip('"\'., ')
                palabra_ia_sin_prefijo_lower = prefix_regex_om.sub("", palabra_ia_limpia).lower()

                encontrado = False
                for j, op_original in enumerate(opciones_tarea_originales):
                    # Use 20 spaces for indentation
                    op_sin_prefijo = prefix_regex_om.sub("", op_original).strip()
                    op_sin_prefijo_lower = op_sin_prefijo.lower()

                    # Limpiar puntuación final y normalizar espacios ANTES de comparar
                    respuesta_compare = ' '.join(palabra_ia_sin_prefijo_lower.split()).rstrip('.?! ').strip()
                    opcion_compare = ' '.join(op_sin_prefijo_lower.split()).rstrip('.?! ').strip()

                    if respuesta_compare == opcion_compare:
                        # Use 24 spaces for indentation
                        respuestas_verificadas.append(op_original) # Guarda la original
                        encontrado = True
                        break
                if not encontrado:
                    # Use 20 spaces for indentation
                    # Fallback por si la IA devuelve la opción con prefijo
                    if palabra_ia_limpia in opciones_tarea_originales:
                         # Use 24 spaces for indentation
                         print(f"      Alerta IA (OM Lote): Tarea {i+1} - IA devolvió '{palabra_ia_limpia}' con prefijo, encontrada exacto.")
                         respuestas_verificadas.append(palabra_ia_limpia)
                         encontrado = True

                if not encontrado:
                    # Use 20 spaces for indentation
                    print(f"Error IA (OM Lote): Tarea {i+1} - '{palabra_ia_limpia}' no coincide con ninguna opción (ni sin prefijo/puntuación) en {opciones_tarea_originales}")
                    return None

            print(f"IA (OM Lote): Recibidas {len(respuestas_verificadas)} respuestas verificadas.")
            return respuestas_verificadas
        else:
            # Use 12 spaces for indentation
            print("Error IA (OM Lote): La lista no coincide en tamaño.")
            return None
    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (OM Lote): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (OM Lote): {e}")
        return None

def extraer_solucion_simple(texto_error_modal, opciones_lista):
    """Extrae la única respuesta correcta del texto de error del modal."""
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
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        respuesta_limpia = respuesta_texto.strip('"\'., ')

        # Validación mejorada (ignora prefijos y puntuación final + normaliza espacios)
        prefix_regex_learn = re.compile(r"^\s*([a-zA-Z]|\d+)\s*[\.\)]\s*")
        respuesta_sin_prefijo_lower = prefix_regex_learn.sub("", respuesta_limpia).lower()
        respuesta_compare = ' '.join(respuesta_sin_prefijo_lower.split()).rstrip('.?! ').strip()


        for op_original in opciones_lista:
            # Use 12 spaces for indentation
            op_sin_prefijo = prefix_regex_learn.sub("", op_original).strip()
            op_sin_prefijo_lower = op_sin_prefijo.lower()
            opcion_compare = ' '.join(op_sin_prefijo_lower.split()).rstrip('.?! ').strip()

            if respuesta_compare == opcion_compare:
                # Use 16 spaces for indentation
                print(f"IA (Aprendizaje Simple) extrajo (match sin prefijo/puntuación/espacios): '{op_original}'")
                return op_original # Devolver la original

        # Fallback si la IA devuelve la opción con prefijo y coincide exacto
        if respuesta_limpia in opciones_lista:
             # Use 12 spaces for indentation
             print(f"IA (Aprendizaje Simple) extrajo (match exacto con prefijo): '{respuesta_limpia}'")
             return respuesta_limpia

        print(f"IA (Aprendizaje Simple) falló. Respuesta '{respuesta_limpia}' no en {opciones_lista} (ni normalizada)")
        return None

    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Aprendizaje Simple): {e}"); return None

def extraer_solucion_lote_tf(texto_error_modal, afirmaciones_lista):
    """Extrae la secuencia True/False correcta del texto de error."""
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
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Lote T/F) no es lista: {respuesta_texto}"); return None

        solucion_lista = json.loads(respuesta_texto)

        if isinstance(solucion_lista, list) and len(solucion_lista) == num_afirmaciones:
            # Use 12 spaces for indentation
            respuestas_normalizadas = []
            for r in solucion_lista:
                # Use 16 spaces for indentation
                r_norm = str(r).strip().capitalize()
                if r_norm == "True" or r_norm == "False":
                    # Use 20 spaces for indentation
                    respuestas_normalizadas.append(r_norm)
                else:
                    # Use 20 spaces for indentation
                    print(f"IA (Aprendizaje Lote T/F) respuesta inválida '{r}'"); return None

            print(f"IA (Aprendizaje Lote T/F) extrajo: {respuestas_normalizadas}")
            return respuestas_normalizadas
        else:
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Lote T/F) inválido o incompleto: {solucion_lista}"); return None

    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (Aprendizaje Lote T/F): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Aprendizaje Lote T/F): {e}"); return None

def extraer_solucion_ordenar(texto_error_modal, frases_desordenadas):
    """Extrae la secuencia ordenada correcta del texto de error."""
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
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Ordenar) no es lista: {respuesta_texto}"); return None

        solucion_lista = json.loads(respuesta_texto)

        # Usar sets para comparación robusta
        frases_originales_set = set(frases_desordenadas)
        # Convertir a string antes de añadir al set por si acaso
        solucion_set = set(str(item) for item in solucion_lista)


        if (isinstance(solucion_lista, list) and
            len(solucion_lista) == num_frases and
            solucion_set == frases_originales_set): # Comprobar que contenga exactamente las mismas frases
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Ordenar) extrajo: {solucion_lista}")
            return solucion_lista
        else:
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Ordenar) inválido, incompleto o no coincide con frases originales. Resp: {solucion_lista}"); return None

    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (Aprendizaje Ordenar): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Aprendizaje Ordenar): {e}"); return None

def extraer_solucion_emparejar(texto_error_modal, claves_lista, definiciones_lista):
    """Extrae los pares {clave: definicion} correctos del texto de error."""
    print(f"IA (Aprendizaje Emparejar): Analizando texto de error...")
    claves_str = ", ".join(f'"{c}"' for c in claves_lista)
    defs_str = ", ".join(f'"{d}"' for d in definiciones_lista)

    prompt = f"""
Rol: Experto en extracción de datos.
Analiza el [Texto de Error] de un pop-up. Este texto contiene la solución correcta para un ejercicio de emparejamiento.

Las [Claves] (los elementos de la izquierda, podrían ser texto o identificadores como IMG_DIM:...) eran: {claves_str}
Las [Opciones] (los elementos de la derecha) eran: {defs_str}

Tu tarea es devolver SÓLO un diccionario JSON que mapee CADA clave de la [Claves] a su opción correcta de [Opciones], basándote en la solución del [Texto de Error]. Usa las claves exactas proporcionadas.

[Texto de Error]:
"{texto_error_modal}"

---
Diccionario de Solución ({{clave: opcion}}):
"""
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("{") or not respuesta_texto.endswith("}"):
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Emparejar) no es dicc: {respuesta_texto}"); return None

        solucion_dict = json.loads(respuesta_texto)

        # Validación
        claves_esperadas_set = set(claves_lista)
        claves_recibidas_set = set(solucion_dict.keys())
        valores_recibidos_set = set(solucion_dict.values())
        definiciones_set = set(definiciones_lista)

        if (isinstance(solucion_dict, dict) and
            len(solucion_dict) == len(claves_lista) and
            claves_recibidas_set == claves_esperadas_set and
            valores_recibidos_set.issubset(definiciones_set)):
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Emparejar) extrajo: {solucion_dict}")
            return solucion_dict
        else:
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Emparejar) inválido o incompleto. Claves esperadas:{len(claves_lista)}, Recibidas:{len(solucion_dict)}. Resp: {solucion_dict}"); return None

    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        # Fallback con ast.literal_eval
        try:
             # Use 12 spaces for indentation
             solucion_dict = ast.literal_eval(respuesta_texto)
             claves_esperadas_set = set(claves_lista)
             claves_recibidas_set = set(solucion_dict.keys())
             valores_recibidos_set = set(solucion_dict.values())
             definiciones_set = set(definiciones_lista)
             if (isinstance(solucion_dict, dict) and
                 len(solucion_dict) == len(claves_lista) and
                 claves_recibidas_set == claves_esperadas_set and
                 valores_recibidos_set.issubset(definiciones_set)):
                  # Use 16 spaces for indentation
                  print(f"IA (Aprendizaje Emparejar) [Fallback AST] extrajo: {solucion_dict}")
                  return solucion_dict
             else:
                  # Use 16 spaces for indentation
                  print(f"IA (Aprendizaje Emparejar) [Fallback AST] inválido: {solucion_dict}"); return None
        except (SyntaxError, ValueError) as e_ast:
             # Use 12 spaces for indentation
             print(f"Error parse JSON y AST IA (Aprendizaje Emparejar): JSON({e}), AST({e_ast})\nResp: {respuesta_texto}")
             return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Aprendizaje Emparejar): {e}"); return None

def extraer_solucion_lote_completar(texto_error_modal, tareas_lista):
    """Extrae la lista de palabras correctas para completar del texto de error."""
    print(f"IA (Aprendizaje Lote Completar): Analizando texto de error...")

    tareas_str = ""
    for i, tarea in enumerate(tareas_lista):
        # Use 8 spaces for indentation
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
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Lote Completar) no es lista: {respuesta_texto}"); return None

        solucion_lista = json.loads(respuesta_texto)

        if isinstance(solucion_lista, list) and len(solucion_lista) == len(tareas_lista):
            # Use 12 spaces for indentation
            respuestas_verificadas = []
            for i, respuesta_ia in enumerate(solucion_lista):
                # Use 16 spaces for indentation
                opciones_originales = tareas_lista[i]['opciones']
                respuesta_ia_limpia = str(respuesta_ia).strip().strip('"\'., ')

                if respuesta_ia_limpia in opciones_originales:
                    # Use 20 spaces for indentation
                    respuestas_verificadas.append(respuesta_ia_limpia)
                else:
                    # Use 20 spaces for indentation
                    resp_lower = respuesta_ia_limpia.lower()
                    encontrado = False
                    for op in opciones_originales:
                        # Use 24 spaces for indentation
                        if op.strip('"\'., ').lower() == resp_lower:
                            # Use 28 spaces for indentation
                            respuestas_verificadas.append(op)
                            encontrado = True; break
                    if not encontrado:
                        # Use 24 spaces for indentation
                        print(f"IA (Aprendizaje Lote Completar) Tarea {i+1}: '{respuesta_ia}' no en {opciones_originales}"); return None

            print(f"IA (Aprendizaje Lote Completar) extrajo: {respuestas_verificadas}")
            return respuestas_verificadas
        else:
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Lote Completar) inválido o incompleto: {solucion_lista}"); return None

    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (Aprendizaje Lote Completar): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Aprendizaje Lote Completar): {e}"); return None

def obtener_palabra_ordenada(letras_desordenadas):
    """Obtiene la palabra ordenada a partir de letras desordenadas."""
    print(f"IA (Ordenar Palabra): Ordenando '{letras_desordenadas}'...")
    letras_limpias = "".join(letras_desordenadas.split('/')).replace(" ", "")

    prompt = f"""
Rol: Experto en anagramas y vocabulario.
Analiza las [Letras Desordenadas].
Encuentra la palabra correcta en inglés que se forma con esas letras.
Responde SÓLO con la palabra ordenada.

[Letras Desordenadas]:
{letras_limpias}

---
Palabra Ordenada:
"""
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        palabra_ordenada = respuesta_texto.strip().upper()

        if sorted(palabra_ordenada) == sorted(letras_limpias.upper()):
            # Use 12 spaces for indentation
            print(f"IA (Ordenar Palabra) devolvió: '{palabra_ordenada}'")
            return palabra_ordenada
        else:
            # Use 12 spaces for indentation
            print(f"Error IA (Ordenar Palabra): La respuesta '{palabra_ordenada}' no usa las mismas letras que '{letras_limpias}'.")
            return palabra_ordenada # Devolver igualmente

    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Ordenar Palabra): {e}"); return None

def obtener_palabras_ordenadas_lote(lista_palabras_desordenadas):
    """Obtiene una lista de palabras ordenadas a partir de una lista de letras desordenadas."""
    print(f"IA (Ordenar Palabra Lote): Ordenando {len(lista_palabras_desordenadas)} palabras...")
    palabras_texto = "\n".join(f'- "{p}"' for p in lista_palabras_desordenadas)

    prompt = f"""
Rol: Experto en anagramas y vocabulario.
Analiza cada palabra en la [Lista de Palabras Desordenadas].
Encuentra la palabra correcta en inglés que se forma con las letras de CADA palabra.
Responde SÓLO con una lista JSON de strings, donde cada string es la palabra ordenada correcta, en el mismo orden que la lista original.

[Lista de Palabras Desordenadas]:
{palabras_texto}

---
Respuesta (Sólo la lista JSON de palabras ordenadas):
"""
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"IA (Ordenar Lote) no es lista: {respuesta_texto}"); return None

        lista_ordenada = json.loads(respuesta_texto)

        if isinstance(lista_ordenada, list) and len(lista_ordenada) == len(lista_palabras_desordenadas):
            # Use 12 spaces for indentation
            lista_ordenada_upper = [str(p).strip().upper() for p in lista_ordenada]
            print(f"IA (Ordenar Lote) devolvió: {lista_ordenada_upper}")
            return lista_ordenada_upper
        else:
            # Use 12 spaces for indentation
            print(f"IA (Ordenar Lote) inválida o longitud incorrecta. Resp: {lista_ordenada}"); return None

    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (Ordenar Lote): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Ordenar Lote): {e}"); return None

def extraer_solucion_lote_escribir(texto_error_modal, palabras_desordenadas_lista):
    """Extrae la lista de palabras ordenadas correctas del texto de error."""
    print(f"IA (Aprendizaje Lote Escribir): Analizando texto de error...")
    num_palabras = len(palabras_desordenadas_lista)
    palabras_str = ", ".join(f'"{p}"' for p in palabras_desordenadas_lista)

    prompt = f"""
Rol: Experto en extracción de datos.
Analiza el [Texto de Error] de un pop-up. Este texto contiene la solución correcta para un ejercicio de ordenar letras y escribir {num_palabras} palabras.
Las palabras desordenadas originales eran (en orden): {palabras_str}.

Tu tarea es devolver SÓLO una lista JSON de strings, donde cada string es la palabra ORDENADA correcta, correspondiendo en orden a las palabras desordenadas originales.

[Texto de Error]:
"{texto_error_modal}"

---
Respuesta (Sólo la lista JSON ["PALABRA1", "PALABRA2", ...]):
"""
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Lote Escribir) no es lista: {respuesta_texto}"); return None

        solucion_lista = json.loads(respuesta_texto)

        if isinstance(solucion_lista, list) and len(solucion_lista) == num_palabras:
             # Use 12 spaces for indentation
             respuestas_verificadas = []
             for i, palabra_ia in enumerate(solucion_lista):
                 # Use 16 spaces for indentation
                 palabra_ia_upper = str(palabra_ia).strip().upper()
                 original_upper = palabras_desordenadas_lista[i].upper()
                 # Validación simple de letras (aproximada)
                 if sorted(palabra_ia_upper) == sorted("".join(original_upper.split('/')).replace(" ", "")):
                      # Use 20 spaces for indentation
                      respuestas_verificadas.append(palabra_ia_upper)
                 else:
                      # Use 20 spaces for indentation
                      print(f"IA (Aprendizaje Lote Escribir) WARN Tarea {i+1}: '{palabra_ia_upper}' no usa las mismas letras que '{original_upper}'. Se usará igualmente.")
                      respuestas_verificadas.append(palabra_ia_upper)

             print(f"IA (Aprendizaje Lote Escribir) extrajo: {respuestas_verificadas}")
             return respuestas_verificadas
        else:
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Lote Escribir) inválido o incompleto: {solucion_lista}"); return None

    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (Aprendizaje Lote Escribir): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Aprendizaje Lote Escribir): {e}"); return None

def obtener_respuestas_escribir_opciones_lote(contexto, titulo_pregunta, tareas_lista):
    """Obtiene las palabras correctas para completar frases usando opciones del título/contexto."""
    print(f"IA (Escribir Opciones Lote): Enviando {len(tareas_lista)} frases...")
    tareas_texto = "\n".join(f'- "{t["frase"]}"' for t in tareas_lista)
    contexto_real = titulo_pregunta if titulo_pregunta else contexto
    if not contexto_real: contexto_real = "Complete the sentence"

    prompt = f"""Rol: Experto en gramática y preposiciones.
Analiza la [Instrucción/Contexto] para determinar las opciones de palabras (ej: IN, ON, AT, BEFORE, AFTER, etc.).
Luego, para cada [Tarea], completa la frase (donde está '___') usando SÓLO una de esas opciones.
Responde SÓLO con una lista JSON de strings (las palabras correctas), en el mismo orden que la lista de tareas.

[Instrucción/Contexto]:
{contexto_real}

[Lista de Tareas]:
{tareas_texto}
---
Respuesta (Sólo la lista JSON):
"""
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"IA (Escribir Opciones Lote) no es lista: {respuesta_texto}"); return None

        lista_respuestas = json.loads(respuesta_texto)

        if isinstance(lista_respuestas, list) and len(lista_respuestas) == len(tareas_lista):
            # Use 12 spaces for indentation
            lista_respuestas_upper = [str(p).strip().upper() for p in lista_respuestas]
            print(f"IA (Escribir Opciones Lote) devolvió: {lista_respuestas_upper}")
            return lista_respuestas_upper
        else:
            # Use 12 spaces for indentation
            print(f"IA (Escribir Opciones Lote) inválida o longitud incorrecta. Resp: {lista_respuestas}"); return None

    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (Escribir Opciones Lote): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Escribir Opciones Lote): {e}"); return None

def extraer_solucion_lote_escribir_opciones(texto_error_modal, tareas_lista):
    """Extrae la lista de palabras correctas (opciones) del texto de error."""
    print(f"IA (Aprendizaje Lote Escribir Opciones): Analizando texto de error...")
    num_tareas = len(tareas_lista)
    tareas_str = "\n".join(f'- "{t["frase"]}"' for t in tareas_lista)

    prompt = f"""
Rol: Experto en extracción de datos.
Analiza el [Texto de Error] de un pop-up. Contiene la solución para {num_tareas} frases.
Las frases originales eran:
{tareas_str}

Tu tarea es devolver SÓLO una lista JSON de strings, donde cada string es la palabra correcta (ej: IN, ON, AT)
que completaba cada frase, en el orden correcto.

[Texto de Error]:
"{texto_error_modal}"

---
Respuesta (Sólo la lista JSON ["PALABRA1", "PALABRA2", ...]):
"""
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Lote Escribir Opciones) no es lista: {respuesta_texto}"); return None

        solucion_lista = json.loads(respuesta_texto)

        if isinstance(solucion_lista, list) and len(solucion_lista) == num_tareas:
            # Use 12 spaces for indentation
            solucion_lista_upper = [str(p).strip().upper() for p in solucion_lista]
            print(f"IA (Aprendizaje Lote Escribir Opciones) extrajo: {solucion_lista_upper}")
            return solucion_lista_upper
        else:
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Lote Escribir Opciones) inválido o incompleto: {solucion_lista}"); return None

    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (Aprendizaje Lote Escribir Opciones): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Aprendizaje Lote Escribir Opciones): {e}"); return None
    
# --- ¡NUEVA FUNCIÓN DE APRENDIZAJE PARA TIPO 12! ---
def extraer_solucion_lote_dictado(texto_error_modal, tareas_lista):
    """Extrae la(s) frase(s) completa(s) de un error de dictado TIPO 12."""
    print(f"IA (Aprendizaje Lote DICTADO T12): Analizando texto de error...")
    num_tareas = len(tareas_lista) # Generalmente 1

    prompt = f"""
Rol: Experto en extracción de datos.
Analiza el [Texto de Error] de un pop-up. Este texto contiene la(s) oración(es) correcta(s) de un ejercicio de dictado.
La respuesta correcta es la oración completa que el usuario debía escribir.

Tu tarea es devolver SÓLO una lista JSON de strings, donde cada string es la ORACIÓN COMPLETA correcta.
Limpia la respuesta de comillas o prefijos como "Respuesta: ".
La lista debe tener {num_tareas} elemento(s).

[Texto de Error]:
"{texto_error_modal}"

---
Respuesta (Sólo la lista JSON ["ORACIÓN COMPLETA 1", ...]):
"""
    try:
        # Use 8 spaces for indentation
        response = model.generate_content(prompt)
        respuesta_texto = obtener_texto_de_respuesta(response)
        if respuesta_texto is None: return None

        if respuesta_texto.startswith("```json"): respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"): respuesta_texto = respuesta_texto[:-3]
        respuesta_texto = respuesta_texto.strip()

        if not respuesta_texto.startswith("[") or not respuesta_texto.endswith("]"):
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Lote Dictado) no es lista: {respuesta_texto}"); return None

        solucion_lista = json.loads(respuesta_texto)

        if isinstance(solucion_lista, list) and len(solucion_lista) == num_tareas:
            # Use 12 spaces for indentation
            # Limpiamos comillas dobles y convertimos a MAYÚSCULAS
            solucion_lista_limpia = [str(p).strip().strip('"').upper() for p in solucion_lista]
            print(f"IA (Aprendizaje Lote Dictado) extrajo: {solucion_lista_limpia}")
            return solucion_lista_limpia
        else:
            # Use 12 spaces for indentation
            print(f"IA (Aprendizaje Lote Dictado) inválido o incompleto (esperaba {num_tareas}, recibió {len(solucion_lista)}): {solucion_lista}"); return None

    except json.JSONDecodeError as e:
        # Use 8 spaces for indentation
        print(f"Error parse JSON IA (Aprendizaje Lote Dictado): {e}\nResp: {respuesta_texto}")
        return None
    except Exception as e:
        # Use 8 spaces for indentation
        print(f"Error API IA (Aprendizaje Lote Dictado): {e}"); return None