import React, { useState, useEffect } from 'react';
import { Key, Server, Save, Loader2, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react';
import { api } from '../services/api';

const LicenseSettings = () => {
  const [serverUrl, setServerUrl] = useState('http://localhost:8000');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [licenseInfo, setLicenseInfo] = useState(null);
  const [loadingLicense, setLoadingLicense] = useState(false);
  const [licenseKey, setLicenseKey] = useState('');
  const [editingKey, setEditingKey] = useState(false);
  const [validatingKey, setValidatingKey] = useState(false);

  useEffect(() => {
    loadLicenseConfig();
    loadLicenseInfo();
  }, []);

  const loadLicenseConfig = async () => {
    try {
      setLoading(true);
      const response = await api.getLicenseServerConfig();
      if (response.success) {
        setServerUrl(response.server_url);
      }
    } catch (err) {
      console.error('Failed to load license config:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadLicenseInfo = async () => {
    try {
      setLoadingLicense(true);
      const response = await api.getLicenseInfo();
      setLicenseInfo(response);
      setLicenseKey(response.license_key || '');
    } catch (err) {
      console.error('Failed to load license info:', err);
    } finally {
      setLoadingLicense(false);
    }
  };

  const handleUpdateLicenseKey = async () => {
    setError('');
    setSuccess('');
    
    if (!licenseKey.trim()) {
      setError('License key cannot be empty');
      return;
    }

    try {
      setValidatingKey(true);
      const response = await api.updateLicenseKey(licenseKey.trim());
      
      if (response.success) {
        setSuccess('License key updated and validated successfully!');
        setEditingKey(false);
        await loadLicenseInfo();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(response.message || 'Failed to update license key');
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to update license key';
      setError(errorMsg);
    } finally {
      setValidatingKey(false);
    }
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');
    
    if (!serverUrl.trim()) {
      setError('Server URL is required');
      return;
    }

    if (!serverUrl.startsWith('http://') && !serverUrl.startsWith('https://')) {
      setError('Invalid URL format. Must start with http:// or https://');
      return;
    }

    try {
      setSaving(true);
      const response = await api.updateLicenseServerConfig(serverUrl);
      
      if (response.success) {
        setSuccess('License server URL updated successfully!');
        setTimeout(() => setSuccess(''), 3000);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to update server URL';
      setError(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleOpenServer = () => {
    window.open(serverUrl, '_blank');
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b border-gray-200">
        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
          <Key className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">License Settings</h3>
          <p className="text-sm text-gray-600">Configure license server and view activation status</p>
        </div>
      </div>

      {/* Current License Status */}
      {loadingLicense ? (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
            <span className="text-sm text-gray-600">Loading license information...</span>
          </div>
        </div>
      ) : licenseInfo && licenseInfo.activated ? (
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-medium text-green-900 mb-2">License Active</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-green-700 font-medium">Type</p>
                  <p className="text-green-900 capitalize">{licenseInfo.license_type || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-green-700 font-medium">Status</p>
                  <p className="text-green-900">
                    {licenseInfo.expired ? (
                      <span className="text-red-600 font-semibold">Expired</span>
                    ) : (
                      <span className="text-green-600 font-semibold">Valid</span>
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-green-700 font-medium">Activated At</p>
                  <p className="text-green-900">{formatDate(licenseInfo.activated_at)}</p>
                </div>
                <div>
                  <p className="text-green-700 font-medium">Expires</p>
                  <p className="text-green-900">{formatDate(licenseInfo.expiry_date)}</p>
                </div>
                {licenseInfo.days_remaining !== undefined && (
                  <div className="col-span-2">
                    <p className="text-green-700 font-medium">Days Remaining</p>
                    <p className={`font-bold ${licenseInfo.days_remaining < 7 ? 'text-red-600' : 'text-green-900'}`}>
                      {licenseInfo.days_remaining} days
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-yellow-900 mb-1">No Active License</h4>
              <p className="text-sm text-yellow-700">
                Please activate a license to use the full features of the application.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* License Key Management */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-gray-700" />
            <h4 className="font-medium text-gray-900">License Key</h4>
          </div>
          {!editingKey && licenseKey && (
            <button
              onClick={() => setEditingKey(true)}
              className="text-sm text-purple-600 hover:text-purple-700 font-medium"
            >
              Edit
            </button>
          )}
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Current License Key
            </label>
            <textarea
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value)}
              placeholder="Paste your license key here..."
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-xs resize-none"
              rows="4"
              disabled={!editingKey || validatingKey}
            />
            <p className="mt-1 text-xs text-gray-500">
              {editingKey 
                ? 'Enter your license key and click Update to validate and save' 
                : 'Your currently activated license key'}
            </p>
          </div>

          {editingKey && (
            <div className="flex gap-3">
              <button
                onClick={handleUpdateLicenseKey}
                disabled={validatingKey}
                className="flex-1 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {validatingKey ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Validating...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    <span>Update & Validate</span>
                  </>
                )}
              </button>
              <button
                onClick={() => {
                  setEditingKey(false);
                  loadLicenseInfo();
                }}
                disabled={validatingKey}
                className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* License Server Configuration */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-gray-700" />
          <h4 className="font-medium text-gray-900">License Server URL</h4>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Server URL
            </label>
            <input
              type="url"
              value={serverUrl}
              onChange={(e) => setServerUrl(e.target.value)}
              placeholder="http://localhost:8000"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={loading || saving}
            />
            <p className="mt-1 text-xs text-gray-500">
              URL of the license server. Must start with http:// or https://
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex gap-2">
                <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-green-800">{success}</p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={saving || loading}
              className="flex-1 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save Settings</span>
                </>
              )}
            </button>
            <button
              onClick={handleOpenServer}
              disabled={!serverUrl || loading || saving}
              className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              <span>Open Server</span>
            </button>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <Key className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <h4 className="text-sm font-medium text-blue-900 mb-1">License Server</h4>
            <p className="text-xs text-blue-700 leading-relaxed">
              The license server validates and manages license keys. Configure the server URL here to connect
              to your organization's license server or use the default local server for testing.
              Changes take effect immediately and will be used for all license operations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LicenseSettings;
