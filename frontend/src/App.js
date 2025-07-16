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
  const [isExporting, setIsExporting] = useState(false);

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
    
    setIsExporting(true);
    
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
          message: `📋 Archivo filtrado creado: ${response.archivo_filtrado.split('/').pop()}`,
          type: 'success'
        }]);
      }
      
      if (response.carpeta_busqueda) {
        setLogs(prev => [...prev, {
          timestamp: new Date().toISOString(),
          message: `📂 Archivos guardados en: ${response.carpeta_busqueda.split('/').pop()}`,
          type: 'info'
        }]);
      }
      
    } catch (error) {
      console.error('Error exportando:', error);
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        message: `❌ Error en exportación: ${error.message}`,
        type: 'error'
      }]);
    } finally {
      setIsExporting(false);
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
                    loadingText="Investigando..."
                  >
                    {isInvestigating ? 'INVESTIGANDO...' : 'INICIAR INVESTIGACIÓN DUAL'}
                  </Button>
                  
                  <Button
                    onClick={exportarResultados}
                    disabled={!status || status.status !== 'completado' || isExporting}
                    loading={isExporting}
                    loadingText="Exportando..."
                  >
                    {isExporting ? 'EXPORTANDO...' : 'EXPORTAR Y FILTRAR CONTACTOS'}
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

            {/* 4 PANELES ORGANIZADOS */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
              
              {/* PANEL 2: URLs de Contactos */}
              <Container
                header={
                  <h3 style={{ 
                    fontSize: '1.4rem', 
                    fontWeight: 'bold', 
                    color: '#0073BB',
                    margin: 0,
                    fontFamily: 'Amazon Ember, sans-serif'
                  }}>
                    🌐 PANEL 2: URLs DE DIRECTORIOS
                  </h3>
                }
              >
                {status && status.resultados && status.resultados.length > 0 ? (
                  <SpaceBetween direction="vertical" size="s">
                    {status.resultados.map((item, index) => (
                      <Box key={index} padding="s" color="background-container-content">
                        <SpaceBetween direction="vertical" size="xs">
                          <Box><strong>🏢 {item.entidad}</strong></Box>
                          <Box>
                            <Badge color={item.contactos.exito ? "success" : "error"}>
                              {item.contactos.exito ? "✅ URL Encontrada" : "❌ No Encontrada"}
                            </Badge>
                          </Box>
                          {item.contactos.url_oficial && (
                            <Box fontSize="body-s">
                              <strong>Página:</strong><br/>
                              <a href={item.contactos.url_oficial} target="_blank" rel="noopener noreferrer" style={{color: '#0073BB'}}>
                                {item.contactos.url_oficial.length > 50 ? item.contactos.url_oficial.substring(0, 50) + '...' : item.contactos.url_oficial}
                              </a>
                            </Box>
                          )}
                          {item.contactos.url_directorio && item.contactos.url_directorio !== item.contactos.url_oficial && (
                            <Box fontSize="body-s">
                              <strong>Directorio:</strong><br/>
                              <a href={item.contactos.url_directorio} target="_blank" rel="noopener noreferrer" style={{color: '#0073BB'}}>
                                {item.contactos.url_directorio.length > 50 ? item.contactos.url_directorio.substring(0, 50) + '...' : item.contactos.url_directorio}
                              </a>
                            </Box>
                          )}
                        </SpaceBetween>
                      </Box>
                    ))}
                  </SpaceBetween>
                ) : (
                  <Box textAlign="center" color="text-status-inactive">
                    🔍 Esperando resultados de búsqueda...
                  </Box>
                )}
              </Container>

              {/* PANEL 3: Agente Transparencia */}
              <Container
                header={
                  <h3 style={{ 
                    fontSize: '1.4rem', 
                    fontWeight: 'bold', 
                    color: '#067D62',
                    margin: 0,
                    fontFamily: 'Amazon Ember, sans-serif'
                  }}>
                    📊 PANEL 3: AGENTE TRANSPARENCIA
                  </h3>
                }
              >
                {status && status.resultados && status.resultados.length > 0 ? (
                  <SpaceBetween direction="vertical" size="s">
                    {status.resultados.map((item, index) => (
                      <Box key={index} padding="s" color="background-container-content">
                        <SpaceBetween direction="vertical" size="xs">
                          <Box><strong>🏢 {item.entidad}</strong></Box>
                          <Box>
                            <Badge color={item.transparencia.exito ? "success" : "error"}>
                              {item.transparencia.exito ? "✅ Excel Descargado" : "❌ Error"}
                            </Badge>
                          </Box>
                          {item.transparencia.exito && (
                            <>
                              {item.transparencia.total_registros && (
                                <Box fontSize="body-s">
                                  <strong>Registros:</strong> {item.transparencia.total_registros}
                                </Box>
                              )}
                              {item.transparencia.total_columnas && (
                                <Box fontSize="body-s">
                                  <strong>Columnas:</strong> {item.transparencia.total_columnas}
                                </Box>
                              )}
                              {item.transparencia.similitud && (
                                <Box fontSize="body-s">
                                  <strong>Similitud:</strong> {item.transparencia.similitud}%
                                </Box>
                              )}
                            </>
                          )}
                          {!item.transparencia.exito && item.transparencia.error && (
                            <Box fontSize="body-s" color="text-status-error">
                              {item.transparencia.error}
                            </Box>
                          )}
                        </SpaceBetween>
                      </Box>
                    ))}
                  </SpaceBetween>
                ) : (
                  <Box textAlign="center" color="text-status-inactive">
                    📊 Esperando descarga de directorios...
                  </Box>
                )}
              </Container>

              {/* PANEL 4: Contactos AWS Filtrados */}
              <Container
                header={
                  <h3 style={{ 
                    fontSize: '1.4rem', 
                    fontWeight: 'bold', 
                    color: '#FF9900',
                    margin: 0,
                    fontFamily: 'Amazon Ember, sans-serif'
                  }}>
                    🎯 PANEL 4: CONTACTOS AWS FILTRADOS
                  </h3>
                }
                style={{ gridColumn: 'span 2' }}
              >
                {status && status.contactos_aws && status.contactos_aws.length > 0 ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '15px' }}>
                    {status.contactos_aws.map((contacto, index) => (
                      <Box key={index} padding="m" color="background-container-content">
                        <SpaceBetween direction="vertical" size="xs">
                          <Box><strong>👤 {contacto.nombre}</strong></Box>
                          <Box fontSize="body-s"><strong>🏢 {contacto.entidad}</strong></Box>
                          <Box fontSize="body-s">💼 {contacto.cargo}</Box>
                          <Box fontSize="body-s">📧 {contacto.email}</Box>
                          <Box fontSize="body-s">📞 {contacto.telefono}</Box>
                          <Box>
                            <Badge color={contacto.relevancia_aws >= 80 ? "success" : contacto.relevancia_aws >= 60 ? "warning" : "error"}>
                              🎯 {contacto.relevancia_aws}% AWS
                            </Badge>
                          </Box>
                          <Box fontSize="body-s" color="text-body-secondary">
                            <em>{contacto.razon}</em>
                          </Box>
                        </SpaceBetween>
                      </Box>
                    ))}
                  </div>
                ) : (
                  <Box textAlign="center" color="text-status-inactive">
                    📊 Esperando filtrado de contactos...
                  </Box>
                )}
              </Container>

              {/* Log Viewer - Ocupa toda la fila inferior */}
              <div style={{ gridColumn: 'span 2' }}>
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