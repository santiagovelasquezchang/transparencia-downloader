import React, { useState, useEffect } from 'react';
import {
  AppLayout,
  Header,
  ContentLayout,
  Container,
  SpaceBetween,
  Button,
  Textarea,
  ProgressBar,
  Alert,
  Box,
  Badge,
  Cards,
  TextContent,
  TopNavigation
} from '@cloudscape-design/components';
import '@cloudscape-design/global-styles/index.css';
import './App.css';
import { InvestigacionService } from './services/InvestigacionService';
import LogViewer from './components/LogViewer';

function App() {
  const [entidades, setEntidades] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [isInvestigating, setIsInvestigating] = useState(false);

  const placeholderText = `Secretaría de Educación Pública
Instituto Nacional Electoral
Comisión Nacional de Derechos Humanos
Secretaría de Salud de Nayarit`;

  const iniciarInvestigacion = async () => {
    if (!entidades.trim()) return;
    
    const entidadesList = entidades.split('\n').filter(e => e.trim());
    const newSessionId = Date.now().toString();
    
    setSessionId(newSessionId);
    setIsInvestigating(true);
    setLogs([{
      timestamp: new Date().toISOString(),
      message: '🚀 Iniciando investigación dual...',
      type: 'info'
    }, {
      timestamp: new Date().toISOString(),
      message: `📊 Procesando ${entidadesList.length} entidades`,
      type: 'info'
    }]);
    
    try {
      await InvestigacionService.iniciarInvestigacion(entidadesList, newSessionId);
    } catch (error) {
      console.error('Error iniciando investigación:', error);
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        message: `❌ Error: ${error.message}`,
        type: 'error'
      }]);
    }
  };

  const exportarResultados = async () => {
    if (!sessionId) return;
    
    // Agregar log de inicio de exportación
    setLogs(prev => [...prev, {
      timestamp: new Date().toISOString(),
      message: '📋 Iniciando exportación y filtrado...',
      type: 'info'
    }]);
    
    try {
      const response = await InvestigacionService.exportarResultados(sessionId);
      
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        message: `✅ Exportación completada: ${response.filename}`,
        type: 'success'
      }]);
      
      if (response.archivo_filtrado) {
        setLogs(prev => [...prev, {
          timestamp: new Date().toISOString(),
          message: `📋 Archivo filtrado: ${response.archivo_filtrado.split('/').pop()}`,
          type: 'success'
        }]);
      }
      
    } catch (error) {
      console.error('Error exportando:', error);
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        message: `❌ Error en exportación: ${error.message}`,
        type: 'error'
      }]);
    }
  };

  // Polling para obtener status y logs en tiempo real
  useEffect(() => {
    if (!sessionId) return;

    const interval = setInterval(async () => {
      try {
        const statusData = await InvestigacionService.obtenerStatus(sessionId);
        setStatus(statusData);
        
        const logsData = await InvestigacionService.obtenerLogs(sessionId, logs.length);
        if (logsData.logs.length > 0) {
          setLogs(prev => [...prev, ...logsData.logs]);
        }
        
        if (statusData.status === 'completado' || statusData.status === 'error') {
          setIsInvestigating(false);
        }
      } catch (error) {
        console.error('Error obteniendo status:', error);
      }
    }, 1000); // Polling cada segundo para tiempo real

    return () => clearInterval(interval);
  }, [sessionId, logs.length]);

  const getStatusBadge = () => {
    if (!status) return null;
    
    const statusConfig = {
      'iniciando': { color: 'blue', text: 'Iniciando' },
      'procesando': { color: 'in-progress', text: 'Procesando' },
      'completado': { color: 'success', text: 'Completado' },
      'error': { color: 'error', text: 'Error' }
    };
    
    const config = statusConfig[status.status] || { color: 'grey', text: status.status };
    return <Badge color={config.color}>{config.text}</Badge>;
  };

  return (
    <>
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(180deg, #FFF4E6 0%, #FFF8F0 30%, #FFFCF7 60%, #FFFFFF 100%)',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: -1
      }}></div>
      <div style={{
        minHeight: '100vh',
        position: 'relative'
      }}>
      <div style={{
        backgroundColor: '#232F3E',
        height: '60px',
        display: 'flex',
        alignItems: 'center',
        paddingLeft: '40px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <img 
            src="https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg" 
            alt="AWS" 
            style={{ height: '24px', filter: 'brightness(0) invert(1)' }}
          />
          <span style={{ 
            color: '#fff', 
            fontWeight: 'bold', 
            fontSize: '18px',
            fontFamily: 'Amazon Ember, sans-serif',
            textTransform: 'uppercase'
          }}>VELCH</span>
          <span style={{ color: '#ccc', fontSize: '18px' }}>|</span>
          <span style={{ 
            color: '#fff', 
            fontSize: '18px',
            fontFamily: 'Amazon Ember, sans-serif',
            textTransform: 'uppercase'
          }}>CONTACT FINDER LATAM</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginLeft: 'auto', marginRight: '40px' }}>
          <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <span style={{ 
              color: '#fff', 
              fontSize: '14px',
              fontFamily: 'Amazon Ember, sans-serif'
            }}>Soporte</span>
            <span style={{ color: '#fff', marginLeft: '5px' }}>▼</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <span style={{ 
              color: '#fff', 
              fontSize: '14px',
              fontFamily: 'Amazon Ember, sans-serif'
            }}>Cuenta</span>
            <span style={{ color: '#fff', marginLeft: '5px' }}>▼</span>
          </div>
        </div>
      </div>
      <AppLayout
        navigationHide
        toolsHide
        content={
        <div style={{ background: 'transparent' }}>
        <ContentLayout
          header={
            <div>
              <h1 style={{ 
                fontSize: '2.5rem', 
                fontWeight: 'bold', 
                color: '#232F3E',
                marginBottom: '10px',
                textAlign: 'left',
                fontFamily: 'Amazon Ember, sans-serif',
                textTransform: 'uppercase'
              }}>
                INVESTIGADOR DE ENTIDADES
              </h1>
              <p style={{ 
                fontSize: '1.2rem', 
                color: '#666',
                margin: 0,
                textAlign: 'left',
                fontFamily: 'Amazon Ember, sans-serif'
              }}>
                Sistema automatizado de investigación dual para entidades gubernamentales mexicanas
              </p>
            </div>
          }
        >
          <div style={{ marginTop: '20px' }}>
          <SpaceBetween direction="vertical" size="l">
            
            {/* Panel de Control */}
            <Container
              header={
                <h2 style={{ 
                  fontSize: '1.8rem', 
                  fontWeight: 'bold', 
                  color: '#232F3E',
                  margin: 0,
                  fontFamily: 'Amazon Ember, sans-serif',
                  textTransform: 'uppercase'
                }}>
                  PANEL DE INVESTIGACIÓN
                </h2>
              }
            >
              <SpaceBetween direction="vertical" size="m">
                <Box>
                  <TextContent>
                    <p>🤖 <strong>Agente Transparencia:</strong> Valida nombres → Descarga Excel directorio oficial</p>
                    <p>🌐 <strong>Agente Contactos:</strong> Busca página oficial → Extrae contactos adicionales</p>
                  </TextContent>
                </Box>
                
                <Textarea
                  value={entidades}
                  onChange={({ detail }) => setEntidades(detail.value)}
                  placeholder={placeholderText}
                  rows={8}
                />
                
                <SpaceBetween direction="horizontal" size="s">
                  <Button
                    variant="primary"
                    onClick={iniciarInvestigacion}
                    disabled={isInvestigating || !entidades.trim()}
                    loading={isInvestigating}
                  >
                    INICIAR INVESTIGACIÓN DUAL
                  </Button>
                  
                  <Button
                    onClick={exportarResultados}
                    disabled={!status || status.status !== 'completado'}
                  >
                    EXPORTAR Y FILTRAR CONTACTOS
                  </Button>
                </SpaceBetween>
                
                {status && (
                  <SpaceBetween direction="vertical" size="s">
                    <Box>
                      <SpaceBetween direction="horizontal" size="s">
                        <span>Estado:</span>
                        {getStatusBadge()}
                        <span>{status.entidades_procesadas}/{status.total_entidades} entidades</span>
                      </SpaceBetween>
                    </Box>
                    
                    <ProgressBar
                      value={status.progress || 0}
                      additionalInfo={`${Math.round(status.progress || 0)}%`}
                      description="Progreso de investigación"
                    />
                  </SpaceBetween>
                )}
              </SpaceBetween>
            </Container>

            {/* Contenedor para Resultados y Estado lado a lado */}
            <div style={{ display: 'flex', gap: '20px' }}>
              
              {/* Resultados */}
              {status && status.resultados && status.resultados.length > 0 && (
                <div style={{ flex: 1 }}>
                  <Container
                    header={
                      <h2 style={{ 
                        fontSize: '1.8rem', 
                        fontWeight: 'bold', 
                        color: '#232F3E',
                        margin: 0,
                        fontFamily: 'Amazon Ember, sans-serif',
                        textTransform: 'uppercase'
                      }}>
                        RESULTADOS DE INVESTIGACIÓN
                      </h2>
                    }
                  >
                <Cards
                  cardDefinition={{
                    header: item => item.entidad,
                    sections: [
                      {
                        id: "transparencia",
                        header: "🤖 Agente Transparencia",
                        content: item => (
                          <SpaceBetween direction="vertical" size="xs">
                            <Box>
                              <Badge color={item.transparencia.exito ? "success" : "error"}>
                                {item.transparencia.exito ? "✅ Exitoso" : "❌ Falló"}
                              </Badge>
                            </Box>
                            {item.transparencia.institucion_validada && (
                              <Box>Institución: {item.transparencia.institucion_validada}</Box>
                            )}
                            {item.transparencia.similitud && (
                              <Box>Similitud: {item.transparencia.similitud}%</Box>
                            )}
                          </SpaceBetween>
                        )
                      },
                      {
                        id: "contactos",
                        header: "🌐 Agente Contactos",
                        content: item => (
                          <SpaceBetween direction="vertical" size="xs">
                            <Box>
                              <Badge color={item.contactos.exito ? "success" : "error"}>
                                {item.contactos.exito ? "✅ Exitoso" : "❌ Falló"}
                              </Badge>
                            </Box>
                            {item.contactos.datos?.url_oficial && (
                              <Box>URL: {item.contactos.datos.url_oficial}</Box>
                            )}
                            {item.contactos.datos?.contactos && (
                              <Box>Contactos: {item.contactos.datos.contactos.length}</Box>
                            )}
                          </SpaceBetween>
                        )
                      }
                    ]
                  }}
                  cardsPerRow={[
                    { cards: 1 },
                    { minWidth: 500, cards: 2 }
                  ]}
                  items={status.resultados}
                />
                  </Container>
                </div>
              )}
              
              {/* Log Viewer */}
              <div style={{ flex: 1 }}>
                <LogViewer logs={logs} />
              </div>
              
            </div>



            {/* Alertas */}
            {status?.status === 'error' && (
              <Alert type="error" header="Error en la investigación">
                {status.error}
              </Alert>
            )}
            
            {status?.status === 'completado' && (
              <Alert type="success" header="¡Investigación completada!">
                Se procesaron {status.total_entidades} entidades. Los archivos están disponibles en la carpeta downloads.
              </Alert>
            )}

          </SpaceBetween>
          </div>
        </ContentLayout>
        </div>
      }
      />
    </div>
    </>
  );
}

export default App;