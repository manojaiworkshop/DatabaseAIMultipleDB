#!/bin/sh
# Runtime environment variable injection for React app
# This script generates config.js with environment variables at container startup

# Default API URL (can be overridden by environment variable)
API_URL="${REACT_APP_API_URL:-http://localhost:8088/api/v1}"

# Generate config.js with runtime environment variables
cat > /usr/share/nginx/html/config.js <<EOF
// Runtime configuration - loaded before React app
// Generated at container startup
window.ENV = {
  REACT_APP_API_URL: '${API_URL}'
};
console.log('Runtime config loaded:', window.ENV);
EOF

echo "Generated config.js with API_URL: ${API_URL}"

# Start nginx
exec nginx -g 'daemon off;'
