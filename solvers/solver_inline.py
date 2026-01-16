from selenium.webdriver.common.by import By
import time

def resolver(driver, sel, ia_utils, contexto): # <--- Interfaz estándar
    print("   🔍 [Solver T13] Analizando Selección en Línea...")
    
    filas = driver.find_elements(*sel.SELECTOR_TIPO_13_FILAS)
    lista_items = []
    
    # 1. Recolectar
    for i, fila in enumerate(filas):
        txt = fila.text.replace("\n", " ").strip()
        btns = [b.text.strip() for b in fila.find_elements(By.TAG_NAME, "button") if b.text.strip()]
        if btns:
            lista_items.append(f"Item {i+1}: {txt} | Opciones: {btns}")

    # 2. Consultar IA
    prompt = f"Grammar test. Context: {contexto}. Items:\n" + "\n".join(lista_items) + "\nReply ONLY: Item X: [Option]"
    resp = ia_utils.obtener_texto_de_respuesta(ia_utils.model.generate_content(prompt))
    print(f"      🤖 IA Dice: {resp}")

    # 3. Ejecutar
    if resp:
        for linea in resp.split("\n"):
            if "Item" in linea and ":" in linea:
                try:
                    parts = linea.split(":")
                    idx = int(parts[0].replace("Item", "").strip()) - 1
                    txt_resp = parts[1].strip().lower()
                    
                    if 0 <= idx < len(filas):
                        for btn in filas[idx].find_elements(By.TAG_NAME, "button"):
                            if btn.text.strip().lower() == txt_resp:
                                driver.execute_script("arguments[0].click();", btn)
                                print(f"      ✅ Click: {btn.text}")
                                time.sleep(0.5)
                except: pass