import os
import logging
# Suprimir logs de Selenium
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import time
from fuzzywuzzy import fuzz, process
import re

try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

class AgenteTransparencia:
    def __init__(self, download_path="downloads"):
        self.download_path = os.path.abspath(download_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        
        # DICCIONARIO DE ESTADOS Y ABREVIACIONES
        self.estados_mexico = {
            # Estado completo -> Abreviación
            'aguascalientes': 'AS',
            'baja california': 'BC',
            'baja california sur': 'BS',
            'campeche': 'CC',
            'coahuila': 'CL',
            'coahuila de zaragoza': 'CL',
            'colima': 'CM',
            'chiapas': 'CS',
            'chihuahua': 'CH',
            'ciudad de mexico': 'DF',
            'cdmx': 'DF',
            'durango': 'DG',
            'guanajuato': 'GT',
            'guerrero': 'GR',
            'hidalgo': 'HG',
            'jalisco': 'JC',
            'mexico': 'MC',
            'estado de mexico': 'MC',
            'michoacan': 'MN',
            'michoacan de ocampo': 'MN',
            'morelos': 'MS',
            'nayarit': 'NT',
            'nuevo leon': 'NL',
            'oaxaca': 'OC',
            'puebla': 'PL',
            'queretaro': 'QT',
            'quintana roo': 'QR',
            'san luis potosi': 'SP',
            'sinaloa': 'SL',
            'sonora': 'SR',
            'tabasco': 'TC',
            'tamaulipas': 'TS',
            'tlaxcala': 'TL',
            'veracruz': 'VZ',
            'yucatan': 'YN',
            'zacatecas': 'ZS'
        }
        
        # DICCIONARIO INVERSO: Abreviación -> Estado
        self.abreviaciones_estados = {v: k for k, v in self.estados_mexico.items()}
        
        # Agregar variaciones comunes
        self.abreviaciones_estados.update({
            'DF': 'ciudad de mexico',
            'CDMX': 'ciudad de mexico',
            'EDOMEX': 'estado de mexico',
            'EDO MEX': 'estado de mexico'
        })
    
    def detectar_y_convertir_estado(self, institucion_texto):
        """
        FUNCIÓN CORREGIDA: Mejor detección de estados
        """
        variaciones = [institucion_texto]  # Siempre incluir el texto original
        texto_lower = institucion_texto.lower()
        
        print(f"🔍 Analizando estados en: '{institucion_texto}'")
        
        estado_detectado = None
        abreviacion_detectada = None
        
        # 1. DETECTAR ESTADOS COMPLETOS con PRIORIDAD POR EXACTITUD
        estados_encontrados = []
        
        for estado_completo, abreviacion in self.estados_mexico.items():
            # Buscar el estado en diferentes posiciones
            if f" de {estado_completo}" in texto_lower:
                estados_encontrados.append((estado_completo, abreviacion, "de"))
            elif f" del {estado_completo}" in texto_lower:
                estados_encontrados.append((estado_completo, abreviacion, "del"))
            elif f"{estado_completo} " in texto_lower:
                estados_encontrados.append((estado_completo, abreviacion, "inicio"))
            elif f" {estado_completo}" in texto_lower:
                estados_encontrados.append((estado_completo, abreviacion, "final"))
            elif estado_completo in texto_lower:
                estados_encontrados.append((estado_completo, abreviacion, "contenido"))
        
        # Usar el estado más específico encontrado
        if estados_encontrados:
            # Priorizar "de estado" y "del estado"
            for estado, abrev, tipo in estados_encontrados:
                if tipo in ["de", "del"]:
                    estado_detectado = estado
                    abreviacion_detectada = abrev
                    break
            
            # Si no hay "de/del", usar el primero
            if not estado_detectado:
                estado_detectado, abreviacion_detectada, _ = estados_encontrados[0]
            
            print(f"   📍 ESTADO DETECTADO: '{estado_detectado}' -> '{abreviacion_detectada}'")
            
            # Crear variaciones con abreviación
            texto_sin_estado = texto_lower
            texto_sin_estado = texto_sin_estado.replace(f" de {estado_detectado}", "")
            texto_sin_estado = texto_sin_estado.replace(f" del {estado_detectado}", "")
            texto_sin_estado = texto_sin_estado.replace(f"{estado_detectado} ", "")
            texto_sin_estado = texto_sin_estado.replace(f" {estado_detectado}", "")
            texto_sin_estado = texto_sin_estado.strip()
            
            # Generar variación principal con abreviación
            if texto_sin_estado:
                variacion_principal = f"{abreviacion_detectada} - {texto_sin_estado.title()}"
                variaciones.append(variacion_principal)
                print(f"   ✅ Variación principal: '{variacion_principal}'")
        
        # 2. DETECTAR ABREVIACIONES (proceso inverso)
        patron_abreviacion = r'\b([A-Z]{2})\s*-\s*(.+)'
        match = re.match(patron_abreviacion, institucion_texto)
        
        if match:
            abrev_encontrada = match.group(1)
            resto_texto = match.group(2)
            
            if abrev_encontrada in self.abreviaciones_estados:
                estado_completo = self.abreviaciones_estados[abrev_encontrada]
                print(f"   📍 Abreviación detectada: '{abrev_encontrada}' -> '{estado_completo}'")
                
                # Crear variaciones con estado completo
                variacion_con_de = f"{resto_texto} de {estado_completo.title()}"
                variaciones.append(variacion_con_de)
                print(f"   ✅ Variación inversa: '{variacion_con_de}'")
        
        # Limpiar duplicados
        variaciones_limpias = []
        for var in variaciones:
            var_limpia = var.strip()
            if var_limpia and var_limpia not in variaciones_limpias:
                variaciones_limpias.append(var_limpia)
        
        print(f"📋 Total variaciones: {len(variaciones_limpias)}")
        for i, var in enumerate(variaciones_limpias):
            print(f"   {i+1}. {var}")
        
        return variaciones_limpias
    
    def crear_driver_anti_deteccion(self, headless=False):
        """Crea un driver de Chrome configurado para la página (sin verificación de seguridad)."""
        
        options = Options()
        
        # Configuraciones básicas
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--exclude-switches=enable-automation")
        options.add_argument("--useAutomationExtension=false")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        
        # User agent real de Chrome
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
        
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        if headless:
            options.add_argument("--headless=new")
        
        # Crear driver
        driver = webdriver.Chrome(options=options)
        
        # Configurar viewport
        if not headless:
            driver.set_window_size(1366, 768)
        
        # JavaScript básico para ocultar automatización
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver

    def encontrar_opcion_mas_similar(self, driver, wait, institucion_buscada):
        """
        FUNCIÓN CORREGIDA: Prioriza ESTADO detectado sobre similitud general
        """
        print(f"🔍 Búsqueda inteligente para: '{institucion_buscada}'")
        print("="*80)
        
        # Generar variaciones con estados
        variaciones_busqueda = self.detectar_y_convertir_estado(institucion_buscada)
        
        # DETECTAR ESTADO ESPECÍFICO EN LA BÚSQUEDA ORIGINAL
        estado_detectado = None
        abreviacion_esperada = None
        
        for estado_completo, abreviacion in self.estados_mexico.items():
            if estado_completo in institucion_buscada.lower():
                estado_detectado = estado_completo
                abreviacion_esperada = abreviacion
                print(f"🎯 ESTADO DETECTADO: '{estado_completo}' -> Abreviación esperada: '{abreviacion}'")
                break
        
        # Estrategias para encontrar las opciones del bootstrap-select
        opciones_estrategias = [
            (By.CSS_SELECTOR, ".bootstrap-select .dropdown-menu li a"),
            (By.CSS_SELECTOR, ".dropdown-menu li a span.text"),
            (By.CSS_SELECTOR, ".bootstrap-select .dropdown-menu a"),
            (By.CSS_SELECTOR, ".open .dropdown-menu li"),
            (By.XPATH, "//div[contains(@class, 'bootstrap-select')]//ul//li//a"),
            (By.XPATH, "//ul[contains(@class, 'dropdown-menu')]//li//a")
        ]
        
        todas_opciones = []
        opciones_elementos = []
        
        # Recopilar todas las opciones disponibles
        for estrategia in opciones_estrategias:
            try:
                opciones = wait.until(EC.presence_of_all_elements_located(estrategia))
                print(f"📝 Encontradas {len(opciones)} opciones")
                
                for opcion in opciones:
                    try:
                        texto_opcion = opcion.text.strip()
                        if not texto_opcion:
                            try:
                                span_texto = opcion.find_element(By.CSS_SELECTOR, "span.text")
                                texto_opcion = span_texto.text.strip()
                            except:
                                continue
                        
                        if texto_opcion and len(texto_opcion) > 3:
                            todas_opciones.append(texto_opcion)
                            opciones_elementos.append(opcion)
                            
                    except Exception:
                        continue
                
                if todas_opciones:
                    break
                    
            except Exception as e:
                print(f"⚠️ Error con estrategia: {e}")
                continue
        
        if not todas_opciones:
            print("❌ No se encontraron opciones en el dropdown")
            return None, None, 0
        
        print(f"📊 Total opciones: {len(set(todas_opciones))}")
        
        # NUEVA LÓGICA: PRIORIZAR POR ESTADO DETECTADO
        if estado_detectado and abreviacion_esperada:
            print(f"\n🎯 BÚSQUEDA PRIORITARIA POR ESTADO: {estado_detectado.upper()} ({abreviacion_esperada})")
            print("="*80)
            
            # Buscar opciones que empiecen con la abreviación esperada
            opciones_estado_correcto = []
            opciones_estado_incorrecto = []
            opciones_sin_estado = []
            
            for i, texto_opcion in enumerate(todas_opciones):
                # Verificar si empieza con abreviación de estado
                if re.match(r'^[A-Z]{2}\s*-', texto_opcion):
                    abrev_en_opcion = texto_opcion[:2]
                    
                    if abrev_en_opcion == abreviacion_esperada:
                        # OPCIONES CON EL ESTADO CORRECTO (MÁXIMA PRIORIDAD)
                        similitud = fuzz.ratio(institucion_buscada.lower(), texto_opcion.lower())
                        opciones_estado_correcto.append((opciones_elementos[i], texto_opcion, similitud))
                        print(f"   🎯 ESTADO CORRECTO: '{texto_opcion}' (similitud: {similitud}%)")
                    else:
                        # Opciones con otro estado (baja prioridad)
                        similitud = fuzz.ratio(institucion_buscada.lower(), texto_opcion.lower())
                        opciones_estado_incorrecto.append((opciones_elementos[i], texto_opcion, similitud))
                        print(f"   ⚠️ Estado incorrecto ({abrev_en_opcion}): '{texto_opcion}' (similitud: {similitud}%)")
                else:
                    # Opciones sin estado
                    similitud = fuzz.ratio(institucion_buscada.lower(), texto_opcion.lower())
                    opciones_sin_estado.append((opciones_elementos[i], texto_opcion, similitud))
            
            # EVALUAR OPCIONES CON EL ESTADO CORRECTO PRIMERO
            if opciones_estado_correcto:
                print(f"\n✅ ENCONTRADAS {len(opciones_estado_correcto)} OPCIONES CON ESTADO CORRECTO ({abreviacion_esperada})")
                
                # Ordenar por similitud
                opciones_estado_correcto.sort(key=lambda x: x[2], reverse=True)
                
                # Mostrar las mejores opciones del estado correcto
                print("🏆 TOP OPCIONES DEL ESTADO CORRECTO:")
                for j, (elemento, texto, similitud) in enumerate(opciones_estado_correcto[:3]):
                    print(f"   {j+1}. '{texto}' (similitud: {similitud}%)")
                
                # Si la mejor opción del estado correcto tiene similitud decente, usarla
                mejor_elemento, mejor_texto, mejor_similitud = opciones_estado_correcto[0]
                
                if mejor_similitud >= 40:  # Umbral más bajo para estado correcto
                    print(f"\n🎉 SELECCIONANDO OPCIÓN DEL ESTADO CORRECTO:")
                    print(f"   📝 Buscado: '{institucion_buscada}'")
                    print(f"   ✅ Encontrado: '{mejor_texto}'")
                    print(f"   📊 Similitud: {mejor_similitud}%")
                    print(f"   🎯 Estado: {abreviacion_esperada} (CORRECTO)")
                    print("="*80)
                    return mejor_elemento, mejor_texto, mejor_similitud
                else:
                    print(f"⚠️ Similitud muy baja en estado correcto: {mejor_similitud}%")
            
            # Si no hay buenas opciones con el estado correcto, mostrar advertencia
            if opciones_estado_incorrecto:
                print(f"\n⚠️ ADVERTENCIA: Se encontraron opciones con otros estados:")
                opciones_estado_incorrecto.sort(key=lambda x: x[2], reverse=True)
                for j, (elemento, texto, similitud) in enumerate(opciones_estado_incorrecto[:3]):
                    estado_inc = texto[:2]
                    print(f"   {j+1}. '{texto}' (similitud: {similitud}%, estado: {estado_inc})")
                
                print(f"❌ ESTAS OPCIONES NO COINCIDEN CON EL ESTADO BUSCADO: {abreviacion_esperada}")
        
        # BÚSQUEDA NORMAL (si no hay estado detectado o no hay opciones del estado correcto)
        print(f"\n🔍 BÚSQUEDA GENERAL (sin prioridad de estado)")
        print("="*60)
        
        mejor_resultado = None
        mejor_similitud = 0
        
        for variacion in variaciones_busqueda:
            print(f"🔍 Probando variación: '{variacion}'")
            
            # 1. BÚSQUEDA EXACTA
            for j, texto_opcion in enumerate(todas_opciones):
                if variacion.lower() == texto_opcion.lower():
                    print(f"🎉 ¡COINCIDENCIA EXACTA!: '{texto_opcion}'")
                    return opciones_elementos[j], texto_opcion, 100
            
            # 2. FUZZY MATCHING
            try:
                mejor_coincidencia, similitud = process.extractOne(
                    variacion, 
                    todas_opciones, 
                    scorer=fuzz.ratio
                )
                
                if similitud > mejor_similitud:
                    indice = todas_opciones.index(mejor_coincidencia)
                    elemento = opciones_elementos[indice]
                    mejor_resultado = (elemento, mejor_coincidencia, similitud)
                    mejor_similitud = similitud
                    print(f"   🔬 Nueva mejor similitud: {similitud}% - '{mejor_coincidencia}'")
                    
            except Exception as e:
                continue
        
        # RESULTADO FINAL
        if mejor_resultado and mejor_similitud >= 45:
            elemento, texto_encontrado, similitud = mejor_resultado
            print(f"\n🏆 RESULTADO FINAL:")
            print(f"   📝 Buscado: '{institucion_buscada}'")
            print(f"   ✅ Encontrado: '{texto_encontrado}'")
            print(f"   📊 Similitud: {similitud}%")
            
            # Advertencia si se detectó un estado pero se eligió otra opción
            if estado_detectado:
                if not texto_encontrado.startswith(abreviacion_esperada):
                    print(f"   ⚠️ ADVERTENCIA: Se detectó estado '{estado_detectado}' ({abreviacion_esperada}) pero se eligió una opción diferente")
                    print(f"   ⚠️ Verificar si '{texto_encontrado}' es realmente la institución correcta")
            
            print("="*80)
            return elemento, texto_encontrado, similitud
        else:
            print(f"❌ No se encontró coincidencia aceptable")
            print("="*80)
            return None, None, 0

    def buscar_contactos_instituciones(self, institucion: str, headless: bool = False):
        """Busca contactos de una institución específica - CÓDIGO COMPLETO."""
        
        print(f"🔍 Iniciando búsqueda para: {institucion}")
        
        driver = self.crear_driver_anti_deteccion(headless)
        
        try:
            # Configurar wait al inicio
            wait = WebDriverWait(driver, 20)
            
            # Navegar directamente a la página
            print("📄 Navegando a la página...")
            driver.get("https://consultapublicamx.plataformadetransparencia.org.mx/vut-web/faces/view/consultaPublica.xhtml")
            
            # Espera corta para que cargue la página
            print("⏳ Esperando que cargue la página...")
            time.sleep(5)
            
            # Verificar y esperar a que desaparezcan las capas bloqueadoras
            print("🔍 Verificando capas bloqueadoras...")
            try:
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".capaBloqueaPantalla")))
                print("✅ Capa bloqueadora removida")
            except:
                print("⚠️ No se detectó capa bloqueadora o ya fue removida")
            
            time.sleep(3)
            print("✅ Página cargada correctamente")
            
            # Buscar el dropdown bootstrap-select de institución
            print("🏢 Buscando dropdown de institución...")
            
            dropdown_estrategias = [
                (By.CSS_SELECTOR, "button[data-id='formEntidadFederativa:cboSujetoObligado']"),
                (By.CSS_SELECTOR, ".bootstrap-select button.dropdown-toggle"),
                (By.CSS_SELECTOR, ".institucionCompartida button"),
                (By.CSS_SELECTOR, "#filaIntitucion .bootstrap-select button"),
                (By.XPATH, "//button[@data-id='formEntidadFederativa:cboSujetoObligado']"),
                (By.XPATH, "//div[@class='btn-group bootstrap-select institucionCompartida']//button")
            ]
            
            dropdown_button = None
            for estrategia in dropdown_estrategias:
                try:
                    dropdown_button = wait.until(EC.presence_of_element_located(estrategia))
                    print(f"✅ Dropdown encontrado")
                    break
                except:
                    continue
            
            if not dropdown_button:
                print("❌ No se pudo encontrar el dropdown de institución")
                return pd.DataFrame()
            
            # Verificar elementos bloqueadores
            print("🔍 Verificando elementos bloqueadores...")
            try:
                bloqueadores = [".capaBloqueaPantalla", ".loading-overlay", ".modal-backdrop", ".overlay"]
                for selector in bloqueadores:
                    try:
                        elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                        for elemento in elementos:
                            if elemento.is_displayed():
                                driver.execute_script("arguments[0].style.display = 'none';", elemento)
                    except:
                        continue
            except:
                pass
            
            # Hacer scroll al elemento
            print("📍 Haciendo scroll al dropdown...")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", dropdown_button)
            time.sleep(2)
            
            # Abrir dropdown con múltiples estrategias
            print("📋 Intentando abrir dropdown...")
            click_exitoso = False
            
            try:
                dropdown_button.click()
                click_exitoso = True
                print("✅ Dropdown abierto con clic normal")
            except Exception as e:
                print(f"⚠️ Clic normal falló: {e}")
            
            if not click_exitoso:
                try:
                    driver.execute_script("arguments[0].click();", dropdown_button)
                    click_exitoso = True
                    print("✅ Dropdown abierto con JavaScript")
                except Exception as e:
                    print(f"⚠️ JavaScript click falló: {e}")
            
            if not click_exitoso:
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(dropdown_button).click().perform()
                    click_exitoso = True
                    print("✅ Dropdown abierto con ActionChains")
                except Exception as e:
                    print(f"⚠️ ActionChains falló: {e}")
            
            if not click_exitoso:
                print("❌ No se pudo abrir el dropdown")
                return pd.DataFrame()
            
            time.sleep(3)
            
            # BÚSQUEDA INTELIGENTE CON ESTADOS CORREGIDA
            print(f"\n🎯 BÚSQUEDA INTELIGENTE CON PRIORIDAD DE ESTADO")
            print("="*80)
            
            opcion_elemento, texto_encontrado, similitud = self.encontrar_opcion_mas_similar(
                driver, wait, institucion
            )
            
            if not opcion_elemento:
                print("❌ No se encontró ninguna opción similar")
                try:
                    dropdown_button.click()
                except:
                    pass
                return pd.DataFrame()
            
            print(f"\n🎉 SELECCIONANDO:")
            print(f"   📝 Búsqueda: '{institucion}'")
            print(f"   ✅ Encontrado: '{texto_encontrado}'")
            print(f"   📊 Similitud: {similitud}%")
            print("="*80)
            
            # Seleccionar la opción encontrada
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", opcion_elemento)
                time.sleep(1)
                opcion_elemento.click()
                print("✅ Opción seleccionada exitosamente")
            except Exception as e:
                print(f"⚠️ Error haciendo clic: {e}")
                try:
                    driver.execute_script("arguments[0].click();", opcion_elemento)
                    print("✅ Opción seleccionada con JavaScript")
                except Exception as e2:
                    print(f"❌ Error total: {e2}")
                    return pd.DataFrame()
            
            print("✅ Institución seleccionada correctamente")
            print("⏳ Esperando 15 segundos a que se actualice la página...")
            time.sleep(15)
            
            # Buscar directorio
            print("📞 Buscando botón de DIRECTORIO...")
            try:
                print("🔍 Esperando contenedor de obligaciones...")
                wait.until(EC.presence_of_element_located((By.ID, "cpListaObligacionesTransparencia")))
                time.sleep(2)
                
                directorio_estrategias = [
                    (By.XPATH, "//div[@id='cpListaObligacionesTransparencia']//label[contains(@class, 'grid6Obligaciones')]//div[contains(@class, 'tituloObligacion')]//label[text()='DIRECTORIO']/ancestor::label"),
                    (By.XPATH, "//label[contains(@class, 'grid6Obligaciones') and .//label[text()='DIRECTORIO']]"),
                    (By.XPATH, "//div[@id='cpListaObligacionesTransparencia']//div[@class='tituloObligacion']//label[text()='DIRECTORIO']/ancestor::label"),
                    (By.XPATH, "//div[@data-original-title='DIRECTORIO']/ancestor::label"),
                    (By.XPATH, "//label[contains(@onclick, 'seleccionObligacion') and .//label[text()='DIRECTORIO']]"),
                    (By.CSS_SELECTOR, "#cpListaObligacionesTransparencia label.grid6Obligaciones"),
                    (By.XPATH, "//div[@id='cpListaObligacionesTransparencia']//*[contains(text(), 'DIRECTORIO')]"),
                ]
                
                directorio_encontrado = False
                enlace_directorio = None
                
                for i, estrategia in enumerate(directorio_estrategias):
                    try:
                        print(f"🔍 Probando estrategia {i+1}")
                        
                        if i == 5:  # CSS que puede devolver múltiples elementos
                            elementos = driver.find_elements(*estrategia)
                            for elemento in elementos:
                                if "DIRECTORIO" in elemento.text:
                                    enlace_directorio = elemento
                                    break
                        else:
                            enlace_directorio = wait.until(EC.element_to_be_clickable(estrategia))
                        
                        if enlace_directorio:
                            print(f"✅ Botón de directorio encontrado")
                            
                            # Hacer scroll al elemento
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", enlace_directorio)
                            time.sleep(2)
                            
                            # Intentar hacer clic
                            try:
                                enlace_directorio.click()
                                directorio_encontrado = True
                                print("✅ Botón de directorio clickeado exitosamente")
                                break
                            except Exception as e:
                                print(f"⚠️ Error en clic normal: {e}")
                                try:
                                    driver.execute_script("arguments[0].click();", enlace_directorio)
                                    directorio_encontrado = True
                                    print("✅ Botón clickeado con JavaScript")
                                    break
                                except Exception as e2:
                                    print(f"⚠️ Error en JavaScript: {e2}")
                                    try:
                                        onclick_attr = enlace_directorio.get_attribute("onclick")
                                        if onclick_attr:
                                            driver.execute_script(onclick_attr)
                                            directorio_encontrado = True
                                            print("✅ Evento onclick ejecutado")
                                            break
                                    except Exception as e3:
                                        print(f"⚠️ Error ejecutando onclick: {e3}")
                                        continue
                        
                    except Exception as e:
                        print(f"⚠️ Estrategia {i+1} falló: {e}")
                        continue
                
                if not directorio_encontrado:
                    print("❌ No se encontró el botón del directorio")
                    return pd.DataFrame()
                    
            except Exception as e:
                print(f"❌ Error buscando directorio: {e}")
                return pd.DataFrame()
            
            # Esperar a que cargue el directorio
            print("⏳ Esperando que cargue el directorio (30 segundos)...")
            time.sleep(30)
            
            print("\n🎉 ¡Directorio cargado exitosamente!")
            
            # Hacer clic en "Ver todos los campos"
            print("👁️ Buscando botón 'Ver todos los campos'...")
            try:
                ver_todos_campos = wait.until(EC.element_to_be_clickable((By.ID, "toggleIrrelevantes")))
                print(f"✅ Botón encontrado")
                
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ver_todos_campos)
                time.sleep(2)
                
                try:
                    ver_todos_campos.click()
                    print("✅ Clic exitoso en 'Ver todos los campos'")
                except Exception as e:
                    print(f"⚠️ Error en clic normal: {e}")
                    try:
                        driver.execute_script("arguments[0].click();", ver_todos_campos)
                        print("✅ Clic exitoso con JavaScript")
                    except Exception as e2:
                        print(f"⚠️ Error en JavaScript: {e2}")
                        try:
                            driver.execute_script("ocultaMostrar(); cambiarTexto();")
                            print("✅ Funciones ejecutadas directamente")
                        except Exception as e3:
                            print(f"⚠️ Error ejecutando funciones: {e3}")
                
                print("⏳ Esperando que se muestren todos los campos...")
                time.sleep(5)
                
            except Exception as e:
                print(f"⚠️ No se pudo hacer clic en 'Ver todos los campos': {e}")
                print("🔄 Continuando con extracción...")
            
            # Extraer tabla del directorio
            print("📊 Extrayendo tabla del directorio...")
            tabla_df = pd.DataFrame()
            
            try:
                print("🔍 Buscando contenedor integraInformacion_wrapper...")
                contenedor_tabla = wait.until(EC.presence_of_element_located((By.ID, "integraInformacion_wrapper")))
                print("✅ Contenedor encontrado")
                
                print("🔍 Buscando estructura DataTables...")
                
                # 1. Obtener headers
                headers = []
                try:
                    tabla_headers = contenedor_tabla.find_element(By.CSS_SELECTOR, "table.integraInformacion.consultaHeader.dataTable.no-footer")
                    thead_element = tabla_headers.find_element(By.TAG_NAME, "thead")
                    headers_elementos = thead_element.find_elements(By.CSS_SELECTOR, "td")
                    
                    ejercicio_encontrado = False
                    for td in headers_elementos:
                        try:
                            span_element = td.find_element(By.CSS_SELECTOR, "span[data-original-title]")
                            header_text = span_element.get_attribute("data-original-title").strip()
                            
                            if not header_text:
                                header_text = span_element.text.strip()
                                
                        except:
                            header_text = td.text.strip()
                        
                        # Empezar desde "Ejercicio"
                        if header_text == "Ejercicio":
                            ejercicio_encontrado = True
                        
                        if ejercicio_encontrado and header_text:
                            headers.append(header_text)
                    
                    print(f"📋 Headers extraídos: {len(headers)} columnas")
                    
                except Exception as e:
                    print(f"⚠️ Error extrayendo headers: {e}")
                    headers = ["Ejercicio", "Fecha_inicio", "Fecha_termino", "Cargo", "Nombre"]
                
                # 2. Obtener datos
                datos = []
                try:
                    scroll_body = contenedor_tabla.find_element(By.CLASS_NAME, "dataTables_scrollBody")
                    tabla_body = scroll_body.find_element(By.TAG_NAME, "tbody")
                    filas_datos = tabla_body.find_elements(By.TAG_NAME, "tr")
                    
                    print(f"📊 Filas encontradas: {len(filas_datos)}")
                    
                    for i, fila in enumerate(filas_datos):
                        try:
                            celdas = fila.find_elements(By.TAG_NAME, "td")
                            if celdas:
                                # Buscar columna "Ejercicio"
                                inicio_ejercicio = 0
                                for j, celda in enumerate(celdas):
                                    texto_celda = celda.text.strip()
                                    if texto_celda == "2025":
                                        inicio_ejercicio = j
                                        break
                                
                                # Extraer datos desde Ejercicio
                                fila_datos = {}
                                for j in range(inicio_ejercicio, len(celdas)):
                                    if j - inicio_ejercicio < len(headers):
                                        celda = celdas[j]
                                        header_name = headers[j - inicio_ejercicio]
                                        
                                        texto_celda = celda.text.strip()
                                        
                                        if not texto_celda:
                                            try:
                                                span_con_titulo = celda.find_element(By.CSS_SELECTOR, "span[data-original-title]")
                                                texto_celda = span_con_titulo.get_attribute("data-original-title")
                                            except:
                                                pass
                                        
                                        fila_datos[header_name] = texto_celda
                                
                                if any(v for v in fila_datos.values() if v):
                                    datos.append(fila_datos)
                            
                        except Exception as e_fila:
                            print(f"⚠️ Error procesando fila {i}: {e_fila}")
                            continue
                    
                    print(f"📊 Total filas extraídas: {len(datos)}")
                    
                    if datos:
                        tabla_df = pd.DataFrame(datos)
                        print(f"✅ DataFrame creado: {len(tabla_df)} filas, {len(tabla_df.columns)} columnas")
                    else:
                        print("❌ No se pudieron extraer datos válidos")
                        
                except Exception as e:
                    print(f"❌ Error extrayendo datos: {e}")
                
                # Mostrar resultados
                if not tabla_df.empty:
                    print("\n" + "="*80)
                    print("📊 DIRECTORIO EXTRAÍDO")
                    print("="*80)
                    print(f"📈 Total registros: {len(tabla_df)}")
                    print(f"📋 Columnas: {list(tabla_df.columns)}")
                    
                    # Verificar ejercicios
                    if 'Ejercicio' in tabla_df.columns:
                        ejercicios_unicos = tabla_df['Ejercicio'].unique()
                        print(f"📅 Ejercicios: {list(ejercicios_unicos)}")
                    
                    # Verificar emails
                    email_col = 'Correo electrónico oficial, en su caso'
                    if email_col in tabla_df.columns:
                        emails_no_vacios = tabla_df[email_col].dropna()
                        emails_no_vacios = emails_no_vacios[emails_no_vacios != '']
                        print(f"📧 Emails encontrados: {len(emails_no_vacios)}")
                    
                    print("\n📋 PRIMERAS 5 FILAS:")
                    print("-" * 80)
                    print(tabla_df.head().to_string(index=False))
                    
                    print("\n" + "="*80)
                    
                    # Guardar CSV
                    institucion_clean = texto_encontrado.replace(' ', '_').replace('/', '_').lower()
                    filename = os.path.join(self.download_path, f"directorio_{institucion_clean}.csv")
                    tabla_df.to_csv(filename, index=False, encoding='utf-8')
                    print(f"💾 Directorio guardado en: {filename}")
                    
                    # Estadísticas
                    print(f"\n📈 === ESTADÍSTICAS ===")
                    for col in tabla_df.columns:
                        no_vacios = tabla_df[col].notna().sum()
                        print(f"📌 {col}: {no_vacios} registros con datos")
                    
                    print("\n🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
                    print("="*60)
                    print(f"✅ Búsqueda: {institucion}")
                    print(f"✅ Encontrado: {texto_encontrado}")
                    print(f"📊 Similitud: {similitud}%")
                    print(f"📊 Registros: {len(tabla_df)}")
                    print(f"💾 Archivo: {filename}")
                    print("="*60)
                    return tabla_df
                        
                else:
                    print("❌ No se pudo extraer datos de la tabla")
                    return pd.DataFrame()
                    
            except Exception as e:
                print(f"❌ Error extrayendo tabla: {e}")
                return pd.DataFrame()
        
        finally:
            driver.quit()

    def investigar(self, nombre_entidad):
        """Método principal que integra todo"""
        try:
            print(f"[AGENTE TRANSPARENCIA] Iniciando para: {nombre_entidad}")
            
            # Usar el código completo
            tabla_df = self.buscar_contactos_instituciones(nombre_entidad, headless=False)
            
            if not tabla_df.empty:
                # Contar emails válidos
                email_cols = [col for col in tabla_df.columns if 'correo' in col.lower() or 'email' in col.lower()]
                total_emails = 0
                for col in email_cols:
                    emails_validos = tabla_df[col].dropna()
                    emails_validos = emails_validos[emails_validos != '']
                    total_emails += len(emails_validos)
                
                institucion_clean = nombre_entidad.replace(' ', '_').replace('/', '_').lower()
                archivo_path = os.path.join(self.download_path, f"directorio_{institucion_clean}.csv")
                
                return {
                    'exito': True,
                    'error': None,
                    'institucion_validada': nombre_entidad,
                    'similitud': 100,
                    'archivo_descargado': True,
                    'ruta_archivo': archivo_path,
                    'total_registros': len(tabla_df),
                    'total_emails': total_emails,
                    'columnas': list(tabla_df.columns)
                }
            else:
                return {
                    'exito': False,
                    'error': 'No se pudieron extraer datos del directorio',
                    'institucion_validada': nombre_entidad,
                    'similitud': 0,
                    'archivo_descargado': False,
                    'ruta_archivo': None
                }
                
        except Exception as e:
            return {
                'exito': False,
                'error': str(e),
                'institucion_validada': None,
                'similitud': 0,
                'archivo_descargado': False,
                'ruta_archivo': None
            }