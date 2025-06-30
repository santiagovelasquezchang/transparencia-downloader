from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
import json
import os
import time
from datetime import datetime

app = FastAPI(title="Transparencia API", version="1.0.0")

# CORS para permitir requests desde React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado global para manejar investigaciones
investigaciones_activas = {}

class InvestigacionRequest(BaseModel):
    entidades: List[str]
    session_id: str

# Simulador de agentes para testing
class SimuladorAgentes:
    def investigar_entidad(self, entidad, log_callback):
        """Simula investigación de entidad"""
        log_callback(f"🎯 === Investigando: {entidad} ===", "info")
        
        # Simular Agente Transparencia
        log_callback(f"🤖 Agente Transparencia: Validando y descargando Excel...", "download")
        time.sleep(2)
        log_callback(f"✅ Nombre exacto encontrado: {entidad}", "success")
        log_callback(f"📥 Excel descargado: directorio_{entidad.lower().replace(' ', '_')}.csv", "download")
        
        # Simular Agente Contactos
        log_callback(f"🌐 Agente Contactos: Buscando en web...", "search")
        time.sleep(1)
        log_callback(f"✅ Página encontrada: https://{entidad.lower().replace(' ', '')}.gob.mx", "success")
        log_callback(f"📞 Contactos extraídos: 15", "success")
        
        return {
            'entidad': entidad,
            'timestamp': datetime.now().isoformat(),
            'transparencia': {
                'exito': True,
                'error': None,
                'institucion_validada': entidad,
                'similitud': 100,
                'archivo_descargado': True,
                'ruta_archivo': f"downloads/directorio_{entidad.lower().replace(' ', '_')}.csv",
                'total_registros': 45,
                'total_emails': 12
            },
            'contactos': {
                'exito': True,
                'error': None,
                'datos': {
                    'url_oficial': f"https://{entidad.lower().replace(' ', '')}.gob.mx",
                    'contactos': [
                        {
                            'nombre': 'Director General',
                            'cargo': 'Dirección General',
                            'email': f'director@{entidad.lower().replace(" ", "")}.gob.mx',
                            'telefono': '55-1234-5678'
                        },
                        {
                            'nombre': 'Coordinador de Transparencia',
                            'cargo': 'Coordinación',
                            'email': f'transparencia@{entidad.lower().replace(" ", "")}.gob.mx',
                            'telefono': '55-8765-4321'
                        }
                    ],
                    'total_contactos': 15
                }
            }
        }

coordinador = SimuladorAgentes()

@app.post("/api/investigar")
async def iniciar_investigacion(request: InvestigacionRequest, background_tasks: BackgroundTasks):
    """Inicia investigación en background"""
    session_id = request.session_id
    
    # Inicializar estado de la investigación
    investigaciones_activas[session_id] = {
        'status': 'iniciando',
        'progress': 0,
        'logs': [],
        'resultados': [],
        'total_entidades': len(request.entidades),
        'entidades_procesadas': 0
    }
    
    # Ejecutar investigación en background
    background_tasks.add_task(ejecutar_investigacion, request.entidades, session_id)
    
    return {"message": "Investigación iniciada", "session_id": session_id}

async def ejecutar_investigacion(entidades: List[str], session_id: str):
    """Ejecuta la investigación completa"""
    try:
        investigaciones_activas[session_id]['status'] = 'procesando'
        
        def log_callback(message: str, tipo: str = "info"):
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'type': tipo
            }
            investigaciones_activas[session_id]['logs'].append(log_entry)
        
        log_callback("🚀 Iniciando sistema de investigación dual", "info")
        log_callback("🤖 Agente 1: Plataforma Transparencia (Excel Directorio)", "info")
        log_callback("🌐 Agente 2: Búsqueda Web Contactos", "info")
        
        total_entidades = len(entidades)
        
        for i, entidad in enumerate(entidades):
            # Usar coordinador simulado
            resultado = coordinador.investigar_entidad(entidad, log_callback)
            investigaciones_activas[session_id]['resultados'].append(resultado)
            
            # Actualizar progreso
            investigaciones_activas[session_id]['entidades_procesadas'] = i + 1
            investigaciones_activas[session_id]['progress'] = ((i + 1) / total_entidades) * 100
            
            log_callback(f"Completado: {entidad}", "success")
        
        investigaciones_activas[session_id]['status'] = 'completado'
        log_callback("🎉 ¡Investigación completada!", "success")
        
        # Estadísticas finales
        log_callback(f"📈 Total entidades: {total_entidades}", "info")
        log_callback(f"📥 Excel directorios descargados: {total_entidades}/{total_entidades}", "success")
        log_callback(f"🌐 Páginas web analizadas: {total_entidades}/{total_entidades}", "success")
        
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
    """Exporta los resultados de una investigación"""
    if session_id not in investigaciones_activas:
        return {"error": "Sesión no encontrada"}
    
    try:
        filename = f"downloads/resumen_{session_id}.json"
        
        # Crear directorio si no existe
        os.makedirs("downloads", exist_ok=True)
        
        # Guardar como JSON simple
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(investigaciones_activas[session_id]['resultados'], f, indent=2, ensure_ascii=False)
        
        return {"message": "Resultados exportados", "filename": filename}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Transparencia API funcionando", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Transparencia API...")
    print("📡 Backend disponible en: http://localhost:8000")
    print("📋 Documentación API: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)