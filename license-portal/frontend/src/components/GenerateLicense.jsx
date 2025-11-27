import React, { useState } from 'react';
import { Copy, Sparkles, RefreshCw } from 'lucide-react';
import { toast } from 'react-hot-toast';
import Card from './Card';
import Input from './Input';
import Button from './Button';
import { licenseAPI } from '../services/api';

const GenerateLicense = () => {
  const [formData, setFormData] = useState({
    email: '',
    deploymentId: '',
    licenseType: 'trial',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const generateDeploymentId = () => {
    const date = new Date().toISOString().split('T')[0].replace(/-/g, '');
    const random = Math.random().toString(36).substring(2, 10).toUpperCase();
    setFormData({ ...formData, deploymentId: `deploy-${date}-${random}` });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const data = await licenseAPI.generateLicense(
        formData.email,
        formData.deploymentId,
        formData.licenseType
      );
      setResult(data);
      toast.success(`License generated and sent to ${formData.email}!`);
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to generate license';
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
            <Sparkles className="w-6 h-6 text-primary-600" />
            <span>Generate New License</span>
          </h2>
          <p className="text-gray-600 mt-1">Create a new license for your PGAIView deployment</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            type="email"
            label="Email Address"
            placeholder="user@example.com"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
            helperText="Enter the user's email address"
          />

          <div>
            <label className="label">Deployment ID</label>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text"
                value={formData.deploymentId}
                onChange={(e) => setFormData({ ...formData, deploymentId: e.target.value })}
                placeholder="deploy-20251102-ABC12345"
                required
                className="input w-full"
              />
              <Button
                type="button"
                variant="secondary"
                onClick={generateDeploymentId}
                className="flex items-center justify-center gap-2 w-full"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Generate</span>
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-1">Unique identifier for this deployment</p>
          </div>

          <div>
            <label className="label">License Type</label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {[
                { value: 'trial', label: 'Trial', days: '10 days', desc: 'For testing' },
                { value: 'standard', label: 'Standard', days: '60 days', desc: '2 months' },
                { value: 'enterprise', label: 'Enterprise', days: '365 days', desc: 'Full year' },
              ].map((type) => (
                <label
                  key={type.value}
                  className={`relative flex cursor-pointer rounded-lg border-2 p-4 transition-all ${
                    formData.licenseType === type.value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="licenseType"
                    value={type.value}
                    checked={formData.licenseType === type.value}
                    onChange={(e) => setFormData({ ...formData, licenseType: e.target.value })}
                    className="sr-only"
                  />
                  <div className="flex flex-col w-full">
                    <span className="font-semibold text-gray-900">{type.label}</span>
                    <span className="text-sm text-primary-600 font-medium">{type.days}</span>
                    <span className="text-xs text-gray-500 mt-1">{type.desc}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <Button type="submit" loading={loading} className="w-full flex items-center justify-center gap-2">
            <Sparkles className="w-4 h-4" />
            <span>Generate License</span>
          </Button>
        </form>
      </Card>

      {result && (
        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-green-900 flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span>License Generated Successfully!</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-white rounded-lg p-3 border border-green-200">
                <p className="text-xs text-gray-600">License Type</p>
                <p className="font-semibold text-gray-900 capitalize">{result.license_type}</p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-green-200">
                <p className="text-xs text-gray-600">Valid For</p>
                <p className="font-semibold text-gray-900">{result.days_valid} days</p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-green-200">
                <p className="text-xs text-gray-600">Issue Date</p>
                <p className="font-semibold text-gray-900">{formatDate(result.issue_date)}</p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-green-200">
                <p className="text-xs text-gray-600">Expiry Date</p>
                <p className="font-semibold text-gray-900">{formatDate(result.expiry_date)}</p>
              </div>
            </div>

            <div>
              <label className="label">License Key</label>
              <div className="relative">
                <textarea
                  readOnly
                  value={result.license_key}
                  className="w-full p-3 pr-12 border border-green-300 rounded-lg bg-white font-mono text-sm resize-none"
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

export default GenerateLicense;
