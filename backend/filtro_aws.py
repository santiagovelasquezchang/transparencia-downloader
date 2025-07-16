import pandas as pd
import re
import os

class FiltroAWS:
    """Filtro simple basado en reglas para contactos relevantes para AWS"""
    
    def __init__(self):
        # Palabras clave para cargos relevantes
        self.cargos_relevantes = {
            # Tecnología (90-100 puntos)
            'tecnologia': 100,
            'sistemas': 95,
            'informatica': 95,
            'informacion': 90,
            'innovacion': 90,
            'digital': 90,
            'datos': 90,
            'cto': 100,
            'chief technology': 100,
            
            # Administración/Finanzas (80-90 puntos)
            'administracion': 85,
            'finanzas': 85,
            'administrativo': 80,
            'financiero': 80,
            'cfo': 90,
            'chief financial': 90,
            
            # Compras/Adquisiciones (75-85 puntos)
            'compras': 80,
            'adquisiciones': 80,
            'contrataciones': 75,
            'licitaciones': 75,
            
            # Otros relevantes (60-75 puntos)
            'planeacion': 70,
            'estrategia': 70,
            'modernizacion': 75,
            'proyectos': 65,
            'operaciones': 60
        }
        
        # Palabras clave para áreas relevantes
        self.areas_relevantes = {
            'tecnologia': 20,
            'sistemas': 20,
            'informatica': 20,
            'innovacion': 15,
            'digital': 15,
            'compras': 10,
            'adquisiciones': 10,
            'finanzas': 10,
            'administracion': 10
        }
        
        # Niveles jerárquicos
        self.niveles = {
            'director': 40,
            'coordinador': 30,
            'jefe': 25,
            'gerente': 30,
            'subdirector': 20,
            'titular': 35,
            'secretario': 35
        }
    
    def calcular_relevancia(self, cargo, area=""):
        """Calcula la relevancia de un contacto para AWS (0-100)"""
        if not cargo:
            return 0
            
        cargo_lower = cargo.lower()
        area_lower = area.lower() if area else ""
        
        # Puntuación base por nivel jerárquico
        puntuacion = 0
        for nivel, puntos in self.niveles.items():
            if nivel in cargo_lower:
                puntuacion += puntos
                break
        
        # Puntuación por cargo relevante
        for palabra, puntos in self.cargos_relevantes.items():
            if palabra in cargo_lower:
                puntuacion += puntos // 2  # Dividir entre 2 para no exceder 100
                break
        
        # Puntuación adicional por área
        if area_lower:
            for palabra, puntos in self.areas_relevantes.items():
                if palabra in area_lower:
                    puntuacion += puntos
                    break
        
        # Limitar a 100 puntos máximo
        return min(100, puntuacion)
    
    def generar_razon(self, cargo, area, puntuacion):
        """Genera una razón para la relevancia"""
        if puntuacion >= 90:
            return f"Alto nivel directivo en {cargo}" + (f" del área de {area}" if area else "")
        elif puntuacion >= 80:
            return f"Posición clave en {cargo}" + (f" relacionada con {area}" if area else "")
        elif puntuacion >= 70:
            return f"Rol importante en {cargo}" + (f" dentro de {area}" if area else "")
        elif puntuacion >= 60:
            return f"Posición relevante para decisiones en {cargo}"
        else:
            return f"Posición con potencial interés para AWS"
    
    def filtrar_contactos(self, archivo_csv, min_relevancia=60):
        """Filtra contactos de un archivo CSV por relevancia"""
        print(f"📊 Analizando archivo: {archivo_csv}")
        
        try:
            # Leer CSV
            df = pd.read_csv(archivo_csv)
            print(f"📋 Total contactos: {len(df)}")
            
            # Buscar columnas relevantes
            columnas = {
                'nombre': None,
                'cargo': None,
                'area': None,
                'email': None,
                'telefono': None
            }
            
            # Mapear columnas
            for col in df.columns:
                col_lower = col.lower()
                if 'nombre' in col_lower and 'persona' in col_lower:
                    columnas['nombre'] = col
                elif 'cargo' in col_lower or 'denominaci' in col_lower:
                    columnas['cargo'] = col
                elif 'area' in col_lower or 'adscripci' in col_lower:
                    columnas['area'] = col
                elif 'correo' in col_lower or 'email' in col_lower:
                    columnas['email'] = col
                elif 'tel' in col_lower or 'fono' in col_lower:
                    columnas['telefono'] = col
            
            print(f"🔍 Columnas encontradas: {columnas}")
            
            # Procesar contactos
            contactos_aws = []
            
            for _, row in df.iterrows():
                # Extraer datos
                nombre = self.extraer_valor(row, columnas['nombre'])
                cargo = self.extraer_valor(row, columnas['cargo'])
                area = self.extraer_valor(row, columnas['area'])
                email = self.extraer_valor(row, columnas['email'])
                telefono = self.extraer_valor(row, columnas['telefono'])
                
                # Calcular relevancia
                relevancia = self.calcular_relevancia(cargo, area)
                
                # Filtrar por relevancia mínima
                if relevancia >= min_relevancia:
                    razon = self.generar_razon(cargo, area, relevancia)
                    
                    contactos_aws.append({
                        'nombre': nombre,
                        'cargo': cargo,
                        'area': area,
                        'email': email,
                        'telefono': telefono,
                        'relevancia_aws': relevancia,
                        'razon': razon
                    })
            
            # Ordenar por relevancia
            contactos_aws.sort(key=lambda x: x['relevancia_aws'], reverse=True)
            
            print(f"✅ Contactos AWS encontrados: {len(contactos_aws)}")
            
            # Guardar resultados
            if contactos_aws:
                df_aws = pd.DataFrame(contactos_aws)
                archivo_salida = archivo_csv.replace('.csv', '_aws.csv')
                df_aws.to_csv(archivo_salida, index=False)
                print(f"💾 Resultados guardados en: {archivo_salida}")
            
            return contactos_aws
            
        except Exception as e:
            print(f"❌ Error procesando archivo: {e}")
            return []
    
    def extraer_valor(self, row, columna):
        """Extrae valor de una columna con manejo de errores"""
        if columna is None:
            return ""
        try:
            valor = row[columna]
            if pd.isna(valor):
                return ""
            return str(valor).strip()
        except:
            return ""
    
    def filtrar_directorio(self, directorio, min_relevancia=60):
        """Filtra todos los CSV en un directorio"""
        print(f"🔍 Buscando archivos CSV en: {directorio}")
        
        resultados = {}
        
        try:
            # Listar archivos CSV
            archivos_csv = [f for f in os.listdir(directorio) if f.endswith('.csv') and 'directorio' in f.lower()]
            print(f"📁 Archivos encontrados: {len(archivos_csv)}")
            
            for archivo in archivos_csv:
                ruta_completa = os.path.join(directorio, archivo)
                print(f"\n📄 Procesando: {archivo}")
                
                # Extraer nombre de entidad del archivo
                entidad = archivo.replace('directorio_', '').replace('.csv', '')
                entidad = entidad.replace('_', ' ').title()
                
                # Filtrar contactos
                contactos = self.filtrar_contactos(ruta_completa, min_relevancia)
                
                if contactos:
                    resultados[entidad] = contactos
            
            # Generar resumen consolidado
            if resultados:
                self.generar_resumen_consolidado(resultados, directorio)
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error procesando directorio: {e}")
            return {}
    
    def generar_resumen_consolidado(self, resultados, directorio):
        """Genera un Excel con todos los contactos AWS"""
        try:
            # Crear lista consolidada
            todos_contactos = []
            
            for entidad, contactos in resultados.items():
                for contacto in contactos:
                    contacto_con_entidad = contacto.copy()
                    contacto_con_entidad['entidad'] = entidad
                    todos_contactos.append(contacto_con_entidad)
            
            # Crear DataFrame
            df_consolidado = pd.DataFrame(todos_contactos)
            
            # Ordenar por relevancia
            df_consolidado = df_consolidado.sort_values(by=['relevancia_aws', 'entidad'], ascending=[False, True])
            
            # Guardar Excel
            archivo_salida = os.path.join(directorio, f"contactos_aws_consolidado.xlsx")
            df_consolidado.to_excel(archivo_salida, index=False)
            
            print(f"\n✅ Resumen consolidado guardado en: {archivo_salida}")
            print(f"📊 Total contactos AWS: {len(df_consolidado)}")
            
        except Exception as e:
            print(f"❌ Error generando resumen: {e}")

# Ejemplo de uso
if __name__ == "__main__":
    import glob
    import os
    
    # Buscar carpeta más reciente en Downloads
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    carpetas_busqueda = glob.glob(os.path.join(downloads_path, "AWS_VELCH_busqueda_*"))
    
    if carpetas_busqueda:
        # Ordenar por fecha de creación (más reciente primero)
        carpetas_busqueda.sort(key=os.path.getctime, reverse=True)
        carpeta_reciente = carpetas_busqueda[0]
        
        print(f"🔍 Usando carpeta más reciente: {carpeta_reciente}")
        
        # Filtrar contactos
        filtro = FiltroAWS()
        resultados = filtro.filtrar_directorio(carpeta_reciente)
        
        print("\n📊 RESUMEN FINAL:")
        for entidad, contactos in resultados.items():
            print(f"- {entidad}: {len(contactos)} contactos AWS")
    else:
        print("❌ No se encontraron carpetas de búsqueda")