import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export class InvestigacionService {
  static async iniciarInvestigacion(entidades, sessionId) {
    const response = await axios.post(`${API_BASE_URL}/api/investigar`, {
      entidades,
      session_id: sessionId
    });
    return response.data;
  }

  static async obtenerStatus(sessionId) {
    const response = await axios.get(`${API_BASE_URL}/api/status/${sessionId}`);
    return response.data;
  }

  static async obtenerLogs(sessionId, desde = 0) {
    const response = await axios.get(`${API_BASE_URL}/api/logs/${sessionId}?desde=${desde}`);
    return response.data;
  }

  static async exportarResultados(sessionId) {
    const response = await axios.post(`${API_BASE_URL}/api/exportar/${sessionId}`);
    return response.data;
  }

  static async listarDescargas() {
    const response = await axios.get(`${API_BASE_URL}/api/downloads`);
    return response.data;
  }
}