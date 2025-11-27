# PGAIView License Portal - Quick Start Guide

## 🚀 One-Command Start

```bash
cd license-portal
./start.sh
```

This will:
1. ✅ Check dependencies
2. ✅ Install if needed  
3. ✅ Start backend (port 8000)
4. ✅ Start frontend (port 3000)
5. ✅ Open browser automatically

## 🌐 Access Points

- **Web Portal**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

## 🎯 Quick Usage

### Generate License
1. Enter email and deployment ID
2. Select type (Trial/Standard/Enterprise)
3. Enter admin key: `pgaiview-admin-2024`
4. Click "Generate"
5. Copy license key

### Validate License
1. Paste license key
2. Click "Validate"
3. View details

### Renew License
1. Paste current license
2. Enter admin key
3. Click "Renew"
4. Copy new key

## 🛠️ Manual Start

### Backend Only
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend Only
```bash
cd frontend
npm install
npm run dev
```

## 📱 Features

✨ Beautiful light theme  
📱 Mobile responsive  
🚀 Fast & lightweight  
🔐 Secure encryption  
⚡ Real-time validation  

## 🔑 Default Credentials

**Admin Key**: `pgaiview-admin-2024`

Change with environment variable:
```bash
export ADMIN_KEY="your-secure-key"
```

## 📞 Support

Check **README.md** for detailed documentation.

---

**Made for PGAIView** | Version 2.0
