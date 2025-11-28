/**
 * API Service for backend communication
 */
import axios from 'axios';

// Dynamically determine API URL based on current host
const getApiBaseUrl = () => {
  // Check for runtime config first
  if (window.ENV?.REACT_APP_API_URL) {
    return window.ENV.REACT_APP_API_URL;
  }
  
  // Check for build-time env variable
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Dynamically construct from window.location
  const protocol = window.location.protocol; // http: or https:
  const hostname = window.location.hostname;  // IP or domain
  
  // In Docker/production, use same host (nginx proxies /api/ to backend)
  // In development, use port 8088
  if (hostname === 'localhost' && window.location.port === '') {
    // Docker setup - use nginx proxy
    return `${protocol}//${hostname}/api/v1`;
  } else if (window.location.port === '3000') {
    // Development - React dev server
    return `http://localhost:8088/api/v1`;
  } else {
    // Use same host/port as frontend
    return `${protocol}//${hostname}${window.location.port ? ':' + window.location.port : ''}/api/v1`;
  }
};

const API_BASE_URL = getApiBaseUrl(); 

console.log('API Base URL:', API_BASE_URL);

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Database connection
  connectDatabase: async (connectionData) => {
    const response = await apiClient.post('/database/connect', connectionData);
    return response.data;
  },

  // Database disconnection
  disconnectDatabase: async () => {
    const response = await apiClient.post('/database/disconnect');
    return response.data;
  },

  // Get database snapshot
  getDatabaseSnapshot: async () => {
    const response = await apiClient.get('/database/snapshot');
    return response.data;
  },

  // Get all schemas
  getAllSchemas: async () => {
    const response = await apiClient.get('/database/schemas');
    return response.data;
  },

  // Get schema-specific snapshot
  getSchemaSnapshot: async (schemaName) => {
    const response = await apiClient.get(`/database/schemas/${schemaName}/snapshot`);
    return response.data;
  },

  // Select tables to work with
  selectTables: async (tables) => {
    const response = await apiClient.post('/database/select-tables', { tables });
    return response.data;
  },

  // Get selected tables
  getSelectedTables: async () => {
    const response = await apiClient.get('/database/selected-tables');
    return response.data;
  },

  // Query database
  queryDatabase: async (queryData) => {
    const response = await apiClient.post('/query', queryData);
    return response.data;
  },

  // Configure LLM
  configureLLM: async (config) => {
    const response = await apiClient.post('/llm/configure', config);
    return response.data;
  },

  // Settings endpoints
  getSettings: async () => {
    const response = await apiClient.get('/settings/all');
    return response.data;
  },

  updateSettings: async (sectionOrPayload, settings = null) => {
    // Support both calling patterns:
    // 1. updateSettings({ section: 'neo4j', settings: {...} })
    // 2. updateSettings('neo4j', {...})
    const payload = typeof sectionOrPayload === 'string' 
      ? { section: sectionOrPayload, settings } 
      : sectionOrPayload;
    const response = await apiClient.put('/settings/update', payload);
    return response.data;
  },

  // LLM Provider settings
  getOpenAISettings: async () => {
    const response = await apiClient.get('/settings/openai');
    return response.data;
  },

  updateOpenAISettings: async (settings) => {
    const response = await apiClient.put('/settings/update', { section: 'openai', settings });
    return response.data;
  },

  getVLLMSettings: async () => {
    const response = await apiClient.get('/settings/vllm');
    return response.data;
  },

  updateVLLMSettings: async (settings) => {
    const response = await apiClient.put('/settings/update', { section: 'vllm', settings });
    return response.data;
  },

  getOllamaSettings: async () => {
    const response = await apiClient.get('/settings/ollama');
    return response.data;
  },

  updateOllamaSettings: async (settings) => {
    const response = await apiClient.put('/settings/update', { section: 'ollama', settings });
    return response.data;
  },

  // License endpoints
  validateLicense: async (licenseKey) => {
    const response = await apiClient.post('/license/validate', { license_key: licenseKey });
    return response.data;
  },

  getLicenseInfo: async () => {
    const response = await apiClient.get('/license/info');
    return response.data;
  },

  activateLicense: async (licenseKey) => {
    const response = await apiClient.post('/license/activate', { license_key: licenseKey });
    return response.data;
  },

  updateLicenseKey: async (licenseKey) => {
    const response = await apiClient.put('/license/key', { license_key: licenseKey });
    return response.data;
  },

  getLicenseServerConfig: async () => {
    const response = await apiClient.get('/license/server-config');
    return response.data;
  },

  updateLicenseServerConfig: async (serverUrl) => {
    const response = await apiClient.put('/license/server-config', { server_url: serverUrl });
    return response.data;
  },

  // Neo4j Knowledge Graph endpoints
  testNeo4jConnection: async (connectionData) => {
    const response = await apiClient.post('/settings/neo4j/test', connectionData);
    return response.data;
  },

  syncSchemaToNeo4j: async (syncOptions) => {
    const response = await apiClient.post('/settings/neo4j/sync', syncOptions);
    return response.data;
  },

  getNeo4jStatus: async () => {
    const response = await apiClient.get('/settings/neo4j/status');
    return response.data;
  },

  getTableInsights: async (tableName) => {
    const response = await apiClient.get(`/settings/neo4j/insights/${tableName}`);
    return response.data;
  },

  // Ontology Management
  getOntologySettings: async () => {
    const response = await apiClient.get('/ontology/settings');
    return response;
  },

  updateOntologySettings: async (settings) => {
    const response = await apiClient.put('/ontology/settings', settings);
    return response;
  },

  generateDynamicOntology: async (options = {}) => {
    const response = await apiClient.post('/ontology/generate', options);
    return response;
  },

  listOntologyFiles: async () => {
    const response = await apiClient.get('/ontology/files');
    return response;
  },

  downloadOntologyFile: async (filename) => {
    const response = await apiClient.get(`/ontology/download/${filename}`, {
      responseType: 'text'
    });
    return response;
  },
};

// Export individual functions for easier imports
export const {
  healthCheck,
  connectDatabase,
  disconnectDatabase,
  getDatabaseSnapshot,
  getAllSchemas,
  getSchemaSnapshot,
  queryDatabase,
  configureLLM,
  getSettings,
  updateSettings,
  getOpenAISettings,
  updateOpenAISettings,
  getVLLMSettings,
  updateVLLMSettings,
  getOllamaSettings,
  updateOllamaSettings,
  validateLicense,
  getLicenseInfo,
  activateLicense,
  getLicenseServerConfig,
  updateLicenseServerConfig,
  testNeo4jConnection,
  syncSchemaToNeo4j,
  getNeo4jStatus,
  getTableInsights,
  getOntologySettings,
  updateOntologySettings,
  generateDynamicOntology,
  listOntologyFiles,
  downloadOntologyFile,
} = api;

export default api;

