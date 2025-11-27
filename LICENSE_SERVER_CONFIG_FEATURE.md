# License Server Configuration Feature

## Overview
Added the ability to configure and persist the license server URL from the UI. Users can now edit the license server URL from both the Settings drawer and License modal, and the configuration is saved to `app_config.yml`.

## Changes Made

### Backend Changes

#### 1. `app_config.yml`
- Added `server_url` field under `license` section
- Default value: `http://localhost:5000`

```yaml
license:
  server_url: http://localhost:5000
  # ... other license fields
```

#### 2. `backend/app/routes/license.py`
- Modified to use dynamic license server URL from config
- Added `get_license_server_url()` function to read URL from config/environment
- Updated `validate_license_with_server()` to use dynamic URL
- Added new endpoints:
  - `GET /api/v1/license/server-config` - Get current license server URL
  - `PUT /api/v1/license/server-config` - Update license server URL
- Added `LicenseServerConfigRequest` model for URL updates
- URL validation: Ensures URL starts with http:// or https://

### Frontend Changes

#### 1. `frontend/src/services/api.js`
- Added `getLicenseServerConfig()` - Fetch current license server URL
- Added `updateLicenseServerConfig(serverUrl)` - Update license server URL
- Exported new functions for component use

#### 2. New Component: `frontend/src/components/LicenseSettings.js`
- Comprehensive license settings component
- Features:
  - Display current license status (active/inactive)
  - Show license details (type, expiration, days remaining)
  - Edit license server URL
  - Save settings with validation
  - Open license server in new tab
  - Real-time status indicators
  - Error and success messages

#### 3. `frontend/src/components/SettingsDrawer.js`
- Added import for `LicenseSettings` component
- Replaced inline license tab content with `<LicenseSettings />` component
- Simplified tab structure

#### 4. `frontend/src/components/LicenseModal.js`
- Made license server URL dynamic
- Added `useEffect` to load license server URL on modal open
- Updated "Get License" button to use configured URL
- Updated help text to display configured server URL

#### 5. `Dockerfile.combined`
- Fixed backend executable path issue
- Changed from `/app/backend` (directory) to `/app/backend/pgaiview-backend` (executable)
- Updated supervisord configuration to use correct executable path

## Features

### 1. License Server URL Configuration
- **Editable in UI**: Users can change the license server URL without editing config files
- **Persistent**: Changes are saved to `app_config.yml` and persist across restarts
- **Validated**: URL format is validated (must start with http:// or https://)
- **Dynamic**: All license operations (activation, validation) use the configured URL

### 2. License Status Dashboard
- Real-time license information display
- Shows: Type, Status, Activation date, Expiration date, Days remaining
- Color-coded status indicators:
  - Green: Active and valid license
  - Yellow: No license or inactive
  - Red: Expired license or < 7 days remaining

### 3. Quick Actions
- **Save Settings**: Persist license server URL changes
- **Open Server**: Quick link to open license server in new tab
- Visual feedback for all actions (loading, success, error states)

## Usage

### For End Users

#### Via Settings Drawer:
1. Click Settings icon in chat page
2. Navigate to "License" tab
3. View current license status
4. Edit "Server URL" field
5. Click "Save Settings"
6. Use "Open Server" to visit license server

#### Via License Modal (when required):
1. Modal appears when license is required
2. Click "Get License" button to open configured license server
3. Server URL is automatically loaded from config

### For Administrators

#### Set Default License Server:
Edit `app_config.yml`:
```yaml
license:
  server_url: https://your-license-server.com
```

#### Environment Variable Override:
```bash
export LICENSE_SERVER_URL=https://your-license-server.com
```

Priority: Config file > Environment variable > Default (localhost:5000)

## API Endpoints

### Get License Server Config
```
GET /api/v1/license/server-config
```
Response:
```json
{
  "success": true,
  "server_url": "http://localhost:5000"
}
```

### Update License Server Config
```
PUT /api/v1/license/server-config
```
Request:
```json
{
  "server_url": "https://new-server.com"
}
```
Response:
```json
{
  "success": true,
  "message": "License server URL updated successfully",
  "server_url": "https://new-server.com"
}
```

## Configuration Priority

1. **Config File** (`app_config.yml`): Primary source
2. **Environment Variable** (`LICENSE_SERVER_URL`): Fallback
3. **Default**: `http://localhost:5000`

## Benefits

✅ **No Code Changes**: Users can change license server without modifying code
✅ **Multi-Environment Support**: Easy configuration for dev, staging, production
✅ **User-Friendly**: Intuitive UI for configuration
✅ **Persistent**: Settings survive container restarts
✅ **Validated**: Prevents invalid URL formats
✅ **Real-Time Updates**: Changes take effect immediately
✅ **Centralized Management**: Single source of truth in config file

## Testing

1. **Test URL Update**:
   - Open Settings → License tab
   - Change URL to `http://test-server:5000`
   - Click Save
   - Verify success message
   - Restart backend
   - Verify URL persists

2. **Test License Activation**:
   - Configure license server URL
   - Click "Get License" in modal
   - Verify correct server opens
   - Activate license
   - Verify activation uses correct server

3. **Test Validation**:
   - Try invalid URL (no protocol): Should show error
   - Try empty URL: Should show error
   - Try valid URL: Should succeed

## Docker Build Fix

The Dockerfile issue has been resolved:
- **Problem**: PyInstaller COLLECT creates a directory, not a single executable
- **Solution**: Updated path from `/app/backend` to `/app/backend/pgaiview-backend`
- **Status**: ✅ Fixed and tested

## Deployment

To deploy with the fix:
```bash
# Rebuild image
docker build -f Dockerfile.combined -t opendockerai/pgaiview:latest .

# Run container
docker run -d --name pgaiview -p 80:80 opendockerai/pgaiview:latest
```

The application is now fully functional with configurable license server support!
