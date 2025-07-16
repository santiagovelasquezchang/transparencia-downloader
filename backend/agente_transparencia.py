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
from ollama_filter import OllamaContactFilter

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
        
        # Initialize Ollama contact filter
        self.contact_filter = OllamaContactFilter()
        
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
    
    def set_download_path(self, new_path):
        """Actualiza la ruta de descarga"""
        self.download_path = os.path.abspath(new_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
    
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
        """Configuración simple que funcionaba antes"""
        
        options = Options()
        
        # Solo las configuraciones básicas que funcionaban
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        if headless:
            options.add_argument("--headless=new")
        
        # Crear driver simple
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1366, 768)
        
        return driver

    def busqueda_inteligente_estado(self, texto_usuario, opciones_disponibles):
        """Búsqueda flexible por estado y palabras clave"""
        import unicodedata
        
        def normalizar_texto(texto):
            """Normaliza texto removiendo acentos y convirtiendo a minúsculas"""
            texto = unicodedata.normalize('NFD', texto)
            texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
            return texto.lower().strip()
        
        texto_normalizado = normalizar_texto(texto_usuario)
        
        # 1. DETECTAR ESTADO
        estado_detectado = None
        codigo_estado = None
        
        for estado, codigo in self.estados_mexico.items():
            estado_norm = normalizar_texto(estado)
            if estado_norm in texto_normalizado:
                estado_detectado = estado
                codigo_estado = codigo
                break
        
        if not estado_detectado:
            return None, None, []
        
        print(f"🎯 Estado: '{estado_detectado}' -> '{codigo_estado}'")
        
        # 2. EXTRAER PALABRAS CLAVE DEL TEXTO (MÁS FLEXIBLE)
        palabras_importantes = {
            'economia': ['economia', 'economico', 'economica'],
            'educacion': ['educacion', 'educativo', 'educativa'],
            'salud': ['salud', 'sanitario', 'sanitaria'],
            'desarrollo': ['desarrollo'],
            'trabajo': ['trabajo', 'laboral'],
            'turismo': ['turismo', 'turistico', 'turistica'],
            'agricultura': ['agricultura', 'agricola'],
            'planeacion': ['planeacion', 'planeamiento'],
            'finanzas': ['finanzas', 'financiero', 'financiera'],
            'bienestar': ['bienestar'],
            'administracion': ['administracion', 'administrativo', 'administrativa'],
            'seguridad': ['seguridad'],
            'comunicaciones': ['comunicaciones', 'comunicacion'],
            'movilidad': ['movilidad', 'transporte']
        }
        
        palabras_encontradas = []
        for palabra_base, variantes in palabras_importantes.items():
            for variante in variantes:
                if normalizar_texto(variante) in texto_normalizado:
                    if palabra_base not in palabras_encontradas:
                        palabras_encontradas.append(palabra_base)
                    break
        
        if not palabras_encontradas:
            print(f"❌ No se encontraron palabras clave en: '{texto_usuario}'")
            return None, None, []
        
        print(f"🎯 Palabras clave encontradas: {palabras_encontradas}")
        
        # 3. BUSCAR OPCIONES DEL ESTADO CORRECTO
        opciones_estado = []
        
        for opcion in opciones_disponibles:
            if opcion.startswith(codigo_estado + " - "):
                opciones_estado.append(opcion)
        
        print(f"📊 Opciones encontradas para {codigo_estado}: {len(opciones_estado)}")
        
        # 4. LÓGICA SIMPLE: Si solo hay 1 opción, esa es la correcta
        if len(opciones_estado) == 1:
            print(f"✅ Única opción encontrada: '{opciones_estado[0]}'")
            return estado_detectado, codigo_estado, [(opciones_estado[0], 100)]
        
        # 5. Si hay múltiples opciones, filtrar por palabras clave
        coincidencias = []
        
        for opcion in opciones_estado:
            opcion_norm = normalizar_texto(opcion)
            
            # Contar palabras clave que coinciden
            coincidencias_palabras = 0
            for palabra in palabras_encontradas:
                if palabra in opcion_norm:
                    coincidencias_palabras += 1
            
            # Si coincide al menos una palabra clave
            if coincidencias_palabras > 0:
                # Similitud base + bonus por palabras
                similitud_base = fuzz.token_sort_ratio(texto_normalizado, opcion_norm)
                bonus = coincidencias_palabras * 25
                similitud_final = min(100, similitud_base + bonus)
                
                coincidencias.append((opcion, similitud_final))
                print(f"   ✅ '{opcion}' -> {similitud_final}%")
        
        # 6. Si no hay coincidencias por palabras clave, tomar la más similar
        if not coincidencias and opciones_estado:
            print(f"⚠️ No hay coincidencias por palabras clave, usando similitud general")
            for opcion in opciones_estado:
                similitud = fuzz.token_sort_ratio(texto_normalizado, normalizar_texto(opcion))
                if similitud >= 40:  # Umbral muy bajo para casos parciales
                    coincidencias.append((opcion, similitud))
                    print(f"   🔄 '{opcion}' -> {similitud}%")
        
        # 7. ORDENAR por similitud
        coincidencias.sort(key=lambda x: x[1], reverse=True)
        
        return estado_detectado, codigo_estado, coincidencias
    
    # Método eliminado - No funciona correctamente
    
    # Método eliminado - No funciona correctamente
    
    # Método eliminado - No funciona correctamente
    
    def extraer_palabras_principales(self, texto):
        """Extrae palabras clave del texto"""
        palabras = ['economia', 'educacion', 'salud', 'desarrollo', 'trabajo', 'turismo', 
                   'agricultura', 'planeacion', 'finanzas', 'bienestar', 'administracion']
        
        texto_lower = texto.lower()
        encontradas = []
        
        for palabra in palabras:
            if palabra in texto_lower:
                encontradas.append(palabra)
        
        return encontradas
    
    def encontrar_opcion_mas_similar(self, driver, wait, institucion_buscada):
        """Función tradicional como fallback"""
        print(f"🔍 Búsqueda tradicional para: '{institucion_buscada}'")
        print("="*80)
        
        # Obtener todas las opciones del dropdown
        todas_opciones = []
        opciones_elementos = []
        
        try:
            opciones = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".bootstrap-select .dropdown-menu li a")))
            
            for opcion in opciones:
                try:
                    texto_opcion = opcion.text.strip()
                    if texto_opcion and len(texto_opcion) > 3:
                        todas_opciones.append(texto_opcion)
                        opciones_elementos.append(opcion)
                except:
                    continue
                    
        except Exception as e:
            print(f"❌ Error obteniendo opciones: {e}")
            return None, None, 0
        
        if not todas_opciones:
            return None, None, 0
        
        # USAR BÚSQUEDA INTELIGENTE
        estado, codigo, coincidencias = self.busqueda_inteligente_estado(institucion_buscada, todas_opciones)
        
        if not coincidencias:
            print("❌ No se encontraron coincidencias")
            return None, None, 0
        
        # Mostrar resultados
        print(f"🏆 COINCIDENCIAS ENCONTRADAS ({len(coincidencias)}):")
        for i, (opcion, similitud) in enumerate(coincidencias[:5]):
            print(f"   {i+1}. '{opcion}' ({similitud:.1f}%)")
        
        # Seleccionar la mejor opción
        mejor_opcion, mejor_similitud = coincidencias[0]
        
        # Encontrar el elemento correspondiente
        mejor_elemento = None
        for i, texto in enumerate(todas_opciones):
            if texto == mejor_opcion:
                mejor_elemento = opciones_elementos[i]
                break
        
        if mejor_elemento:
            print(f"\n✅ SELECCIONANDO: '{mejor_opcion}' ({mejor_similitud:.1f}%)")
            return mejor_elemento, mejor_opcion, mejor_similitud
        
        return None, None, 0

    def buscar_contactos_instituciones(self, institucion: str, headless: bool = False):
        """Busca contactos de una institución específica - CÓDIGO COMPLETO."""
        
        print(f"🔍 Iniciando búsqueda para: {institucion}")
        
        driver = self.crear_driver_anti_deteccion(headless)
        
        try:
            # Configurar wait al inicio
            wait = WebDriverWait(driver, 20)
            
            # Navegar con comportamiento humano
            print("📄 Navegando a la página...")
            
            # Primero ir a Google para parecer más humano
            driver.get("https://www.google.com")
            time.sleep(2)
            
            # Luego navegar a la página objetivo
            driver.get("https://consultapublicamx.plataformadetransparencia.org.mx/vut-web/faces/view/consultaPublica.xhtml")
            
            # Espera más larga para parecer humano
            print("⏳ Esperando que cargue la página...")
            time.sleep(8)
            
            # Simular movimiento de mouse
            try:
                actions = ActionChains(driver)
                actions.move_by_offset(100, 100).perform()
                time.sleep(1)
                actions.move_by_offset(200, 150).perform()
            except:
                pass
            
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
            
            # Abrir dropdown con comportamiento humano
            print("📋 Intentando abrir dropdown...")
            click_exitoso = False
            
            # Simular hover antes del clic
            try:
                actions = ActionChains(driver)
                actions.move_to_element(dropdown_button).perform()
                time.sleep(1)
                
                # Clic con pausa humana
                dropdown_button.click()
                click_exitoso = True
                print("✅ Dropdown abierto con clic normal")
                time.sleep(2)  # Pausa humana
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
            
            # BÚSQUEDA TRADICIONAL DIRECTA
            print(f"\n🎯 BÚSQUEDA DE INSTITUCIÓN")
            print("="*80)
            
            # Usar método tradicional directamente
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
            
            # Seleccionar la opción con comportamiento humano
            try:
                # Scroll suave
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", opcion_elemento)
                time.sleep(2)
                
                # Hover antes del clic
                actions = ActionChains(driver)
                actions.move_to_element(opcion_elemento).perform()
                time.sleep(1)
                
                # Clic con pausa
                opcion_elemento.click()
                time.sleep(2)
                print("✅ Opción seleccionada exitosamente")
            except Exception as e:
                print(f"⚠️ Error haciendo clic: {e}")
                try:
                    driver.execute_script("arguments[0].click();", opcion_elemento)
                    time.sleep(2)
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
                    # Estrategias más generales primero
                    (By.XPATH, "//*[contains(text(), 'DIRECTORIO')]"),
                    (By.XPATH, "//div[@id='cpListaObligacionesTransparencia']//*[contains(text(), 'DIRECTORIO')]"),
                    (By.CSS_SELECTOR, "#cpListaObligacionesTransparencia label.grid6Obligaciones"),
                    (By.XPATH, "//div[@data-original-title='DIRECTORIO']/ancestor::label"),
                    # Estrategias originales
                    (By.XPATH, "//div[@id='cpListaObligacionesTransparencia']//label[contains(@class, 'grid6Obligaciones')]//div[contains(@class, 'tituloObligacion')]//label[text()='DIRECTORIO']/ancestor::label"),
                    (By.XPATH, "//label[contains(@class, 'grid6Obligaciones') and .//label[text()='DIRECTORIO']]"),
                    (By.XPATH, "//div[@id='cpListaObligacionesTransparencia']//div[@class='tituloObligacion']//label[text()='DIRECTORIO']/ancestor::label"),
                    (By.XPATH, "//label[contains(@onclick, 'seleccionObligacion') and .//label[text()='DIRECTORIO']]"),
                ]
                
                directorio_encontrado = False
                enlace_directorio = None
                
                for i, estrategia in enumerate(directorio_estrategias):
                    try:
                        print(f"🔍 Probando estrategia {i+1}")
                        
                        if i == 2:  # CSS que puede devolver múltiples elementos
                            elementos = driver.find_elements(*estrategia)
                            for elemento in elementos:
                                if "DIRECTORIO" in elemento.text:
                                    enlace_directorio = elemento
                                    break
                        elif i == 0 or i == 1:  # Estrategia general para cualquier elemento con "DIRECTORIO"
                            elementos = driver.find_elements(*estrategia)
                            print(f"   📊 Encontrados {len(elementos)} elementos con 'DIRECTORIO'")
                            for elemento in elementos:
                                try:
                                    if elemento.is_displayed() and elemento.is_enabled() and "DIRECTORIO" in elemento.text:
                                        enlace_directorio = elemento
                                        break
                                except:
                                    continue
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
            print("⏳ Esperando que cargue el directorio (45 segundos)...")
            time.sleep(45)  # Aumentar tiempo de espera
            
            print("\n🎉 ¡Directorio cargado exitosamente!")
            
            # FORZAR EXPANSIÓN DE TODOS LOS CAMPOS
            print("👁️ Expandiendo todos los campos...")
            
            # Estrategia múltiple para asegurar expansión
            try:
                # 1. Buscar y hacer clic en el botón
                botones_posibles = [
                    (By.ID, "toggleIrrelevantes"),
                    (By.XPATH, "//button[contains(text(), 'Ver todos')]"),
                    (By.XPATH, "//button[contains(text(), 'Mostrar todos')]"),
                    (By.XPATH, "//a[contains(text(), 'Ver todos')]"),
                    (By.CSS_SELECTOR, "button[onclick*='ocultaMostrar']"),
                    (By.CSS_SELECTOR, "a[onclick*='ocultaMostrar']")
                ]
                
                boton_encontrado = False
                for selector in botones_posibles:
                    try:
                        boton = driver.find_element(*selector)
                        driver.execute_script("arguments[0].scrollIntoView(true);", boton)
                        time.sleep(1)
                        
                        # Múltiples métodos de clic
                        for metodo in range(3):
                            try:
                                if metodo == 0:
                                    boton.click()
                                elif metodo == 1:
                                    driver.execute_script("arguments[0].click();", boton)
                                else:
                                    driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", boton)
                                
                                print(f"✅ Botón clickeado (método {metodo + 1})")
                                boton_encontrado = True
                                break
                            except:
                                continue
                        
                        if boton_encontrado:
                            break
                            
                    except:
                        continue
                
                # 2. Ejecutar funciones JavaScript directamente
                print("🔧 Ejecutando funciones JavaScript...")
                scripts_expansion = [
                    "if(typeof ocultaMostrar === 'function') { ocultaMostrar(); }",
                    "if(typeof cambiarTexto === 'function') { cambiarTexto(); }",
                    "if(typeof mostrarTodos === 'function') { mostrarTodos(); }",
                    "if(typeof toggleIrrelevantes === 'function') { toggleIrrelevantes(); }",
                    "$('#toggleIrrelevantes').click();",
                    "$('button:contains(Ver todos)').click();",
                    "$('.irrelevante').show();",
                    "$('[style*=display:none]').show();"
                ]
                
                for script in scripts_expansion:
                    try:
                        driver.execute_script(script)
                        time.sleep(1)
                    except:
                        continue
                
                # 3. Esperar y verificar expansión
                time.sleep(8)  # Tiempo generoso para que se expandan
                
                # Contar columnas finales
                try:
                    headers_finales = driver.find_elements(By.CSS_SELECTOR, "table.integraInformacion.consultaHeader.dataTable.no-footer thead td")
                    print(f"📊 Columnas visibles: {len(headers_finales)}")
                except:
                    print("⚠️ No se pudieron contar las columnas")
                
                print("✅ Proceso de expansión completado")
                
            except Exception as e:
                print(f"⚠️ Error en expansión: {e}")
            
            # Extraer tabla del directorio
            print("📊 Extrayendo tabla del directorio...")
            tabla_df = pd.DataFrame()
            
            try:
                print("🔍 Buscando contenedor integraInformacion_wrapper...")
                contenedor_tabla = wait.until(EC.presence_of_element_located((By.ID, "integraInformacion_wrapper")))
                print("✅ Contenedor encontrado")
                
                print("🔍 Buscando estructura DataTables...")
                
                # 1. EXTRAER TODOS LOS HEADERS POSIBLES
                headers = []
                try:
                    # Buscar tabla de headers
                    tabla_headers = contenedor_tabla.find_element(By.CSS_SELECTOR, "table.integraInformacion.consultaHeader.dataTable.no-footer")
                    
                    # Obtener TODAS las celdas de header (incluyendo ocultas)
                    headers_elementos = tabla_headers.find_elements(By.CSS_SELECTOR, "thead td, thead th")
                    
                    print(f"🔍 Elementos de header encontrados: {len(headers_elementos)}")
                    
                    for i, td in enumerate(headers_elementos):
                        try:
                            # Múltiples métodos para obtener el texto del header
                            header_text = ""
                            
                            # Método 1: data-original-title
                            try:
                                span_element = td.find_element(By.CSS_SELECTOR, "span[data-original-title]")
                                header_text = span_element.get_attribute("data-original-title")
                            except:
                                pass
                            
                            # Método 2: texto del span
                            if not header_text:
                                try:
                                    span_element = td.find_element(By.TAG_NAME, "span")
                                    header_text = span_element.text
                                except:
                                    pass
                            
                            # Método 3: texto directo del td
                            if not header_text:
                                header_text = td.text
                            
                            # Método 4: innerHTML si está vacío
                            if not header_text:
                                header_text = driver.execute_script("return arguments[0].innerHTML;", td)
                                # Limpiar HTML tags
                                import re
                                header_text = re.sub(r'<[^>]+>', '', header_text)
                            
                            header_text = header_text.strip()
                            
                            if header_text:
                                headers.append(header_text)
                                print(f"   📋 Header {i+1}: '{header_text}'")
                            else:
                                # Agregar placeholder para columnas vacías
                                headers.append(f"Columna_{i+1}")
                                print(f"   📋 Header {i+1}: 'Columna_{i+1}' (placeholder)")
                                
                        except Exception as e:
                            # Agregar placeholder en caso de error
                            headers.append(f"Columna_{i+1}")
                            print(f"   ⚠️ Error en header {i+1}: {e}")
                    
                    print(f"📊 Total headers extraídos: {len(headers)}")
                    
                except Exception as e:
                    print(f"❌ Error extrayendo headers: {e}")
                    # Headers mínimos como fallback
                    headers = ["Ejercicio", "Fecha_inicio", "Fecha_termino", "Cargo", "Nombre", "Email", "Telefono"]
                
                # 2. Obtener datos
                datos = []
                try:
                    scroll_body = contenedor_tabla.find_element(By.CLASS_NAME, "dataTables_scrollBody")
                    tabla_body = scroll_body.find_element(By.TAG_NAME, "tbody")
                    filas_datos = tabla_body.find_elements(By.TAG_NAME, "tr")
                    
                    print(f"📊 Filas encontradas: {len(filas_datos)}")
                    
                    for i, fila in enumerate(filas_datos):
                        try:
                            # Obtener TODAS las celdas (incluyendo ocultas)
                            celdas = fila.find_elements(By.CSS_SELECTOR, "td, th")
                            
                            if celdas:
                                fila_datos = {}
                                
                                # Procesar TODAS las celdas disponibles
                                for j, celda in enumerate(celdas):
                                    # Asegurar que tenemos un header para esta columna
                                    if j < len(headers):
                                        header_name = headers[j]
                                    else:
                                        header_name = f"Columna_{j+1}"
                                        headers.append(header_name)  # Agregar header dinámicamente
                                    
                                    # Usar método mejorado para extraer texto completo
                                    texto_celda = self.extraer_texto_completo_celda(driver, celda)
                                    
                                    # CORREGIR CODIFICACIÓN DE CARACTERES
                                    if texto_celda:
                                        texto_celda = self.corregir_codificacion(texto_celda.strip())
                                    
                                    fila_datos[header_name] = texto_celda if texto_celda else ""
                                
                                # Agregar fila si tiene algún contenido
                                if any(v.strip() for v in fila_datos.values() if v):
                                    datos.append(fila_datos)
                                    
                                    # Log cada 10 filas para mostrar progreso
                                    if (i + 1) % 10 == 0:
                                        print(f"   📊 Procesadas {i + 1} filas...")
                            
                        except Exception as e_fila:
                            print(f"⚠️ Error procesando fila {i}: {e_fila}")
                            continue
                    
                    print(f"📊 Total filas extraídas: {len(datos)}")
                    
                    if datos:
                        # Crear DataFrame con todos los datos
                        tabla_df = pd.DataFrame(datos)
                        
                        # Rellenar columnas faltantes con valores vacíos
                        for header in headers:
                            if header not in tabla_df.columns:
                                tabla_df[header] = ""
                        
                        # Reordenar columnas según el orden de headers
                        tabla_df = tabla_df.reindex(columns=headers, fill_value="")
                        
                        print(f"✅ DataFrame completo: {len(tabla_df)} filas, {len(tabla_df.columns)} columnas")
                        print(f"📋 Columnas finales: {list(tabla_df.columns)}")
                        
                        # Mostrar estadísticas de contenido
                        for col in tabla_df.columns:
                            no_vacios = tabla_df[col].astype(str).str.strip().ne('').sum()
                            if no_vacios > 0:
                                print(f"   📊 {col}: {no_vacios} registros con datos")
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
                    print(f"📋 Total columnas: {len(tabla_df.columns)}")
                    print(f"📋 Columnas extraídas: {list(tabla_df.columns)[:10]}{'...' if len(tabla_df.columns) > 10 else ''}")
                    
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
                    
                    # Apply Ollama filtering before saving
                    print("🤖 Applying Ollama-based filtering...")
                    try:
                        filtered_df = self.contact_filter.filter_contacts_batch(tabla_df)
                        
                        # Save filtered results
                        institucion_clean = texto_encontrado.replace(' ', '_').replace('/', '_').lower()
                        filename = os.path.join(self.download_path, f"directorio_filtered_{institucion_clean}.csv")
                        filtered_df.to_csv(filename, index=False, encoding='utf-8-sig')
                        
                        print(f"✅ Original: {len(tabla_df)} contacts")
                        print(f"✅ Filtered: {len(filtered_df)} contacts") 
                        print(f"💾 Filtered data saved: {filename}")
                        
                        # Update tabla_df to filtered version for return
                        tabla_df = filtered_df
                        
                    except Exception as filter_error:
                        print(f"⚠️ Error applying filter: {filter_error}")
                        print("⚠️ Saving unfiltered data as fallback...")
                        
                        # Fallback: save unfiltered data
                        institucion_clean = texto_encontrado.replace(' ', '_').replace('/', '_').lower()
                        filename = os.path.join(self.download_path, f"directorio_{institucion_clean}.csv")
                        tabla_df.to_csv(filename, index=False, encoding='utf-8-sig')
                        print(f"💾 Unfiltered data saved: {filename}")
                    
                    # Estadísticas detalladas
                    print(f"\n📈 === ESTADÍSTICAS COMPLETAS ===")
                    print(f"📊 Total columnas extraídas: {len(tabla_df.columns)}")
                    print(f"📊 Total filas extraídas: {len(tabla_df)}")
                    
                    # Mostrar solo columnas con datos
                    columnas_con_datos = []
                    for col in tabla_df.columns:
                        no_vacios = tabla_df[col].astype(str).str.strip().ne('').sum()
                        if no_vacios > 0:
                            columnas_con_datos.append((col, no_vacios))
                    
                    print(f"📊 Columnas con datos: {len(columnas_con_datos)}")
                    for col, cantidad in columnas_con_datos:
                        print(f"   📌 {col}: {cantidad} registros")
                    
                    print("\n🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
                    print("="*60)
                    print(f"✅ Búsqueda: {institucion}")
                    print(f"✅ Encontrado: {texto_encontrado}")
                    print(f"📊 Similitud: {similitud}%")
                    print(f"📊 Registros: {len(tabla_df)}")
                    print(f"📊 Columnas totales: {len(tabla_df.columns)}")
                    print(f"💾 Archivo: {filename}")
                    print(f"✅ EXTRACCIÓN COMPLETA - Todos los campos incluidos")
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
                
                # The tabla_df is now filtered, so update the path to reflect this
                institucion_clean = nombre_entidad.replace(' ', '_').replace('/', '_').lower()
                archivo_path = os.path.join(self.download_path, f"directorio_filtered_{institucion_clean}.csv")
                
                return {
                    'exito': True,
                    'error': None,
                    'institucion_validada': nombre_entidad,
                    'similitud': 100,
                    'archivo_descargado': True,
                    'ruta_archivo': archivo_path,
                    'total_registros': len(tabla_df),  # Now filtered count
                    'total_emails': total_emails,
                    'total_columnas': len(tabla_df.columns),
                    'columnas': list(tabla_df.columns),
                    'filter_efficiency': f"{len(tabla_df)} filtered contacts"
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
    
    def corregir_codificacion(self, texto):
        """Corrige problemas de codificación de caracteres"""
        if not texto:
            return texto
        
        try:
            correcciones = {
                'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
                'Ã±': 'ñ', 'Ã¼': 'ü',
                'RamÃ­rez': 'Ramírez', 'ArgÃ¼elles': 'Argüelles',
                'MartÃ­nez': 'Martínez', 'GonzÃ¡lez': 'González',
                'RodrÃ­guez': 'Rodríguez', 'HernÃ¡ndez': 'Hernández'
            }
            
            texto_corregido = texto
            for incorrecto, correcto in correcciones.items():
                texto_corregido = texto_corregido.replace(incorrecto, correcto)
            
            return texto_corregido
            
        except Exception:
            return texto
    
    def extraer_texto_completo_celda(self, driver, celda):
        """Extrae texto completo de una celda, evitando truncamiento"""
        try:
            # Método 1: data-original-title (texto completo sin truncar)
            try:
                span_con_titulo = celda.find_element(By.CSS_SELECTOR, "span[data-original-title]")
                texto_celda = span_con_titulo.get_attribute("data-original-title")
                if texto_celda and not texto_celda.endswith('...'):
                    return texto_celda
            except:
                pass
            
            # Método 2: title attribute
            try:
                titulo = celda.get_attribute("title")
                if titulo and not titulo.endswith('...'):
                    return titulo
            except:
                pass
            
            # Método 3: textContent completo
            try:
                texto_completo = driver.execute_script("return arguments[0].textContent;", celda)
                if texto_completo and not texto_completo.strip().endswith('...'):
                    return texto_completo.strip()
            except:
                pass
            
            # Método 4: texto directo como último recurso
            texto_directo = celda.text.strip()
            return texto_directo if texto_directo else ""
            
        except Exception as e:
            print(f"⚠️ Error extrayendo texto de celda: {e}")
            return ""
