import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const licenseAPI = {
  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Generate license
  generateLicense: async (email, deploymentId, licenseType) => {
    const response = await apiClient.post('/license/generate', {
      email,
      deployment_id: deploymentId,
      license_type: licenseType,
    });
    return response.data;
  },

  // Validate license
  validateLicense: async (licenseKey) => {
    const response = await apiClient.post('/license/validate', {
      license_key: licenseKey,
    });
    return response.data;
  },

  // Renew license
  renewLicense: async (currentLicenseKey, adminKey) => {
    const response = await apiClient.post('/license/renew', {
      current_license_key: currentLicenseKey,
      admin_key: adminKey,
    });
    return response.data;
  },

  // Get license types
  getLicenseTypes: async () => {
    const response = await apiClient.get('/license/types');
    return response.data;
  },
};

export default apiClient;
