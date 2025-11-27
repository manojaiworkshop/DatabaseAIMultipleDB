import React, { useState } from 'react';
import { Shield, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';
import Card from './Card';
import Input from './Input';
import Button from './Button';
import { licenseAPI } from '../services/api';

const ValidateLicense = () => {
  const [licenseKey, setLicenseKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      // Trim whitespace and newlines from license key
      const cleanKey = licenseKey.trim().replace(/\s+/g, '');
      const data = await licenseAPI.validateLicense(cleanKey);
      setResult(data);
      if (data.valid) {
        toast.success('License is valid!');
      } else {
        toast.error('License is invalid or expired');
      }
    } catch (error) {
      toast.error('Validation failed');
    } finally {
      setLoading(false);
    }
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
          <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
            <Shield className="w-6 h-6 text-primary-600" />
            <span>Validate License</span>
          </h2>
          <p className="text-gray-600 mt-1">Check the validity and details of a license key</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="label">License Key</label>
            <textarea
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value)}
              placeholder="Paste your license key here..."
              className="input font-mono text-sm resize-none"
              rows="4"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Enter the complete license key to validate</p>
          </div>

          <Button type="submit" loading={loading} className="w-full">
            <Shield className="w-4 h-4" />
            <span>Validate License</span>
          </Button>
        </form>
      </Card>

      {result && (
        <Card
          className={`${
            result.valid
              ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200'
              : 'bg-gradient-to-br from-red-50 to-rose-50 border-red-200'
          }`}
        >
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              {result.valid ? (
                <>
                  <CheckCircle className="w-8 h-8 text-green-600" />
                  <div>
                    <h3 className="text-lg font-bold text-green-900">License is Valid</h3>
                    <p className="text-sm text-green-700">This license is active and verified</p>
                  </div>
                </>
              ) : (
                <>
                  <XCircle className="w-8 h-8 text-red-600" />
                  <div>
                    <h3 className="text-lg font-bold text-red-900">License is Invalid</h3>
                    <p className="text-sm text-red-700">
                      {result.error || 'This license has expired or is invalid'}
                    </p>
                  </div>
                </>
              )}
            </div>

            {result.deployment_id && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <p className="text-xs text-gray-600">Status</p>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      result.valid
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {result.valid ? 'Active' : 'Expired'}
                  </span>
                </div>
                
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <p className="text-xs text-gray-600">License Type</p>
                  <p className="font-semibold text-gray-900 capitalize">{result.license_type}</p>
                </div>

                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <p className="text-xs text-gray-600">Deployment ID</p>
                  <p className="font-semibold text-gray-900 text-xs break-all">{result.deployment_id}</p>
                </div>

                {result.valid && (
                  <div className="bg-white rounded-lg p-3 border border-gray-200">
                    <p className="text-xs text-gray-600">Days Remaining</p>
                    <p className="font-semibold text-green-600 text-lg">{result.days_remaining} days</p>
                  </div>
                )}

                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <p className="text-xs text-gray-600">Issue Date</p>
                  <p className="font-semibold text-gray-900 text-sm">
                    {formatDate(result.issue_date)}
                  </p>
                </div>

                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <p className="text-xs text-gray-600">Expiry Date</p>
                  <p className="font-semibold text-gray-900 text-sm">
                    {formatDate(result.expiry_date)}
                  </p>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default ValidateLicense;
