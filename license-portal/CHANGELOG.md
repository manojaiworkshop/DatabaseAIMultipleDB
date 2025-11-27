# PGAIView License Portal - Changelog

## [2.0.1] - 2025-11-02

### ✨ New Features

#### 1. **Simplified License Generation**
- **Removed Admin Key Input Field**: Admin key is now used internally for security
- Users only need to provide:
  - Email Address
  - Deployment ID (can auto-generate)
  - License Type (Trial/Standard/Enterprise)
- Cleaner, more user-friendly interface

#### 2. **Email Notifications** 🎉
- **Automatic Email Delivery**: Generated licenses are automatically sent to the provided email address
- **Beautiful HTML Email Template**: Professional email design with:
  - License details (type, deployment ID, validity period)
  - Formatted license key with copy-friendly format
  - Issue and expiry dates
  - Security reminder
- **Background Processing**: Emails sent asynchronously without blocking license generation
- **Configurable SMTP**: Easy setup via `config.yml` for Gmail, Outlook, SendGrid, etc.

#### 3. **Work in Progress Indicator**
- **Renew License Tab**: Now displays a prominent "Work in Progress" banner
- Form is disabled (grayed out) until feature is fully implemented
- Clear messaging for users about upcoming functionality

### 🎨 UI Improvements

#### Layout Fixes
- **50-50 Split**: Deployment ID input and Generate button now use equal width (50-50 grid layout)
- **Proper Icon Alignment**: All icons and labels are horizontally aligned
- **Consistent Spacing**: Changed from `space-x-2` to `gap-2` throughout for better consistency
- **Button Text Alignment**: Generate button icon and text are properly side-by-side

### 🔧 Technical Changes

#### Backend Updates (`backend/main.py`)
- Removed `admin_key` from `LicenseGenerateRequest` model
- Added `BackgroundTasks` support for async email sending
- Added `send_license_email()` function with:
  - SMTP configuration from `config.yml`
  - HTML and plain text email templates
  - Error handling (doesn't block license generation if email fails)
- Internal admin key validation (transparent to users)

#### Frontend Updates
- **GenerateLicense.jsx**:
  - Removed admin key form field
  - Updated success message to show email notification
  - Grid layout for deployment ID field (50-50 split)
  - Improved icon alignment

- **RenewLicense.jsx**:
  - Added "Work in Progress" banner with yellow gradient design
  - Disabled form with opacity and pointer-events
  - Animated pulse effect on icon

- **Button.jsx**:
  - Fixed children wrapping issue (removed extra `<span>`)
  - Changed to `gap-2` for consistent spacing
  - Conditional loading icon rendering

- **api.js**:
  - Removed `adminKey` parameter from `generateLicense()` call

#### Configuration (`config.yml`)
- Enhanced email configuration section with:
  - Detailed SMTP setup instructions
  - Gmail app password guide
  - Examples for multiple email providers (Gmail, Outlook, SendGrid)
  - Enable/disable toggle

### 📋 Configuration Guide

To enable email notifications, edit `config.yml`:

```yaml
email:
  enabled: true  # Change to true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"  # Use Gmail App Password
```

**For Gmail:**
1. Enable 2-factor authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character app password (not your regular Gmail password)

### 🚀 User Experience Flow

**Before:**
1. Enter email
2. Enter deployment ID (or generate)
3. Select license type
4. **Enter admin key** ← Removed
5. Click Generate
6. Manually copy license key

**After:**
1. Enter email
2. Enter deployment ID (or generate)
3. Select license type
4. Click Generate
5. ✅ License generated **and emailed automatically**
6. View license details on screen

### 🔐 Security Notes
- Admin key is still required but handled internally by the backend
- Default admin key: `pgaiview-admin-2024` (configurable in `config.yml`)
- Email passwords should use app-specific passwords (never regular passwords)
- Consider using environment variables for production: `ADMIN_KEY`, `LICENSE_SECRET_KEY`

### 📝 Notes
- Email feature is **optional** - set `email.enabled: false` to disable
- If email is disabled, licenses are still generated and displayed on screen
- Email sending happens in background - doesn't slow down license generation
- Failed email delivery won't prevent license generation

### 🎯 Next Steps
1. Complete Renew License functionality
2. Add license history/management dashboard
3. Implement license usage analytics
4. Add bulk license generation
5. Export license data to CSV/Excel

---

## How to Update

```bash
cd license-portal

# Pull latest changes
git pull

# Backend - Install email dependencies (already included)
cd backend
pip install -r requirements.txt

# Frontend - No new dependencies needed
cd ../frontend
npm install

# Configure email in config.yml
nano ../config.yml

# Restart the application
cd ..
./start.sh
```

---

**Full Changelog**: https://github.com/manojaiworkshop/DatabaseAI/commits/main
