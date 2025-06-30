import React from 'react';
import {
  Container,
  Header,
  Box,
  SpaceBetween,
  Badge
} from '@cloudscape-design/components';

const LogViewer = ({ logs }) => {
  const getLogIcon = (type) => {
    const icons = {
      'info': 'ℹ️',
      'success': '✅',
      'error': '❌',
      'warning': '⚠️',
      'download': '📥',
      'search': '🔍'
    };
    return icons[type] || '📝';
  };

  const getLogBadgeColor = (type) => {
    const colors = {
      'info': 'blue',
      'success': 'success',
      'error': 'error',
      'warning': 'warning',
      'download': 'blue',
      'search': 'blue'
    };
    return colors[type] || 'grey';
  };

  // Filtrar solo logs esenciales
  const getEssentialLogs = (logs) => {
    return logs.filter(log => {
      const message = log.message.toLowerCase();
      return (
        message.includes('investigando:') ||
        message.includes('completado:') ||
        message.includes('excel descargado:') ||
        message.includes('contactos extraídos:') ||
        message.includes('página encontrada:') ||
        message.includes('error') ||
        message.includes('completada')
      );
    }).slice(-10); // Solo últimos 10 logs esenciales
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const essentialLogs = getEssentialLogs(logs);

  return (
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
          📋 ESTADO DE INVESTIGACIÓN
        </h2>
      }
    >
      <Box>
        {essentialLogs.length === 0 ? (
          <Box textAlign="center" color="text-body-secondary">
            Esperando inicio de investigación...
          </Box>
        ) : (
          <SpaceBetween direction="vertical" size="s">
            {essentialLogs.map((log, index) => (
              <Box key={index} padding="s" style={{
                backgroundColor: '#fff',
                borderRadius: '8px',
                border: '1px solid #e9ecef'
              }}>
                <SpaceBetween direction="horizontal" size="s" alignItems="center">
                  <Badge color={getLogBadgeColor(log.type)}>
                    {getLogIcon(log.type)}
                  </Badge>
                  <Box>{log.message}</Box>
                  <Box fontSize="body-s" color="text-body-secondary">
                    {formatTimestamp(log.timestamp)}
                  </Box>
                </SpaceBetween>
              </Box>
            ))}
          </SpaceBetween>
        )}
      </Box>
    </Container>
  );
};

export default LogViewer;