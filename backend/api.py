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

class InvestigacionRequest(BaseModel):
    entidades: List[str]
    session_id: str

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
            from datetime import datetime
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'type': tipo
            }
            investigaciones_activas[session_id]['logs'].append(log_entry)
        
        total_entidades = len(entidades)
        
        for i, entidad in enumerate(entidades):
            log_callback(f"Investigando: {entidad}", "info")
            
            # Usar tu coordinador existente
            resultado = coordinador.investigar_entidad(entidad, log_callback)
            investigaciones_activas[session_id]['resultados'].append(resultado)
            
            # Actualizar progreso
            investigaciones_activas[session_id]['entidades_procesadas'] = i + 1
            investigaciones_activas[session_id]['progress'] = ((i + 1) / total_entidades) * 100
            
            log_callback(f"Completado: {entidad}", "success")
        
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
    """Exporta los resultados de una investigación"""
    if session_id not in investigaciones_activas:
        return {"error": "Sesión no encontrada"}
    
    resultados = investigaciones_activas[session_id]['resultados']
    
    try:
        filename = f"downloads/resumen_{session_id}.xlsx"
        coordinador.exportar_resultados(resultados, filename)
        return {"message": "Resultados exportados", "filename": filename}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)