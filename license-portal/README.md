# 🚀 PGAIView License Portal v2.0

A modern, professional license management system built with **FastAPI** and **React** with **Tailwind CSS**. Features a beautiful, lightweight, responsive design optimized for both desktop and mobile devices.

![License Portal](https://img.shields.io/badge/Version-2.0.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![React](https://img.shields.io/badge/React-18.2-blue)
![Tailwind](https://img.shields.io/badge/TailwindCSS-3.4-cyan)

## ✨ Features

### 🎨 Beautiful UI/UX
- **Modern Light Theme** - Professional, clean design
- **Fully Responsive** - Optimized for mobile, tablet, and desktop
- **Smooth Animations** - Polished transitions and interactions
- **Toast Notifications** - Real-time user feedback
- **Loading States** - Clear visual feedback during operations

### 🔐 License Management
- **Generate Licenses** - Create trial, standard, or enterprise licenses
- **Validate Licenses** - Check validity and view detailed information
- **Renew Licenses** - Extend existing licenses seamlessly
- **Auto-generate IDs** - One-click deployment ID generation
- **Copy to Clipboard** - Easy license key copying

### 🛠️ Technical Stack
- **Backend**: FastAPI with async support
- **Frontend**: React 18 with Vite
- **Styling**: Tailwind CSS with custom components
- **Icons**: Lucide React (lightweight)
- **Notifications**: React Hot Toast
- **API Client**: Axios

## 📁 Project Structure

```
license-portal/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
│
└── frontend/
    ├── src/
    │   ├── components/      # React components
    │   │   ├── GenerateLicense.jsx
    │   │   ├── ValidateLicense.jsx
    │   │   ├── RenewLicense.jsx
    │   │   ├── Button.jsx
    │   │   ├── Input.jsx
    │   │   ├── Card.jsx
    │   │   └── Toast.jsx
    │   ├── services/
    │   │   └── api.js       # API integration
    │   ├── App.jsx          # Main app component
    │   ├── main.jsx         # Entry point
    │   └── index.css        # Tailwind styles
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

### 1. Backend Setup

```bash
cd license-portal/backend

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server
python main.py
```

The backend will start on **http://localhost:8000**

### 2. Frontend Setup

```bash
cd license-portal/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start on **http://localhost:3000**

### 3. Open in Browser

Navigate to **http://localhost:3000** to access the license portal.

## 📖 Usage Guide

### Generate License

1. Click the **"Generate License"** tab
2. Enter the user's email address
3. Generate or enter a deployment ID
4. Select license type:
   - **Trial**: 10 days (for testing)
   - **Standard**: 60 days (2 months)
   - **Enterprise**: 365 days (full year)
5. Enter admin key (default: `pgaiview-admin-2024`)
6. Click **"Generate License"**
7. Copy the generated license key

### Validate License

1. Click the **"Validate License"** tab
2. Paste the license key
3. Click **"Validate License"**
4. View license details:
   - Status (Active/Expired)
   - License type
   - Days remaining
   - Issue and expiry dates

### Renew License

1. Click the **"Renew License"** tab
2. Paste the current license key
3. Enter admin key
4. Click **"Renew License"**
5. Copy the new license key

## 🔧 Configuration

### Backend Configuration

Edit `backend/main.py` or set environment variables:

```bash
# Custom admin key
export ADMIN_KEY="your-secure-admin-key"

# Custom secret key for encryption
export LICENSE_SECRET_KEY="your-secret-key"

# Custom port
export PORT=8000
```

### Frontend Configuration

Create `.env` file in `frontend/`:

```env
VITE_API_URL=http://localhost:8000/api
```

### Customize License Types

Edit `backend/main.py`:

```python
LICENSE_CONFIG = {
    'trial': {'days': 10, 'description': 'Trial License'},
    'standard': {'days': 60, 'description': 'Standard License'},
    'enterprise': {'days': 365, 'description': 'Enterprise License'},
    # Add more types...
}
```

## 🎨 Customization

### Theme Colors

Edit `frontend/tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom color palette
        500: '#your-color',
        600: '#your-color',
        // ...
      },
    },
  },
}
```

### Branding

Update header in `frontend/src/App.jsx`:

```jsx
<h1 className="text-xl font-bold">Your Company License Portal</h1>
```

## 📦 Production Deployment

### Backend (FastAPI)

```bash
cd backend

# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (React)

```bash
cd frontend

# Build for production
npm run build

# Serve with any static server
npx serve -s dist -p 3000
```

### Using Docker

Create `Dockerfile` in `backend/`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

Create `Dockerfile` in `frontend/`:

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

Create `docker-compose.yml` in root:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ADMIN_KEY=pgaiview-admin-2024

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

Run:
```bash
docker-compose up -d
```

## 🔒 Security Best Practices

1. **Change Default Admin Key**
   ```bash
   export ADMIN_KEY="your-strong-password"
   ```

2. **Use HTTPS in Production**
   - Set up SSL/TLS certificates
   - Use reverse proxy (Nginx/Caddy)

3. **Restrict CORS**
   Edit `backend/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       # ...
   )
   ```

4. **Environment Variables**
   - Never commit secrets to git
   - Use `.env` files (add to `.gitignore`)

## 📱 Mobile Responsiveness

The portal is fully optimized for mobile devices:

- **Responsive Layout**: Adapts to any screen size
- **Touch-Friendly**: Large tap targets for mobile
- **Optimized Typography**: Readable on small screens
- **Mobile Navigation**: Streamlined for mobile users

Breakpoints:
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

## 🎯 API Endpoints

### Health Check
```
GET /api/health
```

### Generate License
```
POST /api/license/generate
Body: {
  "email": "user@example.com",
  "deployment_id": "deploy-...",
  "license_type": "trial|standard|enterprise",
  "admin_key": "your-admin-key"
}
```

### Validate License
```
POST /api/license/validate
Body: {
  "license_key": "your-license-key"
}
```

### Renew License
```
POST /api/license/renew
Body: {
  "current_license_key": "existing-key",
  "admin_key": "your-admin-key"
}
```

### Get License Types
```
GET /api/license/types
```

### API Documentation
Visit **http://localhost:8000/api/docs** for interactive Swagger UI

## 🐛 Troubleshooting

### Backend Not Starting

**Issue**: Port 8000 already in use

**Solution**:
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
export PORT=8001
python main.py
```

### Frontend Build Errors

**Issue**: Module not found

**Solution**:
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### CORS Errors

**Issue**: Cross-origin requests blocked

**Solution**: Ensure backend CORS is configured correctly and both services are running

## 🚀 Performance

- **Lightweight**: Total frontend bundle < 500KB
- **Fast Load**: < 2 seconds on 3G
- **Optimized Images**: None required (icon-only)
- **Code Splitting**: Automatic with Vite
- **Caching**: Service worker ready

## 📊 Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS/Android)

## 🤝 Contributing

This is a proprietary application for PGAIView. For issues or feature requests, contact the development team.

## 📝 License

© 2025 PGAIView. All rights reserved.

---

## 🎉 What's New in v2.0

- ✨ Complete UI redesign with modern light theme
- 🚀 Rebuilt with React + FastAPI for better performance
- 📱 Enhanced mobile responsiveness
- 🎨 Professional Tailwind CSS styling
- ⚡ Faster load times with Vite
- 🔐 Improved security with FastAPI
- 📚 Interactive API documentation
- 🎯 Better error handling and validation

---

**Made with ❤️ for PGAIView**
