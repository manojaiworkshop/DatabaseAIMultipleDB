import React, { useState } from 'react';
import { RefreshCcw, Copy } from 'lucide-react';
import { toast } from 'react-hot-toast';
import Card from './Card';
import Input from './Input';
import Button from './Button';
import { licenseAPI } from '../services/api';

const RenewLicense = () => {
  const [formData, setFormData] = useState({
    currentLicenseKey: '',
    adminKey: '',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const data = await licenseAPI.renewLicense(
        formData.currentLicenseKey,
        formData.adminKey
      );
      setResult(data);
      toast.success('License renewed successfully!');
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to renew license';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      <Card>
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <RefreshCcw className="w-6 h-6 text-primary-600" />
            <span>Renew License</span>
          </h2>
          <p className="text-gray-600 mt-1">Extend your existing license with a new key</p>
        </div>

        {/* Work in Progress Banner */}
        <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border-2 border-yellow-300 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-center gap-3">
            <div className="w-12 h-12 bg-yellow-400 rounded-full flex items-center justify-center animate-pulse">
              <RefreshCcw className="w-6 h-6 text-yellow-900" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-yellow-900">Work in Progress</h3>
              <p className="text-yellow-700 text-sm mt-1">
                License renewal feature is currently under development. Please check back soon!
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 opacity-50 pointer-events-none">
          <div>
            <label className="label">Current License Key</label>
            <textarea
              value={formData.currentLicenseKey}
              onChange={(e) =>
                setFormData({ ...formData, currentLicenseKey: e.target.value })
              }
              placeholder="Paste your current license key..."
              className="input font-mono text-sm resize-none"
              rows="4"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Your existing license key that needs renewal
            </p>
          </div>

          <Input
            type="password"
            label="Admin Key"
            placeholder="Enter admin key"
            value={formData.adminKey}
            onChange={(e) => setFormData({ ...formData, adminKey: e.target.value })}
            required
            helperText="Admin authentication key for renewal"
          />

          <Button type="submit" loading={loading} className="w-full">
            <RefreshCcw className="w-4 h-4" />
            <span>Renew License</span>
          </Button>
        </form>
      </Card>

      {result && (
        <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-blue-900 flex items-center space-x-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
              <span>License Renewed Successfully!</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-white rounded-lg p-3 border border-blue-200">
                <p className="text-xs text-gray-600">License Type</p>
                <p className="font-semibold text-gray-900 capitalize">{result.license_type}</p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-blue-200">
                <p className="text-xs text-gray-600">Valid For</p>
                <p className="font-semibold text-gray-900">{result.days_valid} days</p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-blue-200">
                <p className="text-xs text-gray-600">New Issue Date</p>
                <p className="font-semibold text-gray-900">{formatDate(result.issue_date)}</p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-blue-200">
                <p className="text-xs text-gray-600">New Expiry Date</p>
                <p className="font-semibold text-gray-900">{formatDate(result.expiry_date)}</p>
              </div>
            </div>

            <div>
              <label className="label">New License Key</label>
              <div className="relative">
                <textarea
                  readOnly
                  value={result.license_key}
                  className="w-full p-3 pr-12 border border-blue-300 rounded-lg bg-white font-mono text-sm resize-none"
                  rows="4"
                />
                <button
                  onClick={() => copyToClipboard(result.license_key)}
                  className="absolute top-3 right-3 p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default RenewLicense;
