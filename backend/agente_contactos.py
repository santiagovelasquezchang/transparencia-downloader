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

    def investigar_directorio_completo(self, url_base, nombre_entidad):
        """Investigación completa de directorio con múltiples formatos"""
        print(f"🌐 Investigación completa en: {url_base}")
        
        contactos_totales = []
        
        # Paso 1: Buscar enlaces específicos de directorio PRIMERO (evitar contacto general)
        print("🔗 Buscando enlaces de directorio/organigrama...")
        enlaces_directorio = self.encontrar_enlaces_directorio_avanzado(url_base)
        
        # Paso 2: Explorar cada enlace encontrado
        for enlace in enlaces_directorio[:5]:  # Limitar a 5 enlaces
            print(f"\n📂 Explorando: {enlace['texto']}")
            
            if enlace['tipo'] == 'pdf':
                contactos_pdf = self.procesar_pdf_directorio(enlace['url'])
                contactos_totales.extend(contactos_pdf)
            elif enlace['tipo'] == 'imagen':
                contactos_img = self.procesar_imagen_directorio(enlace['url'])
                contactos_totales.extend(contactos_img)
            else:
                contactos_html = self.procesar_pagina_directorio(enlace['url'])
                contactos_totales.extend(contactos_html)
        
        # Paso 3: Solo si no encontramos nada, analizar página principal
        if not contactos_totales:
            print("📄 No se encontraron directorios específicos, analizando página principal...")
            contactos_main = self.analizar_pagina_principal(url_base)
            contactos_totales.extend(contactos_main)
        
        # Procesar y filtrar contactos
        if contactos_totales:
            df_contactos = self.procesar_contactos_encontrados(contactos_totales, nombre_entidad)
            return df_contactos
        
        return pd.DataFrame()

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
        """Procesa PDFs de organigrama/directorio"""
        print(f"📄 Procesando PDF: {url_pdf}")
        contactos = []
        
        try:
            # Descargar PDF
            response = requests.get(url_pdf, timeout=30)
            
            if response.status_code == 200:
                # Leer PDF con PyPDF2
                pdf_file = io.BytesIO(response.content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                texto_completo = ""
                for page in pdf_reader.pages:
                    texto_completo += page.extract_text() + "\n"
                
                # Extraer contactos del texto
                contactos = self.extraer_contactos_de_texto(texto_completo, url_pdf)
                print(f"   ✅ PDF procesado: {len(contactos)} contactos")
                
        except Exception as e:
            print(f"   ❌ Error procesando PDF: {e}")
        
        return contactos

    def procesar_imagen_directorio(self, url_imagen):
        """Procesa imágenes de organigrama usando OCR"""
        print(f"🖼️ Procesando imagen: {url_imagen}")
        contactos = []
        
        try:
            # Descargar imagen
            response = requests.get(url_imagen, timeout=30)
            
            if response.status_code == 200:
                # Cargar imagen
                imagen = Image.open(io.BytesIO(response.content))
                
                # OCR con pytesseract
                texto_ocr = pytesseract.image_to_string(imagen, lang='spa')
                
                # Extraer contactos del texto OCR
                contactos = self.extraer_contactos_de_texto(texto_ocr, url_imagen)
                print(f"   ✅ Imagen procesada: {len(contactos)} contactos")
                
        except Exception as e:
            print(f"   ❌ Error procesando imagen: {e}")
        
        return contactos

    def procesar_pagina_directorio(self, url_pagina):
        """Procesa páginas HTML de directorio"""
        print(f"🌐 Procesando página: {url_pagina}")
        contactos = []
        
        driver = self.crear_driver_avanzado(headless=True)
        
        try:
            driver.get(url_pagina)
            time.sleep(5)
            
            # Estrategia 1: Buscar tablas
            tablas = driver.find_elements(By.TAG_NAME, "table")
            for tabla in tablas:
                if self.es_tabla_directorio(tabla):
                    contactos_tabla = self.extraer_contactos_tabla_avanzada(tabla, url_pagina)
                    contactos.extend(contactos_tabla)
            
            # Estrategia 2: Buscar texto estructurado
            texto_pagina = driver.page_source
            contactos_texto = self.extraer_contactos_de_texto(texto_pagina, url_pagina)
            contactos.extend(contactos_texto)
            
            print(f"   ✅ Página procesada: {len(contactos)} contactos")
            
        except Exception as e:
            print(f"   ❌ Error procesando página: {e}")
        finally:
            driver.quit()
        
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