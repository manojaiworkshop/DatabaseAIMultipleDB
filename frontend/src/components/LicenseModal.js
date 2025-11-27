import React, { useState, useEffect } from 'react';
import { X, Key, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';

const LicenseModal = ({ isOpen, onClose, onLicenseActivated }) => {
  const [licenseKey, setLicenseKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [licenseServerUrl, setLicenseServerUrl] = useState('http://localhost:3000');

  useEffect(() => {
    if (isOpen) {
      loadLicenseServerUrl();
    }
  }, [isOpen]);

  const loadLicenseServerUrl = async () => {
    try {
      const response = await api.getLicenseServerConfig();
      if (response.success && response.server_url) {
        setLicenseServerUrl(response.server_url);
      }
    } catch (err) {
      console.error('Failed to load license server URL:', err);
    }
  };

  if (!isOpen) return null;

  const handleActivate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await api.activateLicense(licenseKey);
      
      if (response.success) {
        setSuccess('License activated successfully!');
        setTimeout(() => {
          onLicenseActivated(response.license_info);
          onClose();
        }, 1500);
      } else {
        setError(response.message || 'Failed to activate license');
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to activate license';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleGetLicense = () => {
    // Open license server in new tab using the configured URL
    window.open(licenseServerUrl, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Key className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">License Required</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Message */}
        <div className="mb-6">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <div className="flex gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-yellow-800 font-medium mb-1">
                  Valid license required to use chat functionality
                </p>
                <p className="text-xs text-yellow-700">
                  Please enter your license key or get one from the license server.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* License Key Form */}
        <form onSubmit={handleActivate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              License Key
            </label>
            <input
              type="text"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value)}
              placeholder="Enter your license key"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              required
              disabled={loading}
            />
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

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleGetLicense}
              className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              disabled={loading}
            >
              Get License
            </button>
            <button
              type="submit"
              disabled={loading || !licenseKey.trim()}
              className="flex-1 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Activating...</span>
                </>
              ) : (
                <>
                  <Key className="w-4 h-4" />
                  <span>Activate</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Help Text */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            Need help? Visit the license server at{' '}
            <button
              onClick={handleGetLicense}
              className="text-blue-600 hover:text-blue-700 underline"
            >
              {licenseServerUrl.replace(/^https?:\/\//, '')}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LicenseModal;
