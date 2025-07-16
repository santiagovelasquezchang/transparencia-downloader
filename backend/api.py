from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
import json
import os
import sys

from coordinador import Coordinador

app = FastAPI(title="Transparencia API", version="1.0.0")

# CORS para permitir requests desde React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Estado global para manejar investigaciones
investigaciones_activas = {}
coordinador = Coordinador()

def crear_carpeta_busqueda():
    """Crea carpeta única para cada búsqueda en Downloads del usuario"""
    from datetime import datetime
    import os
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Obtener carpeta Downloads del usuario
    downloads_usuario = os.path.join(os.path.expanduser("~"), "Downloads")
    carpeta_busqueda = os.path.join(downloads_usuario, f"AWS_VELCH_busqueda_{timestamp}")
    
    os.makedirs(carpeta_busqueda, exist_ok=True)
    return carpeta_busqueda

class InvestigacionRequest(BaseModel):
    entidades: List[str]
    session_id: str

@app.post("/api/investigar")
async def iniciar_investigacion(request: InvestigacionRequest, background_tasks: BackgroundTasks):
    """Inicia investigación en background"""
    session_id = request.session_id
    
    # Crear carpeta única para esta búsqueda
    carpeta_busqueda = crear_carpeta_busqueda()
    
    # Inicializar estado de la investigación
    investigaciones_activas[session_id] = {
        'status': 'iniciando',
        'progress': 0,
        'logs': [],
        'resultados': [],
        'total_entidades': len(request.entidades),
        'entidades_procesadas': 0,
        'carpeta_busqueda': carpeta_busqueda
    }
    
    # Ejecutar investigación en background
    background_tasks.add_task(ejecutar_investigacion, request.entidades, session_id)
    
    return {"message": "Investigación iniciada", "session_id": session_id}

async def ejecutar_investigacion(entidades: List[str], session_id: str):
    """Ejecuta la investigación completa"""
    try:
        investigaciones_activas[session_id]['status'] = 'procesando'
        
        def log_callback(message: str, tipo: str = "info"):
            from datetime import datetime
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'type': tipo
            }
            investigaciones_activas[session_id]['logs'].append(log_entry)
        
        total_entidades = len(entidades)
        
        # Configurar carpeta de búsqueda para los agentes
        carpeta_busqueda = investigaciones_activas[session_id]['carpeta_busqueda']
        coordinador.agente_transparencia.set_download_path(carpeta_busqueda)
        coordinador.agente_contactos.set_download_path(carpeta_busqueda)
        
        # Inicializar lista de contactos AWS
        if 'contactos_aws' not in investigaciones_activas[session_id]:
            investigaciones_activas[session_id]['contactos_aws'] = []
        
        for i, entidad in enumerate(entidades):
            log_callback(f"Investigando: {entidad}", "info")
            
            # Usar tu coordinador existente
            resultado = coordinador.investigar_entidad(entidad, log_callback)
            investigaciones_activas[session_id]['resultados'].append(resultado)
            
            # FILTRAR INMEDIATAMENTE si transparencia fue exitosa
            if resultado['transparencia'].get('exito') and 'ruta_archivo' in resultado['transparencia']:
                try:
                    ruta_archivo = resultado['transparencia']['ruta_archivo']
                    if os.path.exists(ruta_archivo):
                        log_callback(f"📊 Filtrando contactos de {entidad}...", "info")
                        
                        from filtro_aws import FiltroAWS
                        filtro = FiltroAWS()
                        contactos_filtrados = filtro.filtrar_contactos(ruta_archivo)
                        
                        # Añadir entidad a cada contacto y agregarlo a la lista
                        for contacto in contactos_filtrados:
                            contacto['entidad'] = entidad
                            investigaciones_activas[session_id]['contactos_aws'].append(contacto)
                        
                        log_callback(f"✅ {entidad}: {len(contactos_filtrados)} contactos AWS encontrados", "success")
                        
                except Exception as e:
                    log_callback(f"⚠️ Error filtrando {entidad}: {e}", "warning")
            
            # Actualizar progreso
            investigaciones_activas[session_id]['entidades_procesadas'] = i + 1
            investigaciones_activas[session_id]['progress'] = ((i + 1) / total_entidades) * 100
            
            log_callback(f"Completado: {entidad}", "success")
        
        # El filtrado ya se hizo en tiempo real durante la investigación
        total_contactos = len(investigaciones_activas[session_id].get('contactos_aws', []))
        log_callback(f"🎯 Total contactos AWS filtrados: {total_contactos}", "success")
        
        investigaciones_activas[session_id]['status'] = 'completado'
        log_callback("¡Investigación completada!", "success")
        
    except Exception as e:
        investigaciones_activas[session_id]['status'] = 'error'
        investigaciones_activas[session_id]['error'] = str(e)

@app.get("/api/status/{session_id}")
async def obtener_status(session_id: str):
    """Obtiene el status actual de una investigación"""
    if session_id not in investigaciones_activas:
        return {"error": "Sesión no encontrada"}
    
    return investigaciones_activas[session_id]

@app.get("/api/logs/{session_id}")
async def obtener_logs(session_id: str, desde: int = 0):
    """Obtiene logs desde un índice específico"""
    if session_id not in investigaciones_activas:
        return {"logs": []}
    
    logs = investigaciones_activas[session_id]['logs'][desde:]
    return {"logs": logs, "total": len(investigaciones_activas[session_id]['logs'])}

@app.post("/api/exportar/{session_id}")
async def exportar_resultados(session_id: str):
    """Exporta los contactos AWS filtrados por Ollama"""
    if session_id not in investigaciones_activas:
        return {"error": "Sesión no encontrada"}
    
    try:
        carpeta_busqueda = investigaciones_activas[session_id].get('carpeta_busqueda', 'downloads')
        contactos_aws = investigaciones_activas[session_id].get('contactos_aws', [])
        
        if contactos_aws:
            # Agrupar por entidad para el Excel
            contactos_por_entidad = {}
            for contacto in contactos_aws:
                entidad = contacto['entidad']
                if entidad not in contactos_por_entidad:
                    contactos_por_entidad[entidad] = []
                contactos_por_entidad[entidad].append(contacto)
            
            # Generar Excel con contactos AWS
            archivo_aws = coordinador.generar_excel_aws(contactos_por_entidad, carpeta_busqueda)
            
            return {
                "message": "Contactos AWS exportados exitosamente",
                "archivo_aws": archivo_aws,
                "carpeta_busqueda": carpeta_busqueda
            }
        else:
            return {"error": "No hay contactos AWS para exportar"}
            
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/filtrar-contactos")
async def filtrar_contactos(request: dict):
    """Filtra contactos importantes de las instituciones especificadas"""
    try:
        instituciones = request.get('instituciones', [])
        
        from filtro_contactos import FiltroContactos
        filtro = FiltroContactos()
        
        archivo_filtrado = filtro.generar_reporte_filtrado(instituciones)
        
        return {
            "message": "Contactos filtrados exitosamente",
            "archivo": archivo_filtrado
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)