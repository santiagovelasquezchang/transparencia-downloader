import threading
import pandas as pd
from datetime import datetime
from agente_transparencia import AgenteTransparencia
from agente_contactos import AgenteContactos

class Coordinador:
    def __init__(self):
        self.agente_transparencia = AgenteTransparencia()
        self.agente_contactos = AgenteContactos()
        
    def investigar_entidad(self, nombre_entidad, log_callback):
        """Coordina investigación con ambos agentes en paralelo"""
        resultado = {
            'entidad': nombre_entidad,
            'timestamp': datetime.now().isoformat(),
            'transparencia': {},
            'contactos': {}
        }
        
        # Crear threads para ejecución paralela
        transparencia_thread = threading.Thread(
            target=self._ejecutar_agente_transparencia,
            args=(nombre_entidad, resultado, log_callback)
        )
        
        contactos_thread = threading.Thread(
            target=self._ejecutar_agente_contactos,
            args=(nombre_entidad, resultado, log_callback)
        )
        
        # Iniciar ambos agentes
        log_callback(f"   🤖 Agente Transparencia: Validando y descargando Excel...", "download")
        transparencia_thread.start()
        
        log_callback(f"   🌐 Agente Contactos: Buscando en web...", "search")
        contactos_thread.start()
        
        # Esperar a que ambos terminen
        transparencia_thread.join()
        contactos_thread.join()
        
        return resultado
    
    def _ejecutar_agente_transparencia(self, nombre_entidad, resultado, log_callback):
        """Ejecutar agente de transparencia"""
        try:
            log_callback(f"      📋 Validando nombre en plataforma oficial...")
            datos = self.agente_transparencia.investigar(nombre_entidad)
            resultado['transparencia'] = datos
            
            if datos['exito']:
                institucion = datos['institucion_validada']
                similitud = datos['similitud']
                archivo = datos['ruta_archivo']
                
                if similitud == 100:
                    log_callback(f"      ✅ Nombre exacto encontrado: {institucion}")
                else:
                    log_callback(f"      ✅ Nombre corregido: {nombre_entidad} → {institucion} ({similitud}%)")
                
                if archivo:
                    nombre_archivo = archivo.split('/')[-1] if '/' in archivo else archivo.split('\\')[-1]
                    log_callback(f"      📥 Excel descargado: {nombre_archivo}")
                else:
                    log_callback(f"      📥 Excel procesado (verificar carpeta downloads)")
            else:
                error = datos.get('error', 'Error desconocido')
                log_callback(f"      ❌ Transparencia falló: {error}")
                
        except Exception as e:
            log_callback(f"      💥 Error crítico Agente Transparencia: {str(e)}")
            resultado['transparencia'] = {
                'exito': False,
                'error': str(e),
                'institucion_validada': None,
                'similitud': 0,
                'archivo_descargado': False
            }
    
    def _ejecutar_agente_contactos(self, nombre_entidad, resultado, log_callback):
        """Ejecutar agente de contactos web"""
        try:
            log_callback(f"      🔍 Buscando página oficial en Google...")
            datos = self.agente_contactos.investigar(nombre_entidad)
            resultado['contactos'] = datos
            
            if datos['exito']:
                url = datos['datos'].get('url_oficial', 'N/A')
                contactos_count = len(datos['datos'].get('contactos', []))
                log_callback(f"      ✅ Página encontrada: {url}")
                log_callback(f"      📞 Contactos extraídos: {contactos_count}")
            else:
                error = datos.get('error', 'Error desconocido')
                log_callback(f"      ❌ Búsqueda web falló: {error}")
                
        except Exception as e:
            log_callback(f"      💥 Error crítico Agente Contactos: {str(e)}")
            resultado['contactos'] = {
                'exito': False,
                'error': str(e),
                'datos': {}
            }
    
    def exportar_resultados(self, resultados, filename):
        """Exportar resumen de resultados (los Excel están en downloads/)"""
        try:
            # DataFrame principal con resumen
            main_data = []
            for resultado in resultados:
                transparencia = resultado['transparencia']
                contactos = resultado['contactos']
                
                main_data.append({
                    'Entidad_Original': resultado['entidad'],
                    'Fecha_Investigacion': resultado['timestamp'],
                    
                    # Datos Transparencia
                    'Transparencia_Exitoso': transparencia.get('exito', False),
                    'Institucion_Validada': transparencia.get('institucion_validada', ''),
                    'Similitud_Nombre': transparencia.get('similitud', 0),
                    'Excel_Descargado': transparencia.get('archivo_descargado', False),
                    'Archivo_Excel': transparencia.get('ruta_archivo', ''),
                    'Error_Transparencia': transparencia.get('error', ''),
                    
                    # Datos Contactos Web
                    'Contactos_Exitoso': contactos.get('exito', False),
                    'URL_Oficial_Encontrada': contactos.get('datos', {}).get('url_oficial', ''),
                    'Total_Contactos_Web': len(contactos.get('datos', {}).get('contactos', [])),
                    'Error_Contactos': contactos.get('error', '')
                })
            
            # DataFrame de contactos web extraídos
            contactos_web_data = []
            for resultado in resultados:
                if resultado['contactos'].get('exito'):
                    entidad = resultado['entidad']
                    contactos = resultado['contactos'].get('datos', {}).get('contactos', [])
                    
                    for contacto in contactos:
                        contactos_web_data.append({
                            'Entidad': entidad,
                            'Fuente': 'Web',
                            'Nombre': contacto.get('nombre', ''),
                            'Cargo': contacto.get('cargo', ''),
                            'Email': contacto.get('email', ''),
                            'Telefono': contacto.get('telefono', ''),
                            'Departamento': contacto.get('departamento', ''),
                            'URL_Fuente': contacto.get('fuente_url', '')
                        })
            
            # Crear Excel con múltiples hojas
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Hoja principal con resumen
                df_main = pd.DataFrame(main_data)
                df_main.to_excel(writer, sheet_name='Resumen_Investigacion', index=False)
                
                # Hoja de contactos web
                if contactos_web_data:
                    df_contactos_web = pd.DataFrame(contactos_web_data)
                    df_contactos_web.to_excel(writer, sheet_name='Contactos_Web', index=False)
                
                # Hoja de instrucciones
                instrucciones = pd.DataFrame([
                    ['INSTRUCCIONES:', ''],
                    ['', ''],
                    ['1. Excel Directorios:', 'Los archivos Excel con directorios completos están en la carpeta "downloads/"'],
                    ['2. Contactos Web:', 'Contactos adicionales extraídos de páginas web oficiales'],
                    ['3. Resumen:', 'Esta hoja muestra el estado de cada investigación'],
                    ['', ''],
                    ['Columnas importantes:', ''],
                    ['- Excel_Descargado:', 'TRUE = Se descargó el directorio oficial'],
                    ['- Institucion_Validada:', 'Nombre correcto encontrado en la plataforma'],
                    ['- Similitud_Nombre:', 'Porcentaje de similitud con el nombre original'],
                    ['- Total_Contactos_Web:', 'Cantidad de contactos encontrados en web']
                ], columns=['Campo', 'Descripcion'])
                
                instrucciones.to_excel(writer, sheet_name='Instrucciones', index=False)
                
        except Exception as e:
            raise Exception(f"Error exportando resultados: {str(e)}")