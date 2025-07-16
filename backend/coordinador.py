import threading
import pandas as pd
import os
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
        """Ejecutar agente de contactos - Solo URLs"""
        try:
            log_callback(f"      🔍 Buscando URL de directorio...")
            datos = self.agente_contactos.investigar(nombre_entidad)
            resultado['contactos'] = datos
            
            if datos['exito']:
                url_directorio = datos.get('url_directorio', 'N/A')
                log_callback(f"      ✅ URL encontrada: {url_directorio}")
            else:
                error = datos.get('error', 'Error desconocido')
                log_callback(f"      ❌ Búsqueda web falló: {error}")
                
        except Exception as e:
            log_callback(f"      💥 Error crítico Agente Contactos: {str(e)}")
            resultado['contactos'] = {
                'exito': False,
                'error': str(e),
                'url_directorio': None
            }
    
    def filtrar_contactos_aws(self, contactos_raw):
        """Filtra contactos relevantes para adquisición de servicios AWS"""
        
        # Palabras clave para cargos relevantes AWS
        cargos_aws_relevantes = [
            # Tecnología
            'director de tecnologia', 'director tecnologico', 'cto', 'chief technology',
            'coordinador de tecnologia', 'jefe de sistemas', 'director de sistemas',
            'director de informatica', 'coordinador de informatica',
            
            # Administración y Finanzas
            'director de administracion', 'director administrativo', 'cfo', 'chief financial',
            'secretario de administracion', 'coordinador administrativo',
            'director de finanzas', 'coordinador de finanzas', 'tesorero',
            
            # Innovación
            'director de innovacion', 'coordinador de innovacion', 'jefe de innovacion',
            'director de modernizacion', 'coordinador de modernizacion',
            
            # Compras/Adquisiciones
            'director de adquisiciones', 'coordinador de compras', 'jefe de compras',
            'responsable de adquisiciones', 'encargado de compras'
        ]
        
        contactos_filtrados = []
        
        for contacto in contactos_raw:
            cargo_lower = contacto.get('cargo', '').lower()
            nombre = contacto.get('nombre', '').strip()
            email = contacto.get('email', '').strip()
            telefono = contacto.get('telefono', '').strip()
            
            # Verificar si el cargo es relevante para AWS
            es_relevante = any(palabra_clave in cargo_lower for palabra_clave in cargos_aws_relevantes)
            
            # Verificar que tenga datos mínimos
            tiene_datos = nombre and (email or telefono)
            
            # Verificar que el email sea institucional
            email_institucional = '@gob.mx' in email.lower() or '.gob.' in email.lower() or not email
            
            if es_relevante and tiene_datos and email_institucional:
                # Calcular relevancia (0-100)
                relevancia = 0
                if 'director' in cargo_lower:
                    relevancia += 40
                if 'coordinador' in cargo_lower:
                    relevancia += 30
                if 'jefe' in cargo_lower:
                    relevancia += 25
                if any(tech in cargo_lower for tech in ['tecnologia', 'sistemas', 'informatica']):
                    relevancia += 30
                if any(admin in cargo_lower for admin in ['administracion', 'finanzas']):
                    relevancia += 25
                if 'innovacion' in cargo_lower:
                    relevancia += 35
                
                contacto['relevancia_aws'] = min(100, relevancia)
                contactos_filtrados.append(contacto)
        
        # Ordenar por relevancia
        contactos_filtrados.sort(key=lambda x: x.get('relevancia_aws', 0), reverse=True)
        
        return contactos_filtrados
    
    def investigar_multiples_entidades(self, entidades_texto, log_callback):
        """Investiga múltiples entidades y filtra contactos AWS"""
        entidades = [e.strip() for e in entidades_texto.split('\n') if e.strip()]
        
        if not entidades:
            return {"error": "No se proporcionaron entidades para investigar"}
        
        log_callback(f"🚀 Iniciando investigación de {len(entidades)} entidades...")
        
        resultados = []
        todos_contactos = []
        
        for i, entidad in enumerate(entidades, 1):
            log_callback(f"\n🔍 [{i}/{len(entidades)}] Investigando: {entidad}")
            
            # Investigar entidad individual
            resultado = self.investigar_entidad(entidad, log_callback)
            resultados.append(resultado)
            
            # Extraer contactos de ambas fuentes
            contactos_entidad = self._extraer_contactos_resultado(resultado, entidad)
            todos_contactos.extend(contactos_entidad)
        
        # Filtrar contactos relevantes para AWS
        log_callback(f"\n🤖 Filtrando contactos relevantes para AWS...")
        contactos_aws = self.filtrar_contactos_aws(todos_contactos)
        
        # Agrupar por entidad
        contactos_por_entidad = {}
        for contacto in contactos_aws:
            entidad = contacto['entidad']
            if entidad not in contactos_por_entidad:
                contactos_por_entidad[entidad] = []
            contactos_por_entidad[entidad].append(contacto)
        
        log_callback(f"🎯 Contactos AWS encontrados: {len(contactos_aws)}")
        log_callback(f"🎉 Investigación completada")
        
        return {
            'exito': True,
            'total_entidades': len(entidades),
            'resultados': resultados,
            'contactos_aws': contactos_aws,
            'contactos_por_entidad': contactos_por_entidad,
            'timestamp': datetime.now().isoformat()
        }
    
    def _extraer_contactos_resultado(self, resultado, entidad):
        """Extrae contactos de los resultados de transparencia y web"""
        contactos = []
        
        # Contactos de transparencia
        if resultado['transparencia'].get('exito') and 'ruta_archivo' in resultado['transparencia']:
            try:
                df_transp = pd.read_csv(resultado['transparencia']['ruta_archivo'])
                for _, row in df_transp.iterrows():
                    contactos.append({
                        'entidad': entidad,
                        'nombre': str(row.get('Nombre(s) de la persona servidora pública', '')),
                        'cargo': str(row.get('Denominación del cargo', '')),
                        'email': str(row.get('Correo electrónico oficial, en su caso', '')),
                        'telefono': str(row.get('Teléfono', '')),
                        'fuente': 'transparencia'
                    })
            except Exception:
                pass
        
        # Contactos web
        if resultado['contactos'].get('exito'):
            contactos_web = resultado['contactos'].get('datos', {}).get('contactos', [])
            for contacto in contactos_web:
                contactos.append({
                    'entidad': entidad,
                    'nombre': contacto.get('nombre', ''),
                    'cargo': contacto.get('cargo', ''),
                    'email': contacto.get('email', ''),
                    'telefono': contacto.get('telefono', ''),
                    'fuente': 'web'
                })
        
        return contactos
    
    def generar_excel_aws(self, contactos_por_entidad, ruta_descarga):
        """Genera Excel con contactos AWS organizados por entidad"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"contactos_aws_{timestamp}.xlsx"
        filepath = f"{ruta_descarga}/{filename}"
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Hoja con todos los contactos organizados
            todos_contactos = []
            for entidad, contactos in contactos_por_entidad.items():
                for contacto in contactos:
                    todos_contactos.append({
                        'Entidad': entidad,
                        'Nombre': contacto['nombre'],
                        'Cargo': contacto['cargo'],
                        'Email': contacto['email'],
                        'Teléfono': contacto['telefono'],
                        'Relevancia AWS': f"{contacto.get('relevancia_aws', 0)}%",
                        'Fuente': contacto['fuente']
                    })
            
            df_contactos = pd.DataFrame(todos_contactos)
            df_contactos.to_excel(writer, sheet_name='Contactos AWS', index=False)
            
            # Hoja resumen por entidad
            resumen_data = []
            for entidad, contactos in contactos_por_entidad.items():
                resumen_data.append({
                    'Entidad': entidad,
                    'Total Contactos AWS': len(contactos),
                    'Directores': len([c for c in contactos if 'director' in c['cargo'].lower()]),
                    'Coordinadores': len([c for c in contactos if 'coordinador' in c['cargo'].lower()]),
                    'Tecnología': len([c for c in contactos if any(t in c['cargo'].lower() for t in ['tecnologia', 'sistemas', 'informatica'])]),
                    'Finanzas': len([c for c in contactos if any(f in c['cargo'].lower() for f in ['finanzas', 'administracion'])]),
                    'Innovación': len([c for c in contactos if 'innovacion' in c['cargo'].lower()])
                })
            
            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
        
        return filepath
    
    def procesar_con_claude_al_final(self, resultados, log_callback):
        """Procesa todos los resultados con Claude Desktop"""
        try:
            log_callback("🤖 Procesando contactos con Claude AI...", "info")
            
            contactos_aws = []
            
            for resultado in resultados:
                entidad = resultado['entidad']
                
                # Solo procesar si transparencia fue exitosa
                if resultado['transparencia'].get('exito') and 'ruta_archivo' in resultado['transparencia']:
                    try:
                        ruta_archivo = resultado['transparencia']['ruta_archivo']
                        print(f"📁 Procesando: {ruta_archivo}")
                        
                        # Verificar si el archivo existe
                        if not os.path.exists(ruta_archivo):
                            print(f"❌ Archivo no existe: {ruta_archivo}")
                            continue
                        
                        # Usar Claude Desktop
                        from filtro_claude import FiltroClaude
                        filtro = FiltroClaude()
                        contactos_filtrados = filtro.filtrar_contactos(ruta_archivo, min_relevancia=60)
                        
                        for contacto in contactos_filtrados:
                            contacto['entidad'] = entidad
                            contactos_aws.append(contacto)
                        
                        log_callback(f"✅ {entidad}: {len(contactos_filtrados)} contactos AWS", "success")
                    
                    except Exception as e:
                        log_callback(f"⚠️ Error procesando {entidad}: {e}", "warning")
                        print(f"❌ Error detallado para {entidad}: {e}")
                        print(f"📁 Ruta esperada: {resultado['transparencia'].get('ruta_archivo', 'N/A')}")
                        continue
            
            log_callback(f"🎯 Total contactos AWS: {len(contactos_aws)}", "success")
            return contactos_aws
            
        except Exception as e:
            log_callback(f"❌ Error con Claude AI: {e}", "error")
            return []
            
    def procesar_con_filtro_aws(self, resultados, log_callback):
        """Procesa todos los resultados con filtro basado en reglas"""
        try:
            log_callback("📊 Procesando contactos con filtro AWS...", "info")
            
            contactos_aws = []
            
            for resultado in resultados:
                entidad = resultado['entidad']
                
                # Solo procesar si transparencia fue exitosa
                if resultado['transparencia'].get('exito') and 'ruta_archivo' in resultado['transparencia']:
                    try:
                        ruta_archivo = resultado['transparencia']['ruta_archivo']
                        print(f"📁 Procesando: {ruta_archivo}")
                        
                        # Verificar si el archivo existe
                        if not os.path.exists(ruta_archivo):
                            print(f"❌ Archivo no existe: {ruta_archivo}")
                            continue
                        
                        # Usar filtro basado en reglas
                        from filtro_aws import FiltroAWS
                        filtro = FiltroAWS()
                        contactos_filtrados = filtro.filtrar_contactos(ruta_archivo, min_relevancia=60)
                        
                        for contacto in contactos_filtrados:
                            contacto['entidad'] = entidad
                            contactos_aws.append(contacto)
                        
                        log_callback(f"✅ {entidad}: {len(contactos_filtrados)} contactos AWS", "success")
                    
                    except Exception as e:
                        log_callback(f"⚠️ Error procesando {entidad}: {e}", "warning")
                        print(f"❌ Error detallado para {entidad}: {e}")
                        print(f"📁 Ruta esperada: {resultado['transparencia'].get('ruta_archivo', 'N/A')}")
                        continue
            
            log_callback(f"🎯 Total contactos AWS: {len(contactos_aws)}", "success")
            return contactos_aws
            
        except Exception as e:
            log_callback(f"❌ Error con filtro AWS: {e}", "error")
            return []
    
    # Método eliminado - Reemplazado por filtro_aws.py