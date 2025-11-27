# PGAIView License Portal - Web Application

A beautiful, responsive web application for managing PGAIView licenses. Generate, validate, and renew licenses through an intuitive web interface.

![License Portal](https://img.shields.io/badge/License-Portal-blue)
![Status](https://img.shields.io/badge/Status-Active-success)

## ✨ Features

- 🎨 **Beautiful UI** - Modern, responsive design with smooth animations
- 🔐 **Secure** - Encrypted license generation and validation
- 📱 **Mobile Friendly** - Works perfectly on all devices
- ⚡ **Fast** - Instant license generation and validation
- 🎯 **Easy to Use** - Intuitive interface for non-technical users

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Flask and dependencies installed
- A running PGAIView License Server

### Installation

1. **Navigate to the license webapp directory:**
   ```bash
   cd /media/crl/Extra\ Disk31/PYTHON_CODE/DATABASEAI/DatabaseAI/license-webapp
   ```

2. **Start the License Server (in a separate terminal):**
   ```bash
   cd ..
   python3 license_server.py
   ```
   
   The license server will start on `http://localhost:5000`

3. **Open the Web Application:**
   
   **Option A: Using Python's built-in HTTP server**
   ```bash
   python3 -m http.server 8080
   ```
   
   Then open your browser to: `http://localhost:8080`
   
   **Option B: Using Node.js http-server (if installed)**
   ```bash
   npx http-server -p 8080
   ```
   
   **Option C: Direct file access**
   Simply double-click `index.html` or open it in your browser:
   ```bash
   firefox index.html
   # or
   google-chrome index.html
   ```

## 📖 Usage Guide

### 1. Generate License

Generate new licenses for your deployments:

1. Navigate to the **Generate License** tab
2. Fill in the form:
   - **Email Address**: User's email for registration
   - **Deployment ID**: Unique identifier (auto-generated or custom)
   - **License Type**: Choose from Trial (10 days), Standard (60 days), or Enterprise (365 days)
   - **Admin Key**: Authentication key (default: `pgaiview-admin-2024`)
3. Click **Generate License**
4. Copy the generated license key and provide it to the user

### 2. Validate License

Check if a license is valid:

1. Navigate to the **Validate License** tab
2. Paste the license key into the text area
3. Click **Validate License**
4. View the license details including:
   - Status (Valid/Expired)
   - License type
   - Deployment ID
   - Issue and expiry dates
   - Days remaining

### 3. Renew License

Extend an existing license:

1. Navigate to the **Renew License** tab
2. Paste the current license key
3. Enter the admin key
4. Click **Renew License**
5. A new license key will be generated with extended validity

## ⚙️ Configuration

### Change License Server URL

1. Click the **Settings** button (⚙️) in the bottom-right corner
2. Enter your License Server URL (default: `http://localhost:5000`)
3. Click **Save Settings**

The URL is saved in your browser's local storage.

### Admin Key

The default admin key is `pgaiview-admin-2024`. You can change it by:

1. Setting the `ADMIN_KEY` environment variable before starting the license server:
   ```bash
   export ADMIN_KEY="your-secure-admin-key"
   python3 license_server.py
   ```

2. Or edit `license_server.py` and change the default value.

## 🎨 Features Breakdown

### Beautiful Design
- Modern dark theme with gradient accents
- Smooth animations and transitions
- Card-based layout for better organization
- Responsive design for all screen sizes

### User Experience
- **Auto-generate** deployment IDs with one click
- **Copy to clipboard** functionality for license keys
- **Toast notifications** for user feedback
- **Form validation** to prevent errors
- **Loading states** during API calls

### License Types

| Type | Duration | Description |
|------|----------|-------------|
| **Trial** | 10 days | Perfect for testing |
| **Standard** | 60 days | 2 months access |
| **Enterprise** | 365 days | Full year license |

## 🔧 Advanced Usage

### Production Deployment

#### Using Nginx

1. **Copy files to web server:**
   ```bash
   sudo cp -r license-webapp /var/www/html/license-portal
   ```

2. **Configure Nginx:**
   ```nginx
   server {
       listen 80;
       server_name license.yourdomain.com;
       
       root /var/www/html/license-portal;
       index index.html;
       
       location / {
           try_files $uri $uri/ =404;
       }
   }
   ```

3. **Restart Nginx:**
   ```bash
   sudo systemctl restart nginx
   ```

#### Using Docker

Create a `Dockerfile`:
```dockerfile
FROM nginx:alpine
COPY license-webapp /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:
```bash
docker build -t license-portal .
docker run -d -p 8080:80 license-portal
```

### Custom Branding

1. **Change logo and title** in `index.html`:
   ```html
   <div class="logo">
       <i class="fas fa-key"></i>
       <span>Your Company License Portal</span>
   </div>
   ```

2. **Modify colors** in `styles.css`:
   ```css
   :root {
       --primary-color: #your-color;
       --gradient-1: your-gradient;
   }
   ```

3. **Update footer** in `index.html`:
   ```html
   <footer class="footer">
       <p>&copy; 2025 Your Company. All rights reserved.</p>
   </footer>
   ```

## 🔒 Security Considerations

1. **HTTPS**: Always use HTTPS in production
2. **Admin Key**: Change the default admin key to a strong, unique value
3. **CORS**: Configure CORS properly in production (restrict origins)
4. **Rate Limiting**: Consider adding rate limiting to prevent abuse
5. **Authentication**: Add user authentication for accessing the portal

## 🐛 Troubleshooting

### License Server Not Running
**Error**: "Request failed" or connection errors

**Solution**: 
```bash
# Check if license server is running
ps aux | grep license_server

# Start the license server
python3 license_server.py
```

### CORS Errors
**Error**: "Cross-Origin Request Blocked"

**Solution**: The license server already has CORS enabled. If issues persist:
```python
# In license_server.py, update CORS configuration:
CORS(app, resources={r"/*": {"origins": "*"}})
```

### Invalid Admin Key
**Error**: "Unauthorized"

**Solution**: Use the correct admin key or check environment variables:
```bash
echo $ADMIN_KEY
```

## 📱 Mobile Support

The portal is fully responsive and works on:
- 📱 Smartphones (iOS & Android)
- 💻 Tablets
- 🖥️ Desktop computers
- 📺 Large displays

## 🎯 Keyboard Shortcuts

- `Tab` - Navigate between form fields
- `Enter` - Submit active form
- `Esc` - Close settings modal

## 📊 Browser Compatibility

- ✅ Chrome/Edge (Latest)
- ✅ Firefox (Latest)
- ✅ Safari (Latest)
- ✅ Opera (Latest)

## 🤝 Integration with PGAIView

To use generated licenses in PGAIView:

1. Copy the generated license key
2. Open PGAIView application
3. Go to Settings → License
4. Paste the license key
5. Click Activate

## 📝 API Endpoints Used

The portal uses these license server endpoints:

- `POST /license/generate` - Generate new license
- `POST /license/validate` - Validate license
- `POST /license/renew` - Renew existing license
- `GET /health` - Check server health

## 🎓 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review license server logs
3. Consult PGAIView documentation

## 📄 License

This license portal is part of the PGAIView project.

---

**Made with ❤️ for PGAIView**
