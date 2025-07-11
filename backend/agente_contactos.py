import os
import logging
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import PyPDF2
import io
from PIL import Image
import pytesseract
import base64

class AgenteContactos:
    def __init__(self, download_path="downloads"):
        self.download_path = os.path.abspath(download_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        
        # Palabras clave específicas para encontrar directorios de empleados
        self.palabras_directorio = [
            'organigrama', 'directorio', 'directorio institucional',
            'funcionarios', 'autoridades', 'personal directivo',
            'estructura organizacional', 'quien es quien',
            'conocenos', 'conozcanos', 'quienes somos',
            'estructura administrativa', 'gobierno',
            'directorio telefonico', 'staff', 'personal',
            'directorio de funcionarios', 'directorio de personal',
            'estructura orgánica', 'servidores públicos'
        ]
        
        # Palabras a evitar (contacto general de la secretaría)
        self.palabras_evitar = [
            'contacto', 'contactanos', 'atencion al publico',
            'tramites', 'servicios', 'quejas', 'sugerencias',
            'contacto general', 'información general',
            'atención ciudadana', 'mesa de ayuda'
        ]
        
        # Patrones de extracción
        self.patron_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.patron_telefono = r'(\(?[0-9]{2,3}\)?[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{4})'
        self.patron_extension = r'(?:ext|extensión|extension)\.?\s*([0-9]{2,5})'
    
    def set_download_path(self, new_path):
        """Actualiza la ruta de descarga"""
        self.download_path = os.path.abspath(new_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        
    def crear_driver_avanzado(self, headless=False):
        """Driver con configuraciones avanzadas"""
        options = Options()
        
        if headless:
            options.add_argument("--headless=new")
        
        # Configuraciones anti-detección
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--exclude-switches=enable-automation")
        options.add_argument("--useAutomationExtension=false")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # User agent realista
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
        
        # Configurar descargas para PDFs
        prefs = {
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True
        }
        options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1366, 768)
        
        # JavaScript anti-detección
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver

    def buscar_pagina_oficial_avanzada(self, nombre_entidad):
        """Búsqueda avanzada con múltiples estrategias"""
        print(f"🔍 Búsqueda avanzada para: {nombre_entidad}")
        
        # Estrategia 1: Selenium + Google
        url_selenium = self.buscar_con_selenium(nombre_entidad)
        if url_selenium:
            return url_selenium
        
        # Estrategia 2: Requests + Google (fallback)
        url_requests = self.buscar_con_requests(nombre_entidad)
        if url_requests:
            return url_requests
        
        return None

    def buscar_con_selenium(self, nombre_entidad):
        """Búsqueda usando Selenium"""
        driver = self.crear_driver_avanzado(headless=False)
        
        try:
            print("📄 Usando Selenium para búsqueda...")
            driver.get("https://www.google.com")
            time.sleep(2)
            
            # Manejar cookies
            try:
                cookie_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Acepto') or contains(text(), 'Accept')]")
                cookie_btn.click()
                time.sleep(1)
            except:
                pass
            
            # Buscar
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Búsqueda simple solo con el nombre de la entidad
            consultas = [
                f'{nombre_entidad}'
            ]
            
            for consulta in consultas:
                print(f"   🔍 Probando: {consulta}")
                
                search_box.clear()
                search_box.send_keys(consulta)
                search_box.send_keys(Keys.RETURN)
                time.sleep(3)
                
                # Tomar el PRIMER resultado (generalmente es el correcto)
                try:
                    resultados = driver.find_elements(By.CSS_SELECTOR, "h3")
                    if resultados:
                        primer_resultado = resultados[0]
                        try:
                            link = primer_resultado.find_element(By.XPATH, "./ancestor::a")
                            url = link.get_attribute("href")
                            titulo = primer_resultado.text
                            
                            print(f"   📋 Primer resultado: '{titulo}'")
                            print(f"   🔗 URL: {url}")
                            
                            # Validar que sea una URL válida
                            if url and not any(x in url for x in ['youtube.com', 'facebook.com', 'twitter.com']):
                                url_limpia = self.limpiar_url_google(url)
                                print(f"   ✅ Seleccionando primer resultado: {url_limpia}")
                                return url_limpia
                                
                        except Exception as e:
                            print(f"   ⚠️ Error procesando primer resultado: {e}")
                            
                    # Si el primer resultado falla, probar los siguientes
                    print("   🔄 Primer resultado falló, probando siguientes...")
                    for i, resultado in enumerate(resultados[1:4], 2):
                        try:
                            link = resultado.find_element(By.XPATH, "./ancestor::a")
                            url = link.get_attribute("href")
                            titulo = resultado.text
                            
                            if self.es_url_relevante(url, titulo, nombre_entidad):
                                url_limpia = self.limpiar_url_google(url)
                                print(f"   ✅ Resultado #{i} seleccionado: {url_limpia}")
                                return url_limpia
                                
                        except Exception:
                            continue
                            
                except Exception as e:
                    print(f"   ❌ Error obteniendo resultados: {e}")
            
            return None
            
        except Exception as e:
            print(f"❌ Error en Selenium: {e}")
            return None
        finally:
            driver.quit()

    def buscar_con_requests(self, nombre_entidad):
        """Búsqueda usando requests como fallback"""
        print("📄 Usando requests como fallback...")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            query = f"{nombre_entidad}"
            url = f"https://www.google.com/search?q={query}"
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar primer enlace válido en resultados
            enlaces_encontrados = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/url?q=' in href:
                    url_real = href.split('/url?q=')[1].split('&')[0]
                    if url_real and not any(x in url_real for x in ['youtube.com', 'facebook.com', 'twitter.com']):
                        enlaces_encontrados.append((url_real, link.text))
            
            # Tomar el primer enlace válido
            if enlaces_encontrados:
                url_real, titulo = enlaces_encontrados[0]
                print(f"   📋 Primer resultado (requests): '{titulo[:50]}...'")
                print(f"   ✅ URL seleccionada: {url_real}")
                return url_real
            
            return None
            
        except Exception as e:
            print(f"❌ Error en requests: {e}")
            return None

    def es_url_relevante(self, url, titulo, nombre_entidad):
        """Evalúa si una URL es relevante"""
        if not url or 'youtube.com' in url or 'facebook.com' in url:
            return False
        
        # Priorizar dominios oficiales
        if '.gob.mx' in url or '.gov.mx' in url:
            return True
        
        # Evaluar similitud del título
        from fuzzywuzzy import fuzz
        similitud = fuzz.partial_ratio(nombre_entidad.lower(), titulo.lower())
        return similitud >= 60

    def limpiar_url_google(self, url):
        """Limpia URLs de Google"""
        if '/url?q=' in url:
            try:
                from urllib.parse import unquote
                return unquote(url.split('/url?q=')[1].split('&')[0])
            except:
                pass
        return url

    def buscar_en_menus_navegacion(self, url_base):
        """Busca enlaces de directorio en menús de navegación con búsqueda ampliada"""
        driver = self.crear_driver_avanzado(headless=True)
        enlaces_encontrados = []
        
        try:
            driver.get(url_base)
            time.sleep(5)
            
            print("🗺️ Analizando menús de navegación...")
            
            # Palabras clave ampliadas para menús
            palabras_menu_ampliadas = [
                'directorio', 'organigrama', 'funcionarios', 'personal', 'autoridades',
                'quienes somos', 'quiénes somos', 'conocenos', 'conócenos', 'equipo',
                'estructura', 'gobierno', 'administracion', 'administración',
                'staff', 'servidores publicos', 'servidores públicos',
                'directorio institucional', 'estructura organizacional',
                'quien es quien', 'quién es quién', 'nosotros', 'acerca de'
            ]
            
            # Selectores de menús más completos
            selectores_menu = [
                "nav a", "#menu a", ".menu a", ".navbar a", ".nav a",
                "#navigation a", ".navigation a", "header a", ".header a",
                ".main-menu a", "#main-menu a", ".top-menu a", "#top-menu a",
                ".menu-item a", ".nav-item a", ".navbar-nav a",
                "ul.menu a", "ul.nav a", ".dropdown-menu a",
                ".site-navigation a", ".primary-navigation a"
            ]
            
            # Buscar en todos los selectores
            for selector in selectores_menu:
                try:
                    enlaces = driver.find_elements(By.CSS_SELECTOR, selector)
                    for enlace in enlaces:
                        try:
                            href = enlace.get_attribute("href")
                            texto = enlace.text.strip().lower()
                            
                            if not href or not texto or len(texto) < 3:
                                continue
                            
                            # Verificar coincidencias con palabras clave ampliadas
                            coincidencias = 0
                            for palabra in palabras_menu_ampliadas:
                                if palabra in texto:
                                    coincidencias += 1
                            
                            if coincidencias > 0:
                                # Convertir a URL absoluta
                                if href.startswith('/'):
                                    href = urljoin(url_base, href)
                                elif not href.startswith('http'):
                                    href = urljoin(url_base, href)
                                
                                tipo = self.determinar_tipo_contenido(href, texto)
                                
                                enlaces_encontrados.append({
                                    'url': href,
                                    'texto': enlace.text.strip(),
                                    'tipo': tipo,
                                    'fuente': 'menu',
                                    'relevancia': coincidencias
                                })
                                
                                print(f"   🗺️ Menú: '{enlace.text.strip()}' -> {href}")
                        except Exception:
                            continue
                except Exception:
                    continue
            
            # Buscar también en dropdowns y submenús
            try:
                # Expandir dropdowns
                dropdowns = driver.find_elements(By.CSS_SELECTOR, ".dropdown, .has-dropdown")
                for dropdown in dropdowns:
                    try:
                        driver.execute_script("arguments[0].click();", dropdown)
                        time.sleep(1)
                    except:
                        pass
                
                # Buscar en elementos expandidos
                enlaces_expandidos = driver.find_elements(By.CSS_SELECTOR, ".dropdown-menu a, .submenu a")
                for enlace in enlaces_expandidos:
                    try:
                        href = enlace.get_attribute("href")
                        texto = enlace.text.strip().lower()
                        
                        if href and texto and any(palabra in texto for palabra in palabras_menu_ampliadas):
                            if href.startswith('/'):
                                href = urljoin(url_base, href)
                            
                            enlaces_encontrados.append({
                                'url': href,
                                'texto': enlace.text.strip(),
                                'tipo': self.determinar_tipo_contenido(href, texto),
                                'fuente': 'submenu',
                                'relevancia': 1
                            })
                            print(f"   🗺️ Submenú: '{enlace.text.strip()}'")
                    except:
                        continue
            except:
                pass
            
            # Ordenar por relevancia
            enlaces_encontrados.sort(key=lambda x: x['relevancia'], reverse=True)
            
            print(f"🗺️ Total enlaces de menú: {len(enlaces_encontrados)}")
            return enlaces_encontrados
            
        except Exception as e:
            print(f"❌ Error navegando menús: {e}")
            return []
        finally:
            driver.quit()
    
    def investigar_directorio_completo(self, url_base, nombre_entidad):
        """Investigación completa de directorio con múltiples formatos"""
        print(f"🌐 Investigación completa en: {url_base}")
        
        contactos_totales = []
        
        # Paso 1: Navegar por menús para encontrar directorio
        print("🗺️ Navegando por menús de la página...")
        enlaces_menu = self.buscar_en_menus_navegacion(url_base)
        
        # Paso 2: Buscar enlaces específicos de directorio en la página
        print("🔗 Buscando enlaces de directorio/organigrama...")
        enlaces_directorio = self.encontrar_enlaces_directorio_avanzado(url_base)
        
        # Combinar y eliminar duplicados
        todos_enlaces = enlaces_menu + enlaces_directorio
        enlaces_unicos = []
        urls_vistas = set()
        for enlace in todos_enlaces:
            if enlace['url'] not in urls_vistas:
                enlaces_unicos.append(enlace)
                urls_vistas.add(enlace['url'])
        
        print(f"📁 Total enlaces únicos: {len(enlaces_unicos)}")
        
        # Paso 3: Explorar enlaces encontrados
        for enlace in enlaces_unicos[:5]:
            print(f"\n📂 Explorando: {enlace['texto']}")
            
            # Si es un enlace de menú que puede tener submenú, expandirlo primero
            if enlace['fuente'] == 'menu' and ('#' in enlace['url'] or enlace['url'] == url_base):
                print(f"   🗺️ Expandiendo menú: {enlace['texto']}")
                contactos_submenu = self.explorar_submenu_directorio(url_base, enlace['texto'])
                contactos_totales.extend(contactos_submenu)
            elif enlace['tipo'] == 'pdf':
                contactos_pdf = self.procesar_pdf_directorio(enlace['url'])
                contactos_totales.extend(contactos_pdf)
            elif enlace['tipo'] == 'imagen':
                contactos_img = self.procesar_imagen_directorio(enlace['url'])
                contactos_totales.extend(contactos_img)
            else:
                contactos_html = self.procesar_pagina_directorio(enlace['url'])
                contactos_totales.extend(contactos_html)
        
        # Paso 4: Fallback a página principal
        if not contactos_totales:
            print("📄 Analizando página principal como fallback...")
            contactos_main = self.analizar_pagina_principal(url_base)
            contactos_totales.extend(contactos_main)
        
        # Procesar contactos
        if contactos_totales:
            df_contactos = self.procesar_contactos_encontrados(contactos_totales, nombre_entidad)
            return df_contactos
        
        return pd.DataFrame()
    
    def explorar_submenu_directorio(self, url_base, texto_menu):
        """Explora submenús para encontrar directorio u organigrama"""
        print(f"🗺️ Explorando submenú de: {texto_menu}")
        
        driver = self.crear_driver_avanzado(headless=True)
        contactos = []
        
        try:
            driver.get(url_base)
            time.sleep(3)
            
            # Buscar el elemento del menú por texto
            menu_elementos = driver.find_elements(By.XPATH, f"//a[contains(text(), '{texto_menu}') or contains(@title, '{texto_menu}')]")
            
            if not menu_elementos:
                # Buscar de forma más flexible
                menu_elementos = driver.find_elements(By.XPATH, f"//*[contains(text(), '{texto_menu.upper()}') or contains(text(), '{texto_menu.lower()}')]")
            
            for menu_elemento in menu_elementos:
                try:
                    print(f"   🔄 Haciendo clic en: {texto_menu}")
                    
                    # Hacer scroll al elemento
                    driver.execute_script("arguments[0].scrollIntoView(true);", menu_elemento)
                    time.sleep(1)
                    
                    # Hacer clic para expandir
                    try:
                        menu_elemento.click()
                    except:
                        driver.execute_script("arguments[0].click();", menu_elemento)
                    
                    time.sleep(2)
                    
                    # Buscar "DIRECTORIO" o "ORGANIGRAMA" en el submenú expandido
                    palabras_objetivo = ['directorio', 'organigrama', 'directorio institucional', 'estructura organizacional']
                    
                    for palabra in palabras_objetivo:
                        # Buscar enlaces que contengan estas palabras
                        enlaces_submenu = driver.find_elements(By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{palabra}')]")
                        
                        for enlace_sub in enlaces_submenu:
                            try:
                                href_sub = enlace_sub.get_attribute('href')
                                texto_sub = enlace_sub.text.strip()
                                
                                if href_sub and texto_sub:
                                    print(f"   ✅ Encontrado en submenú: '{texto_sub}' -> {href_sub}")
                                    
                                    # Convertir a URL absoluta
                                    if href_sub.startswith('/'):
                                        href_sub = urljoin(url_base, href_sub)
                                    
                                    # Procesar el enlace encontrado
                                    if href_sub.endswith('.pdf'):
                                        contactos_pdf = self.procesar_pdf_directorio(href_sub)
                                        contactos.extend(contactos_pdf)
                                    elif any(ext in href_sub.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                                        contactos_img = self.procesar_imagen_directorio(href_sub)
                                        contactos.extend(contactos_img)
                                    else:
                                        contactos_html = self.procesar_pagina_directorio(href_sub)
                                        contactos.extend(contactos_html)
                                    
                                    # Si encontramos algo, no seguir buscando
                                    if contactos:
                                        print(f"   ✅ Contactos encontrados en submenú: {len(contactos)}")
                                        return contactos
                            except Exception:
                                continue
                    
                    break  # Solo probar el primer elemento del menú
                    
                except Exception as e:
                    print(f"   ⚠️ Error expandiendo menú: {e}")
                    continue
            
            if not contactos:
                print(f"   ❌ No se encontraron enlaces de directorio en submenú")
            
        except Exception as e:
            print(f"   ❌ Error explorando submenú: {e}")
        finally:
            driver.quit()
        
        return contactos

    def encontrar_enlaces_directorio_avanzado(self, url_base):
        """Encuentra enlaces de directorio con análisis avanzado"""
        driver = self.crear_driver_avanzado(headless=True)
        enlaces_encontrados = []
        
        try:
            driver.get(url_base)
            time.sleep(5)
            
            # Buscar todos los enlaces
            todos_enlaces = driver.find_elements(By.TAG_NAME, "a")
            
            for enlace in todos_enlaces:
                try:
                    href = enlace.get_attribute("href")
                    texto = enlace.text.strip().lower()
                    
                    if not href or not texto:
                        continue
                    
                    # Evaluar si es enlace de directorio
                    es_directorio = any(palabra in texto for palabra in self.palabras_directorio)
                    es_contacto_general = any(palabra in texto for palabra in self.palabras_evitar)
                    
                    if es_directorio and not es_contacto_general:
                        # Determinar tipo de contenido
                        tipo = self.determinar_tipo_contenido(href, texto)
                        
                        # Convertir a URL absoluta
                        if href.startswith('/'):
                            href = urljoin(url_base, href)
                        
                        enlaces_encontrados.append({
                            'url': href,
                            'texto': enlace.text.strip(),
                            'tipo': tipo,
                            'relevancia': len([p for p in self.palabras_directorio if p in texto])
                        })
                        
                        print(f"   🎯 Encontrado ({tipo}): {texto[:50]}...")
                
                except Exception:
                    continue
            
            # Ordenar por relevancia
            enlaces_encontrados.sort(key=lambda x: x['relevancia'], reverse=True)
            
            print(f"📋 Total enlaces de directorio: {len(enlaces_encontrados)}")
            return enlaces_encontrados
            
        except Exception as e:
            print(f"❌ Error buscando enlaces: {e}")
            return []
        finally:
            driver.quit()

    def determinar_tipo_contenido(self, url, texto):
        """Determina el tipo de contenido del enlace"""
        url_lower = url.lower()
        texto_lower = texto.lower()
        
        if '.pdf' in url_lower or 'pdf' in texto_lower:
            return 'pdf'
        elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            return 'imagen'
        elif 'organigrama' in texto_lower and ('jpg' in texto_lower or 'png' in texto_lower):
            return 'imagen'
        else:
            return 'html'

    def procesar_pdf_directorio(self, url_pdf):
        """Procesa PDFs de organigrama/directorio con extracción mejorada"""
        print(f"📄 Procesando PDF: {url_pdf}")
        contactos = []
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url_pdf, headers=headers, timeout=30)
            
            if response.status_code == 200:
                pdf_file = io.BytesIO(response.content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                print(f"   📄 PDF con {len(pdf_reader.pages)} páginas")
                
                texto_completo = ""
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        texto_pagina = page.extract_text()
                        texto_completo += f"\n--- Página {i+1} ---\n{texto_pagina}\n"
                    except Exception as e:
                        print(f"   ⚠️ Error en página {i+1}: {e}")
                        continue
                
                if texto_completo.strip():
                    # Extraer contactos con patrones mejorados
                    contactos = self.extraer_contactos_pdf_avanzado(texto_completo, url_pdf)
                    print(f"   ✅ PDF procesado: {len(contactos)} contactos extraidos")
                else:
                    print(f"   ⚠️ PDF sin texto extraible (posible imagen)")
                    # Intentar OCR si el PDF es una imagen
                    contactos = self.procesar_pdf_como_imagen(pdf_file, url_pdf)
                
        except Exception as e:
            print(f"   ❌ Error procesando PDF: {e}")
        
        return contactos
    
    def extraer_contactos_pdf_avanzado(self, texto, url_fuente):
        """Extrae contactos de texto PDF con patrones avanzados"""
        contactos = []
        
        # Patrones mejorados
        patron_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        patron_telefono = r'(?:teléfono|tel|phone)?:?\s*([\(]?\d{2,3}[\)]?[\s.-]?\d{3,4}[\s.-]?\d{4})'
        patron_extension = r'(?:ext|extensión|extension)\.?\s*([0-9]{2,5})'
        
        # Dividir en líneas para mejor procesamiento
        lineas = texto.split('\n')
        
        contacto_actual = {'nombre': '', 'cargo': '', 'email': '', 'telefono': '', 'extension': ''}
        
        for i, linea in enumerate(lineas):
            linea = linea.strip()
            if not linea:
                continue
            
            # Buscar emails
            emails = re.findall(patron_email, linea)
            if emails:
                contacto_actual['email'] = emails[0]
            
            # Buscar teléfonos
            telefonos = re.findall(patron_telefono, linea)
            if telefonos:
                contacto_actual['telefono'] = telefonos[0]
            
            # Buscar extensiones
            extensiones = re.findall(patron_extension, linea)
            if extensiones:
                contacto_actual['extension'] = extensiones[0]
            
            # Identificar cargos (líneas con palabras clave de cargos)
            cargos_keywords = ['director', 'coordinador', 'jefe', 'secretario', 'titular', 'responsable']
            if any(cargo in linea.lower() for cargo in cargos_keywords):
                contacto_actual['cargo'] = linea
            
            # Identificar nombres (líneas que parecen nombres)
            elif re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', linea) and len(linea.split()) >= 2:
                contacto_actual['nombre'] = linea
            
            # Si tenemos suficiente información, guardar contacto
            if contacto_actual['email'] or contacto_actual['telefono']:
                if contacto_actual['nombre'] or contacto_actual['cargo']:
                    contactos.append({
                        'nombre': contacto_actual['nombre'],
                        'cargo': contacto_actual['cargo'],
                        'email': contacto_actual['email'],
                        'telefono': contacto_actual['telefono'],
                        'extension': contacto_actual['extension'],
                        'fuente_url': url_fuente,
                        'fuente_tipo': 'pdf'
                    })
                    
                    # Resetear para siguiente contacto
                    contacto_actual = {'nombre': '', 'cargo': '', 'email': '', 'telefono': '', 'extension': ''}
        
        return contactos
    
    def procesar_pdf_como_imagen(self, pdf_file, url_fuente):
        """Procesa PDF como imagen usando OCR"""
        contactos = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # OCR con pytesseract
                imagen = Image.open(io.BytesIO(img_data))
                texto_ocr = pytesseract.image_to_string(imagen, lang='spa')
                
                if texto_ocr.strip():
                    contactos_pagina = self.extraer_contactos_de_texto(texto_ocr, url_fuente)
                    contactos.extend(contactos_pagina)
            
            doc.close()
            print(f"   ✅ OCR procesado: {len(contactos)} contactos")
            
        except ImportError:
            print(f"   ⚠️ PyMuPDF no disponible para OCR")
        except Exception as e:
            print(f"   ❌ Error en OCR: {e}")
        
        return contactos

    def procesar_imagen_directorio(self, url_imagen):
        """Procesa imágenes de organigrama usando OCR mejorado"""
        print(f"🖼️ Procesando imagen: {url_imagen}")
        contactos = []
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url_imagen, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Cargar y procesar imagen
                imagen = Image.open(io.BytesIO(response.content))
                
                # Mejorar imagen para OCR
                imagen = self.mejorar_imagen_para_ocr(imagen)
                
                # OCR con configuración optimizada
                config_ocr = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÁÉÍÓÚáéíóúñÑ 0123456789@.-_()'
                texto_ocr = pytesseract.image_to_string(imagen, lang='spa', config=config_ocr)
                
                print(f"   🔍 Texto OCR extraido: {len(texto_ocr)} caracteres")
                
                if texto_ocr.strip():
                    # Extraer contactos del texto OCR
                    contactos = self.extraer_contactos_de_texto(texto_ocr, url_imagen)
                    print(f"   ✅ Imagen procesada: {len(contactos)} contactos")
                else:
                    print(f"   ⚠️ No se pudo extraer texto de la imagen")
                
        except Exception as e:
            print(f"   ❌ Error procesando imagen: {e}")
        
        return contactos
    
    def mejorar_imagen_para_ocr(self, imagen):
        """Mejora la imagen para mejor reconocimiento OCR"""
        try:
            # Convertir a escala de grises
            if imagen.mode != 'L':
                imagen = imagen.convert('L')
            
            # Redimensionar si es muy pequeña
            width, height = imagen.size
            if width < 1000 or height < 1000:
                factor = max(1000/width, 1000/height)
                new_size = (int(width * factor), int(height * factor))
                imagen = imagen.resize(new_size, Image.Resampling.LANCZOS)
            
            # Mejorar contraste
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(imagen)
            imagen = enhancer.enhance(2.0)
            
            return imagen
        except:
            return imagen

    def procesar_pagina_directorio(self, url_pagina):
        """Procesa páginas de directorio en todos los formatos evitando footer"""
        print(f"🌐 Procesando página: {url_pagina}")
        contactos = []
        
        driver = self.crear_driver_avanzado(headless=True)
        
        try:
            driver.get(url_pagina)
            time.sleep(5)
            
            # ESTRATEGIA 1: Buscar texto estructurado (evitando footer)
            print(f"   🔍 Buscando contactos en texto...")
            contactos_texto = self.extraer_contactos_contenido_principal(driver, url_pagina)
            if contactos_texto:
                contactos.extend(contactos_texto)
                print(f"   ✅ Encontrados en texto: {len(contactos_texto)} contactos")
            
            # ESTRATEGIA 2: Buscar tablas (evitando footer)
            if not contactos:
                print(f"   🔍 Buscando tablas de directorio...")
                tablas = driver.find_elements(By.TAG_NAME, "table")
                for tabla in tablas:
                    if not self.esta_en_footer(tabla, driver) and self.es_tabla_directorio(tabla):
                        contactos_tabla = self.extraer_contactos_tabla_avanzada(tabla, url_pagina)
                        if contactos_tabla:
                            contactos.extend(contactos_tabla)
                            print(f"   ✅ Encontrados en tabla: {len(contactos_tabla)} contactos")
            
            # ESTRATEGIA 3: Buscar PDFs de directorio
            if not contactos:
                print(f"   🔍 Buscando PDFs de directorio...")
                enlaces_pdf = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
                
                for enlace_pdf in enlaces_pdf:
                    try:
                        href = enlace_pdf.get_attribute('href')
                        texto = enlace_pdf.text.strip().lower()
                        
                        # Verificar si es un PDF de directorio
                        palabras_directorio_pdf = ['directorio', 'organigrama', 'funcionarios', 'personal', 'estructura']
                        if any(palabra in texto for palabra in palabras_directorio_pdf):
                            print(f"   📄 PDF encontrado: {texto} -> {href}")
                            contactos_pdf = self.procesar_pdf_directorio(href)
                            if contactos_pdf:
                                contactos.extend(contactos_pdf)
                                print(f"   ✅ Encontrados en PDF: {len(contactos_pdf)} contactos")
                                break
                    except Exception:
                        continue
            
            # ESTRATEGIA 4: Buscar imágenes de organigrama
            if not contactos:
                print(f"   🔍 Buscando imágenes de organigrama...")
                enlaces_img = driver.find_elements(By.XPATH, "//a[contains(@href, '.jpg') or contains(@href, '.png') or contains(@href, '.jpeg')] | //img[contains(@src, '.jpg') or contains(@src, '.png') or contains(@src, '.jpeg')]")
                
                for enlace_img in enlaces_img:
                    try:
                        href = enlace_img.get_attribute('href') or enlace_img.get_attribute('src')
                        texto = enlace_img.get_attribute('alt') or enlace_img.text or ''
                        texto = texto.strip().lower()
                        
                        if any(palabra in texto for palabra in ['organigrama', 'directorio', 'estructura']) or 'organigrama' in href.lower():
                            print(f"   🖼️ Imagen encontrada: {texto} -> {href}")
                            contactos_img = self.procesar_imagen_directorio(href)
                            if contactos_img:
                                contactos.extend(contactos_img)
                                print(f"   ✅ Encontrados en imagen: {len(contactos_img)} contactos")
                                break
                    except Exception:
                        continue
            
            # ESTRATEGIA 5: Mensaje de verificación manual
            if not contactos:
                print(f"   ⚠️ No se encontraron contactos en ningún formato")
                contactos.append({
                    'nombre': 'No se logro extraer formato',
                    'cargo': 'Corroborar info directamente en la pagina',
                    'email': '',
                    'telefono': '',
                    'fuente_url': url_pagina,
                    'fuente_tipo': 'verificacion_manual',
                    'link_verificacion': url_pagina
                })
                print(f"   🔗 Link para verificación manual: {url_pagina}")
            
            print(f"   ✅ Página procesada: {len(contactos)} contactos totales")
            
        except Exception as e:
            print(f"   ❌ Error procesando página: {e}")
        finally:
            driver.quit()
        
        return contactos
    
    def esta_en_footer(self, elemento, driver):
        """Verifica si un elemento está en el footer de la página"""
        try:
            # Selectores comunes de footer
            selectores_footer = ['footer', '.footer', '#footer', '.pie', '.bottom', '.contact-info']
            
            for selector in selectores_footer:
                try:
                    footers = driver.find_elements(By.CSS_SELECTOR, selector)
                    for footer in footers:
                        if footer.find_elements(By.XPATH, ".//table") and elemento in footer.find_elements(By.XPATH, ".//table"):
                            return True
                except:
                    continue
            
            # Verificar por posición (si está en el último 20% de la página)
            page_height = driver.execute_script("return document.body.scrollHeight")
            element_position = driver.execute_script("return arguments[0].offsetTop;", elemento)
            
            if element_position > (page_height * 0.8):
                return True
                
        except:
            pass
        
        return False
    
    def extraer_contactos_contenido_principal(self, driver, url_fuente):
        """Extrae contactos solo del contenido principal, evitando footer"""
        contactos = []
        
        try:
            # Buscar en el contenido principal, evitando footer
            selectores_contenido = ['main', '.main', '#main', '.content', '#content', '.container', 'article']
            
            contenido_principal = None
            for selector in selectores_contenido:
                try:
                    elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elementos:
                        contenido_principal = elementos[0]
                        break
                except:
                    continue
            
            if contenido_principal:
                texto_contenido = contenido_principal.text
                print(f"   🔍 Analizando contenido principal ({len(texto_contenido)} caracteres)")
            else:
                # Fallback: todo el body pero excluyendo footer
                try:
                    # Remover footers antes de extraer texto
                    driver.execute_script("""
                        var footers = document.querySelectorAll('footer, .footer, #footer, .pie, .bottom');
                        footers.forEach(function(footer) {
                            footer.style.display = 'none';
                        });
                    """)
                    texto_contenido = driver.find_element(By.TAG_NAME, "body").text
                except:
                    texto_contenido = driver.page_source
            
            # Extraer contactos del texto limpio
            if texto_contenido:
                contactos = self.extraer_contactos_de_texto(texto_contenido, url_fuente)
                
                # Filtrar contactos que parezcan ser del footer
                contactos_filtrados = []
                for contacto in contactos:
                    # Evitar contactos con palabras típicas de footer
                    palabras_footer = ['contacto general', 'información general', 'atención ciudadana', 'mesa de ayuda']
                    if not any(palabra in contacto.get('cargo', '').lower() for palabra in palabras_footer):
                        contactos_filtrados.append(contacto)
                
                contactos = contactos_filtrados
                print(f"   📊 Contactos filtrados (sin footer): {len(contactos)}")
            
        except Exception as e:
            print(f"   ❌ Error extrayendo contenido principal: {e}")
        
        return contactos

    def es_tabla_directorio(self, tabla):
        """Evalúa si una tabla contiene directorio"""
        try:
            texto_tabla = tabla.text.lower()
            indicadores = ['nombre', 'cargo', 'email', 'telefono', 'director', 'coordinador']
            coincidencias = sum(1 for ind in indicadores if ind in texto_tabla)
            return coincidencias >= 3
        except:
            return False

    def extraer_contactos_tabla_avanzada(self, tabla, url_fuente):
        """Extrae contactos de tabla con análisis avanzado"""
        contactos = []
        
        try:
            filas = tabla.find_elements(By.TAG_NAME, "tr")
            if len(filas) < 2:
                return contactos
            
            # Analizar headers
            primera_fila = filas[0]
            headers = [cel.text.strip().lower() for cel in primera_fila.find_elements(By.TAG_NAME, ["th", "td"])]
            
            # Mapear columnas
            indices = {
                'nombre': self.encontrar_indice_columna(headers, ['nombre', 'funcionario']),
                'cargo': self.encontrar_indice_columna(headers, ['cargo', 'puesto']),
                'email': self.encontrar_indice_columna(headers, ['email', 'correo']),
                'telefono': self.encontrar_indice_columna(headers, ['telefono', 'tel'])
            }
            
            # Procesar filas de datos
            for fila in filas[1:]:
                celdas = fila.find_elements(By.TAG_NAME, ["td", "th"])
                
                if len(celdas) >= max([i for i in indices.values() if i is not None], default=[0]):
                    contacto = self.extraer_contacto_de_fila(celdas, indices, url_fuente)
                    if contacto:
                        contactos.append(contacto)
            
        except Exception as e:
            print(f"     ⚠️ Error en tabla: {e}")
        
        return contactos

    def encontrar_indice_columna(self, headers, palabras_buscar):
        """Encuentra índice de columna por palabras clave"""
        for i, header in enumerate(headers):
            if any(palabra in header for palabra in palabras_buscar):
                return i
        return None

    def extraer_contacto_de_fila(self, celdas, indices, url_fuente):
        """Extrae contacto de una fila de tabla"""
        try:
            contacto = {
                'nombre': '',
                'cargo': '',
                'email': '',
                'telefono': '',
                'fuente_url': url_fuente,
                'fuente_tipo': 'tabla'
            }
            
            for campo, indice in indices.items():
                if indice is not None and indice < len(celdas):
                    valor = celdas[indice].text.strip()
                    
                    # Limpiar y validar datos según el campo
                    if campo == 'email':
                        email_match = re.search(self.patron_email, valor)
                        contacto[campo] = email_match.group() if email_match else valor
                    elif campo == 'telefono':
                        tel_match = re.search(self.patron_telefono, valor)
                        contacto[campo] = tel_match.group() if tel_match else valor
                    else:
                        contacto[campo] = valor
            
            # Validar que tenga información útil
            if contacto['nombre'] or contacto['email'] or contacto['telefono']:
                return contacto
                
        except Exception:
            pass
        
        return None

    def extraer_contactos_de_texto(self, texto, url_fuente):
        """Extrae contactos de texto libre con patrones avanzados"""
        contactos = []
        
        try:
            # Limpiar HTML si es necesario
            if '<' in texto and '>' in texto:
                soup = BeautifulSoup(texto, 'html.parser')
                texto = soup.get_text()
            
            # Buscar todos los emails
            emails = re.findall(self.patron_email, texto)
            
            # Buscar todos los teléfonos
            telefonos = re.findall(self.patron_telefono, texto)
            
            # Intentar asociar emails/teléfonos con nombres y cargos
            lineas = texto.split('\n')
            
            contacto_actual = {
                'nombre': '',
                'cargo': '',
                'email': '',
                'telefono': '',
                'fuente_url': url_fuente,
                'fuente_tipo': 'texto'
            }
            
            for i, linea in enumerate(lineas):
                linea = linea.strip()
                if not linea:
                    continue
                
                # Buscar email en la línea
                email_match = re.search(self.patron_email, linea)
                if email_match:
                    contacto_actual['email'] = email_match.group()
                
                # Buscar teléfono en la línea
                tel_match = re.search(self.patron_telefono, linea)
                if tel_match:
                    contacto_actual['telefono'] = tel_match.group()
                
                # Identificar nombres y cargos
                if any(palabra in linea.lower() for palabra in ['director', 'coordinador', 'secretario', 'jefe']):
                    contacto_actual['cargo'] = linea
                elif not any(char in linea for char in ['@', 'tel', 'ext', ':']):
                    if not contacto_actual['nombre'] and len(linea.split()) >= 2:
                        contacto_actual['nombre'] = linea
                
                # Si tenemos suficiente información, guardar contacto
                if (contacto_actual['email'] or contacto_actual['telefono']) and contacto_actual['nombre']:
                    contactos.append(contacto_actual.copy())
                    contacto_actual = {
                        'nombre': '',
                        'cargo': '',
                        'email': '',
                        'telefono': '',
                        'fuente_url': url_fuente,
                        'fuente_tipo': 'texto'
                    }
            
            # Agregar contactos simples si no encontramos estructura
            if not contactos:
                for email in emails[:10]:
                    contactos.append({
                        'nombre': '',
                        'cargo': '',
                        'email': email,
                        'telefono': '',
                        'fuente_url': url_fuente,
                        'fuente_tipo': 'email_simple'
                    })
                
                for telefono in telefonos[:5]:
                    contactos.append({
                        'nombre': '',
                        'cargo': '',
                        'email': '',
                        'telefono': telefono,
                        'fuente_url': url_fuente,
                        'fuente_tipo': 'telefono_simple'
                    })
            
        except Exception as e:
            print(f"     ⚠️ Error extrayendo de texto: {e}")
        
        return contactos

    def analizar_pagina_principal(self, url):
        """Analiza la página principal buscando directorio"""
        return self.procesar_pagina_directorio(url)

    def procesar_contactos_encontrados(self, contactos_raw, nombre_entidad):
        """Procesa y limpia todos los contactos encontrados"""
        if not contactos_raw:
            return pd.DataFrame()
        
        try:
            df = pd.DataFrame(contactos_raw)
            
            # Limpiar datos
            for col in ['nombre', 'cargo', 'email', 'telefono']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace(['', 'nan', 'None'], pd.NA)
            
            # Filtrar contactos válidos
            df = df[(df['email'].notna()) | (df['telefono'].notna())]
            
            # Eliminar duplicados
            df = df.drop_duplicates(subset=['email'], keep='first')
            
            # Agregar información adicional
            df['entidad'] = nombre_entidad
            df['fecha_extraccion'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Guardar resultado
            filename = os.path.join(self.download_path, f"directorio_web_{nombre_entidad.replace(' ', '_').lower()}.csv")
            df.to_csv(filename, index=False, encoding='utf-8')
            
            print(f"💾 Directorio guardado: {filename}")
            print(f"📊 Total contactos procesados: {len(df)}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error procesando contactos: {e}")
            return pd.DataFrame()

    def investigar(self, nombre_entidad):
        """Método principal de investigación"""
        try:
            print(f"[AGENTE CONTACTOS ROBUSTO] Iniciando para: {nombre_entidad}")
            
            # Buscar página oficial
            url_oficial = self.buscar_pagina_oficial_avanzada(nombre_entidad)
            
            if not url_oficial:
                return {
                    'exito': False,
                    'error': 'No se encontró página oficial',
                    'datos': {'contactos': [], 'total_contactos': 0}
                }
            
            # Investigar directorio completo
            df_contactos = self.investigar_directorio_completo(url_oficial, nombre_entidad)
            
            if not df_contactos.empty:
                return {
                    'exito': True,
                    'error': None,
                    'datos': {
                        'url_oficial': url_oficial,
                        'contactos': df_contactos.to_dict('records'),
                        'total_contactos': len(df_contactos)
                    }
                }
            else:
                return {
                    'exito': False,
                    'error': 'No se encontraron contactos en el directorio',
                    'datos': {
                        'url_oficial': url_oficial,
                        'contactos': [],
                        'total_contactos': 0
                    }
                }
                
        except Exception as e:
            return {
                'exito': False,
                'error': str(e),
                'datos': {'contactos': [], 'total_contactos': 0}
            }