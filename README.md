# 🕵️ Transparencia Downloader - Investigador de Entidades

Un sistema automatizado de investigación dual que combina dos agentes especializados para obtener información completa de contactos de entidades gubernamentales mexicanas.

## 📋 Descripción

Este proyecto implementa un sistema de investigación automatizada que utiliza dos agentes trabajando en paralelo:

- **🤖 Agente Transparencia**: Valida nombres de instituciones y descarga directorios oficiales desde la Plataforma Nacional de Transparencia
- **🌐 Agente Contactos**: Busca páginas web oficiales y extrae información de contacto adicional

## ✨ Características Principales

### Agente Transparencia
- ✅ Validación inteligente de nombres de instituciones con corrección automática
- 🎯 Detección y conversión automática de estados mexicanos (formato completo ↔ abreviación)
- 📥 Descarga automática de directorios oficiales en formato Excel/CSV
- 🔍 Búsqueda con similitud fuzzy para encontrar coincidencias aproximadas
- 📊 Extracción completa de datos tabulares con todos los campos disponibles

### Agente Contactos
- 🔍 Búsqueda avanzada en Google con múltiples estrategias
- 🌐 Análisis de páginas web oficiales (.gob.mx prioritario)
- 📄 Procesamiento de múltiples formatos: HTML, PDF, imágenes
- 🖼️ OCR para extraer texto de organigramas en imagen
- 📞 Extracción inteligente de emails, teléfonos y cargos
- 🎯 Filtrado específico para directorios institucionales

### Interfaz Gráfica
- 🖥️ Interfaz moderna con CustomTkinter
- 📊 Log en tiempo real del progreso de investigación
- 📈 Barra de progreso y estadísticas detalladas
- 💾 Exportación consolidada de resultados
- 🎨 Diseño inspirado en colores de Amazon

## 🏗️ Arquitectura del Sistema

```
main.py                    # Interfaz gráfica principal
├── coordinador.py         # Coordinador que maneja ambos agentes en paralelo
├── agente_transparencia.py # Agente especializado en Plataforma de Transparencia
├── agente_contactos.py    # Agente especializado en búsqueda web
└── downloads/             # Carpeta con archivos descargados
```

### Flujo de Trabajo

1. **Entrada**: Usuario ingresa lista de entidades a investigar
2. **Coordinación**: El coordinador lanza ambos agentes en paralelo
3. **Agente Transparencia**: 
   - Valida el nombre en la plataforma oficial
   - Corrige automáticamente variaciones de estados
   - Descarga el directorio completo en Excel
4. **Agente Contactos**:
   - Busca la página oficial en Google
   - Analiza la estructura web buscando directorios
   - Extrae contactos de múltiples formatos
5. **Consolidación**: Resultados se combinan y exportan

## 🚀 Instalación

### Prerrequisitos
- Python 3.8+
- Google Chrome instalado
- ChromeDriver (se descarga automáticamente)

### Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### Dependencias Principales
- `selenium` - Automatización web
- `pandas` - Manipulación de datos
- `customtkinter` - Interfaz gráfica moderna
- `beautifulsoup4` - Parsing HTML
- `fuzzywuzzy` - Búsqueda por similitud
- `openpyxl` - Manejo de archivos Excel
- `requests` - Peticiones HTTP
- `PyPDF2` - Procesamiento de PDFs
- `pytesseract` - OCR para imágenes

## 💻 Uso

### Ejecución de la Aplicación

```bash
python main.py
```

### Proceso de Investigación

1. **Ingreso de Entidades**: Escriba las entidades a investigar, una por línea:
   ```
   Secretaría de Educación Pública
   Instituto Nacional Electoral
   Comisión Nacional de Derechos Humanos
   Secretaría de Salud de Nayarit
   ```

2. **Inicio de Investigación**: Haga clic en "🚀 Iniciar Investigación Dual"

