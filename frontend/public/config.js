// Runtime configuration - loaded before React app
// For pgaiview Docker image: backend is proxied through nginx at /api/

window.ENV = {
  // Use nginx proxy path (no port needed in combined image)
  REACT_APP_API_URL: '/api/v1'
};

// Debug info
console.log('PGAIView Runtime Config:');
console.log('  API URL:', window.ENV.REACT_APP_API_URL);
