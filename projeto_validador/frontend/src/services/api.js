import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const preflightApi = {
  /**
   * Upload PDF for multi-agent validation
   */
  uploadPdf: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  /**
   * Get job status (polling)
   */
  getJobStatus: async (jobId) => {
    const response = await api.get(`/jobs/${jobId}/status`);
    return response.data;
  },

  /**
   * Get full validation report
   */
  getReport: async (jobId) => {
    const response = await api.get(`/jobs/${jobId}/report`);
    return response.data;
  },

  /**
   * Health check
   */
  health: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
