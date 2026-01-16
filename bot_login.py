import time
from selenium.webdriver.support import expected_conditions as EC

def realizar_login(driver, wait, sel, config):
    """
    Ejecuta la secuencia completa de inicio de sesión:
    Pop-up -> Botón Inicia Sesión -> Credenciales -> Botón Acceder
    """
    print("🔑 [Login] Iniciando secuencia de acceso automática...")
    
    # 1. Navegar
    driver.get(config.URL_INICIAL)

    # 2. Cerrar Pop-up de Bienvenida
    try:
        print("   🍿 Buscando Pop-up...")
        # Usamos un wait corto para no perder tiempo si no sale
        boton_popup = wait.until(EC.element_to_be_clickable(sel.SELECTOR_CERRAR_POPUP))
        boton_popup.click()
        print("   ✅ Pop-up cerrado.")
        time.sleep(1)
    except:
        print("   ℹ️ No apareció el pop-up (o ya se cerró).")

    # 3. Clic en 'Inicia Sesión' (Botón Verde)
    try:
        print("   👆 Clickeando 'Inicia Sesión'...")
        boton_login = wait.until(EC.element_to_be_clickable(sel.SELECTOR_INICIA_SESION_VERDE))
        boton_login.click()
    except Exception as e:
        print(f"   ❌ Error buscando botón 'Inicia Sesión': {e}")
        return False

    # 4. Ingresar Credenciales
    try:
        print("   ✍️ Escribiendo credenciales...")
        # Usuario
        input_user = wait.until(EC.visibility_of_element_located(sel.SELECTOR_USUARIO_INPUT))
        input_user.clear()
        input_user.send_keys(config.TU_USUARIO_EMAIL)
        
        # Contraseña
        input_pass = wait.until(EC.visibility_of_element_located(sel.SELECTOR_PASSWORD_INPUT))
        input_pass.clear()
        input_pass.send_keys(config.TU_CONTRASENA)
    except Exception as e:
        print(f"   ❌ Error ingresando usuario/pass: {e}")
        return False

    # 5. Clic en 'Acceder' (Botón Amarillo)
    try:
        print("   🚀 Clickeando 'Acceder'...")
        boton_acceder = wait.until(EC.element_to_be_clickable(sel.SELECTOR_ACCEDER_AMARILLO))
        boton_acceder.click()
    except Exception as e:
        print(f"   ❌ Error clickeando Acceder: {e}")
        return False

    print("   ⏳ Esperando carga del menú principal...")
    time.sleep(3) # Pequeña pausa para asegurar la carga
    print("✅ Login Completado.")
    return True