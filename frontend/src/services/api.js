/**
 * API service for backend communication
 */
import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // System status
  async getStatus() {
    const response = await api.get('/status');
    return response.data;
  },

  // EULA
  async getEULA() {
    const response = await api.get('/eula');
    return response.data;
  },

  async acceptEULA() {
    const response = await api.post('/eula/accept', { accepted: true });
    return response.data;
  },

  // Indexing
  async startIndexing(docDir = null) {
    const response = await api.post('/index', { doc_dir: docDir });
    return response.data;
  },

  async getIndexStats() {
    const response = await api.get('/index/stats');
    return response.data;
  },

  // Folders
  async getFolders() {
    const response = await api.get('/folders');
    return response.data;
  },

  async removeFolder(folderPath) {
    const response = await api.delete(`/folders/${encodeURIComponent(folderPath)}`);
    return response.data;
  },

  // Query
  async query(query) {
    const response = await api.post('/query', {
      query,
      stream: false,
    });
    return response.data;
  },

  // Query with streaming
  async queryStream(query, onChunk, onError, onComplete) {
    const response = await fetch(`${API_BASE_URL}/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, stream: true }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            onChunk(data);
          }
        }
      }
      onComplete();
    } catch (error) {
      onError(error);
    }
  },
};

export default apiService;
