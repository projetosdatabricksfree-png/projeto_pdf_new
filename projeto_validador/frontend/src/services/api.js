import axios from 'axios';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? '/api/v1' : 'http://127.0.0.1:8001/api/v1');

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const preflightApi = {
  /**
   * Upload PDF for multi-agent validation
   * @param {File} file
   * @param {{ onUploadProgress?: (percent0to100: number) => void }} [opts]
   */
  uploadPdf: async (file, opts = {}) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/validate', formData, {
      onUploadProgress: (evt) => {
        if (!evt.total || !opts.onUploadProgress) return;
        const pct = Math.round((evt.loaded / evt.total) * 100);
        opts.onUploadProgress(Math.min(100, Math.max(0, pct)));
      },
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