3. **Monitoreo**: Observe el log en tiempo real para seguir el progreso

4. **Resultados**: Los archivos se guardan automáticamente en la carpeta `downloads/`

5. **Exportación**: Use "💾 Exportar Resultados Completos" para generar un resumen consolidado

## 📁 Estructura de Resultados

### Archivos Generados

```
downloads/
├── directorio_secretaria_de_educacion_publica.csv
├── directorio_web_instituto_nacional_electoral.csv
├── contactos_web_secretaria_de_economia_de_nayarit.csv
└── resumen_investigacion.xlsx
```

### Formato de Datos

**Directorio Transparencia (CSV)**:
- Ejercicio, Fecha_inicio, Fecha_termino
- Cargo, Nombre, Correo electrónico oficial
- Teléfono, Extensión, Departamento

**Contactos Web (CSV)**:
- Entidad, Fuente, Nombre, Cargo
- Email, Telefono, Departamento, URL_Fuente

**Resumen Consolidado (Excel)**:
- Hoja "Resumen_Investigacion": Estado de cada búsqueda
- Hoja "Contactos_Web": Todos los contactos web encontrados
- Hoja "Instrucciones": Guía de uso de los datos

## 🎯 Casos de Uso

### Investigación Periodística
- Obtener directorios completos de instituciones gubernamentales
- Verificar información de contacto oficial
- Acceder a organigramas actualizados

### Transparencia y Rendición de Cuentas
- Facilitar el acceso a información pública
- Automatizar solicitudes de información
- Monitorear cambios en estructuras organizacionales

### Investigación Académica
- Análisis de estructuras gubernamentales
- Estudios de transparencia institucional
- Mapeo de redes de contactos oficiales

## ⚙️ Configuración Avanzada

### Detección de Estados
El sistema incluye un diccionario completo de estados mexicanos con sus abreviaciones:

```python
estados_mexico = {
    'aguascalientes': 'AS',
    'baja california': 'BC',
    'nayarit': 'NT',
    'nuevo leon': 'NL',
    # ... todos los estados
}
```

### Palabras Clave para Directorios
```python
palabras_directorio = [
    'organigrama', 'directorio', 'directorio institucional',
    'funcionarios', 'autoridades', 'personal directivo',
    'estructura organizacional', 'quien es quien'
]
```

## 🔧 Solución de Problemas

### Problemas Comunes

**Error de ChromeDriver**:
```bash
# El sistema descarga automáticamente ChromeDriver
# Si hay problemas, actualice Chrome a la última versión
```

**Timeout en Selenium**:
- Aumente los tiempos de espera en el código
- Verifique la conexión a internet
- Algunos sitios pueden tener protecciones anti-bot

**No se encuentran contactos**:
- Verifique que la entidad tenga página web oficial
- Algunos sitios pueden no tener directorios públicos
- El OCR puede fallar con imágenes de baja calidad

### Logs y Debugging

El sistema proporciona logs detallados en tiempo real:
- ✅ Operaciones exitosas
- ⚠️ Advertencias y fallbacks
- ❌ Errores con descripción
- 📊 Estadísticas de progreso

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Áreas de mejora:

- Soporte para más formatos de documentos
- Mejoras en la precisión del OCR
- Integración con más fuentes de datos
- Optimización de velocidad de procesamiento

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.

## ⚠️ Consideraciones Legales

- Este software está diseñado para acceder únicamente a información pública
- Respeta los términos de servicio de los sitios web
- Implementa delays apropiados para no sobrecargar servidores
- Solo accede a datos disponibles públicamente según la Ley de Transparencia

## 📞 Soporte

Para reportar problemas o solicitar características:
1. Revise los logs detallados en la interfaz
2. Verifique la configuración de su sistema
3. Consulte la documentación de troubleshooting

---

**Desarrollado para facilitar el acceso a información pública y promover la transparencia gubernamental en México** 🇲🇽