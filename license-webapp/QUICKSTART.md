# PGAIView License Portal - Quick Start

## 🚀 Start the Portal (Easiest Way)

```bash
cd license-webapp
./start_portal.sh
```

This will:
1. ✅ Start the License Server on port 5000
2. ✅ Start the Web Portal on port 8080
3. ✅ Open your browser automatically

Then visit: **http://localhost:8080**

---

## 📋 Manual Start

### Step 1: Start License Server
```bash
python3 license_server.py
```

### Step 2: Start Web Portal
```bash
cd license-webapp
python3 -m http.server 8080
```

### Step 3: Open Browser
Go to: **http://localhost:8080**

---

## 🎯 Quick Usage

### Generate License
1. Enter email and deployment ID
2. Select license type (Trial/Standard/Enterprise)
3. Enter admin key: `pgaiview-admin-2024`
4. Click "Generate License"
5. Copy the license key

### Validate License
1. Paste license key
2. Click "Validate License"
3. View license details

---

## ⚙️ Configuration

Change License Server URL:
- Click ⚙️ (Settings) button
- Enter new URL
- Click Save

---

## 📞 Support

Need help? Check the full README.md file.
