import pandas as pd
import os
import re
from datetime import datetime
from fuzzywuzzy import fuzz

class FiltroContactos:
    def __init__(self, download_path="downloads"):
        self.download_path = os.path.abspath(download_path)
        
        # Cargos importantes a nivel empresarial
        self.cargos_empresariales = [
            'director', 'directora', 'director general', 'directora general',
            'subdirector', 'subdirectora', 'coordinador', 'coordinadora',
            'jefe', 'jefa', 'gerente', 'secretario', 'secretaria',
            'titular', 'responsable', 'encargado', 'encargada',
            'presidente', 'presidenta', 'vicepresidente', 'vicepresidenta',
            'administrador', 'administradora', 'supervisor', 'supervisora'
        ]
        
        # Cargos importantes de tecnología
        self.cargos_tecnologia = [
            'sistemas', 'informatica', 'tecnologia', 'it', 'tic',
            'cto', 'chief technology officer', 'director de tecnologia',
            'coordinador de sistemas', 'jefe de sistemas', 'analista',
            'programador', 'desarrollador', 'soporte tecnico',
            'administrador de sistemas', 'seguridad informatica',
            'base de datos', 'redes', 'infraestructura'
        ]
    
    def separar_nombre_apellido(self, nombre_completo):
        """Separa nombre y apellido de un nombre completo"""
        if not nombre_completo or pd.isna(nombre_completo):
            return '', ''
        
        partes = str(nombre_completo).strip().split()
        if len(partes) == 0:
            return '', ''
        elif len(partes) == 1:
            return partes[0], ''
        elif len(partes) == 2:
            return partes[0], partes[1]
        else:
            # Asumir que los primeros 2 son nombres y el resto apellidos
            nombres = ' '.join(partes[:2])
            apellidos = ' '.join(partes[2:])
            return nombres, apellidos
    
    def es_cargo_importante(self, cargo):
        """Determina si un cargo es importante (empresarial o tecnológico)"""
        if not cargo or pd.isna(cargo):
            return False, ''
        
        cargo_lower = str(cargo).lower()
        
        # Verificar cargos empresariales
        for cargo_emp in self.cargos_empresariales:
            if cargo_emp in cargo_lower:
                return True, 'empresarial'
        
        # Verificar cargos de tecnología
        for cargo_tech in self.cargos_tecnologia:
            if cargo_tech in cargo_lower:
                return True, 'tecnologia'
        
        return False, ''
    
    def limpiar_telefono(self, telefono):
        """Limpia y formatea número de teléfono"""
        if not telefono or pd.isna(telefono):
            return ''
        
        # Extraer solo números
        numeros = re.sub(r'[^\d]', '', str(telefono))
        
        # Formatear si tiene 10 dígitos
        if len(numeros) == 10:
            return f"({numeros[:3]}) {numeros[3:6]}-{numeros[6:]}"
        elif len(numeros) > 10:
            return f"({numeros[-10:-7]}) {numeros[-7:-4]}-{numeros[-4:]}"
        else:
            return str(telefono)
    
    def procesar_archivo_transparencia(self, archivo_path):
        """Procesa archivo de transparencia (CSV)"""
        contactos = []
        
        try:
            df = pd.read_csv(archivo_path, encoding='utf-8')
            
            for _, row in df.iterrows():
                # Buscar columnas relevantes
                nombre = ''
                cargo = ''
                email = ''
                telefono = ''
                
                # Mapear columnas comunes
                for col in df.columns:
                    col_lower = col.lower()
                    if 'nombre' in col_lower and not nombre:
                        nombre = row[col] if pd.notna(row[col]) else ''
                    elif 'cargo' in col_lower or 'puesto' in col_lower and not cargo:
                        cargo = row[col] if pd.notna(row[col]) else ''
                    elif 'correo' in col_lower or 'email' in col_lower and not email:
                        email = row[col] if pd.notna(row[col]) else ''
                    elif 'telefono' in col_lower or 'tel' in col_lower and not telefono:
                        telefono = row[col] if pd.notna(row[col]) else ''
                
                if nombre and (email or telefono):
                    contactos.append({
                        'nombre_completo': nombre,
                        'cargo': cargo,
                        'email': email,
                        'telefono': telefono,
                        'fuente': 'transparencia'
                    })
        
        except Exception as e:
            print(f"Error procesando {archivo_path}: {e}")
        
        return contactos
    
    def procesar_archivo_contactos(self, archivo_path):
        """Procesa archivo de contactos web (CSV)"""
        contactos = []
        
        try:
            df = pd.read_csv(archivo_path, encoding='utf-8')
            
            for _, row in df.iterrows():
                nombre = row.get('nombre', '') or row.get('Nombre', '')
                cargo = row.get('cargo', '') or row.get('Cargo', '')
                email = row.get('email', '') or row.get('Email', '')
                telefono = row.get('telefono', '') or row.get('Telefono', '')
                
                if nombre and (email or telefono):
                    contactos.append({
                        'nombre_completo': nombre,
                        'cargo': cargo,
                        'email': email,
                        'telefono': telefono,
                        'fuente': 'web'
                    })
        
        except Exception as e:
            print(f"Error procesando {archivo_path}: {e}")
        
        return contactos
    
    def eliminar_duplicados(self, contactos):
        """Elimina contactos duplicados basándose en email y nombre"""
        contactos_unicos = []
        emails_vistos = set()
        nombres_vistos = set()
        
        for contacto in contactos:
            email = contacto['email'].lower().strip() if contacto['email'] else ''
            nombre = contacto['nombre_completo'].lower().strip() if contacto['nombre_completo'] else ''
            
            # Crear clave única
            clave = f"{email}_{nombre}" if email else nombre
            
            if clave and clave not in emails_vistos:
                emails_vistos.add(clave)
                contactos_unicos.append(contacto)
        
        return contactos_unicos
    
    def filtrar_contactos_importantes(self, contactos):
        """Filtra solo contactos con cargos importantes"""
        contactos_importantes = []
        
        for contacto in contactos:
            es_importante, tipo_cargo = self.es_cargo_importante(contacto['cargo'])
            
            if es_importante:
                nombre, apellido = self.separar_nombre_apellido(contacto['nombre_completo'])
                
                contacto_filtrado = {
                    'nombre': nombre,
                    'apellido': apellido,
                    'cargo': contacto['cargo'],
                    'telefono': self.limpiar_telefono(contacto['telefono']),
                    'email': contacto['email'],
                    'tipo_cargo': tipo_cargo,
                    'fuente': contacto['fuente']
                }
                
                contactos_importantes.append(contacto_filtrado)
        
        return contactos_importantes
    
    def procesar_institucion(self, nombre_institucion):
        """Procesa todos los archivos de una institución"""
        print(f"🏢 Procesando institución: {nombre_institucion}")
        
        # Buscar archivos relacionados con la institución
        institucion_clean = nombre_institucion.lower().replace(' ', '_')
        archivos_encontrados = []
        
        for archivo in os.listdir(self.download_path):
            if institucion_clean in archivo.lower() and archivo.endswith('.csv'):
                archivos_encontrados.append(os.path.join(self.download_path, archivo))
        
        print(f"📁 Archivos encontrados: {len(archivos_encontrados)}")
        
        todos_contactos = []
        
        # Procesar cada archivo
        for archivo_path in archivos_encontrados:
            print(f"📄 Procesando: {os.path.basename(archivo_path)}")
            
            if 'directorio_' in archivo_path and 'web' not in archivo_path:
                # Archivo de transparencia
                contactos = self.procesar_archivo_transparencia(archivo_path)
            else:
                # Archivo de contactos web
                contactos = self.procesar_archivo_contactos(archivo_path)
            
            todos_contactos.extend(contactos)
        
        # Eliminar duplicados
        contactos_unicos = self.eliminar_duplicados(todos_contactos)
        print(f"📊 Contactos únicos: {len(contactos_unicos)}")
        
        # Filtrar contactos importantes
        contactos_importantes = self.filtrar_contactos_importantes(contactos_unicos)
        print(f"⭐ Contactos importantes: {len(contactos_importantes)}")
        
        return contactos_importantes
    
    def generar_reporte_filtrado(self, instituciones, log_callback=None):
        """Genera reporte filtrado para múltiples instituciones"""
        if log_callback is None:
            log_callback = lambda msg, tipo: print(f"[{tipo.upper()}] {msg}")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_salida = os.path.join(self.download_path, f"contactos_filtrados_{timestamp}.xlsx")
        
        log_callback(f"📁 Creando archivo Excel: contactos_filtrados_{timestamp}.xlsx", "info")
        log_callback(f"🔍 Leyendo archivos CSV de transparencia y web...", "info")
        log_callback(f"🔄 Eliminando contactos duplicados...", "info")
        
        with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
            # Hoja resumen
            resumen_data = []
            todos_contactos = []
            
            for institucion in instituciones:
                log_callback(f"🏢 Procesando institución: {institucion}", "info")
                contactos = self.procesar_institucion(institucion)
                
                log_callback(f"📊 {institucion}: {len(contactos)} contactos importantes encontrados", "info")
                
                # Agregar institución a cada contacto
                for contacto in contactos:
                    contacto['institucion'] = institucion
                    todos_contactos.append(contacto)
                
                # Estadísticas por institución
                empresariales = len([c for c in contactos if c['tipo_cargo'] == 'empresarial'])
                tecnologia = len([c for c in contactos if c['tipo_cargo'] == 'tecnologia'])
                
                resumen_data.append({
                    'Institucion': institucion,
                    'Total_Contactos': len(contactos),
                    'Cargos_Empresariales': empresariales,
                    'Cargos_Tecnologia': tecnologia,
                    'Fuente_Transparencia': len([c for c in contactos if c['fuente'] == 'transparencia']),
                    'Fuente_Web': len([c for c in contactos if c['fuente'] == 'web'])
                })
            
            # Crear DataFrames
            df_resumen = pd.DataFrame(resumen_data)
            df_contactos = pd.DataFrame(todos_contactos)
            
            # Escribir hojas
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            
            if not df_contactos.empty:
                # Hoja con todos los contactos
                df_contactos.to_excel(writer, sheet_name='Todos_Contactos', index=False)
                
                # Hoja solo cargos empresariales
                df_empresariales = df_contactos[df_contactos['tipo_cargo'] == 'empresarial']
                if not df_empresariales.empty:
                    df_empresariales.to_excel(writer, sheet_name='Cargos_Empresariales', index=False)
                
                # Hoja solo cargos de tecnología
                df_tecnologia = df_contactos[df_contactos['tipo_cargo'] == 'tecnologia']
                if not df_tecnologia.empty:
                    df_tecnologia.to_excel(writer, sheet_name='Cargos_Tecnologia', index=False)
        
        # Estadísticas finales
        total_empresariales = len([c for c in todos_contactos if c.get('tipo_cargo') == 'empresarial'])
        total_tecnologia = len([c for c in todos_contactos if c.get('tipo_cargo') == 'tecnologia'])
        
        log_callback(f"💾 Archivo Excel generado exitosamente", "success")
        log_callback(f"📁 Nombre: {os.path.basename(archivo_salida)}", "info")
        log_callback(f"📊 Total contactos importantes: {len(todos_contactos)}", "success")
        log_callback(f"🏢 Cargos empresariales: {total_empresariales}", "info")
        log_callback(f"💻 Cargos tecnología: {total_tecnologia}", "info")
        log_callback(f"📂 Hojas creadas: Resumen, Todos_Contactos, Cargos_Empresariales, Cargos_Tecnologia", "info")
        
        print(f"📊 Reporte generado: {archivo_salida}")
        print(f"📁 Ubicación: {os.path.abspath(archivo_salida)}")
        print(f"📊 Resumen del filtrado:")
        print(f"   - Instituciones procesadas: {len(instituciones)}")
        print(f"   - Contactos importantes encontrados: {len(todos_contactos)}")
        print(f"   - Cargos empresariales: {total_empresariales}")
        print(f"   - Cargos tecnología: {total_tecnologia}")
        print(f"   - Archivos CSV procesados: {sum(len(os.listdir(self.download_path)) for _ in [1] if os.path.exists(self.download_path))}")
        
        return archivo_salida