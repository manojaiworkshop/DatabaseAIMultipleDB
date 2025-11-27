import React, { useState, useEffect } from 'react';
import api from '../services/api';
import Neo4jSettings from './Neo4jSettings';
import OntologySettings from './OntologySettings';
import LicenseSettings from './LicenseSettings';

export default function SettingsDrawer({ open, onClose }) {
  const [activeTab, setActiveTab] = useState('general');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  // General Settings
  const [generalSettings, setGeneralSettings] = useState({
    llm_provider: 'openai',
    schema_name: '',
    max_retry: 3,
    fallback_to_rules: true,
    context_strategy: 'auto',
    max_tokens: 4000,
  });

  // OpenAI Settings
  const [openaiSettings, setOpenaiSettings] = useState({
    api_key: '',
    model: 'gpt-4o-mini-2024-07-18',
    temperature: 1.0,
    max_tokens: 16000,
    top_p: 1.0,
  });

  // vLLM Settings
  const [vllmSettings, setVllmSettings] = useState({
    api_url: 'http://localhost:8000/v1/chat/completions',
    model: '/models',
    max_tokens: 2048,
    temperature: 0.7,
    top_p: 1.0,
  });

  // Ollama Settings
  const [ollamaSettings, setOllamaSettings] = useState({
    api_url: 'http://localhost:11434/api/chat',
    model: 'mistral:latest',
    max_tokens: 2048,
    temperature: 0.7,
    stream: false,
  });

  // License Settings
  const [licenseKey, setLicenseKey] = useState('');
  const [licenseInfo, setLicenseInfo] = useState(null);
  const [licenseLoading, setLicenseLoading] = useState(false);

  // Load settings on mount
  useEffect(() => {
    if (open) {
      loadAllSettings();
      loadLicenseInfo();
    }
  }, [open]);

  const loadAllSettings = async () => {
    setLoading(true);
    try {
      const response = await api.getSettings();
      const settings = response.settings || response;
      
      console.log('Loaded settings:', settings);
      
      // Load general and LLM settings
      if (settings.llm) {
        setGeneralSettings(prev => ({
          ...prev,
          llm_provider: settings.llm.provider || 'openai',
          fallback_to_rules: settings.llm.fallback_to_rules ?? true,
        }));
      }
      
      if (settings.general) {
        setGeneralSettings(prev => ({
          ...prev,
          schema_name: settings.general.schema_name || '',
          max_retry: settings.general.max_retry_attempts || 3,
          context_strategy: settings.general.context_strategy || 'auto',
          max_tokens: settings.general.max_tokens || 4000,
        }));
      }

      // Load OpenAI settings
      if (settings.openai) {
        setOpenaiSettings(settings.openai);
      }

      // Load vLLM settings
      if (settings.vllm) {
        setVllmSettings(settings.vllm);
      }

      // Load Ollama settings
      if (settings.ollama) {
        setOllamaSettings(settings.ollama);
      }

    } catch (error) {
      console.error('Error loading settings:', error);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const loadLicenseInfo = async () => {
    try {
      const info = await api.getLicenseInfo();
      setLicenseInfo(info);
    } catch (error) {
      console.error('Error loading license:', error);
    }
  };

  const handleGeneralSave = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      // Update LLM settings
      await api.updateSettings({
        section: 'llm',
        settings: {
          provider: generalSettings.llm_provider,
          fallback_to_rules: generalSettings.fallback_to_rules,
        }
      });
      
      // Update general settings
      await api.updateSettings({
        section: 'general',
        settings: {
          schema_name: generalSettings.schema_name || null,
          max_retry_attempts: generalSettings.max_retry,
          context_strategy: generalSettings.context_strategy,
          max_tokens: generalSettings.max_tokens,
        }
      });
      
      setMessage({ type: 'success', text: '✓ General settings saved successfully!' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAISave = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      await api.updateOpenAISettings(openaiSettings);
      setMessage({ type: 'success', text: '✓ OpenAI settings saved successfully!' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Error saving OpenAI settings:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save OpenAI settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleVLLMSave = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      await api.updateVLLMSettings(vllmSettings);
      setMessage({ type: 'success', text: '✓ vLLM settings saved successfully!' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Error saving vLLM settings:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save vLLM settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleOllamaSave = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      await api.updateOllamaSettings(ollamaSettings);
      setMessage({ type: 'success', text: '✓ Ollama settings saved successfully!' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Error saving Ollama settings:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save Ollama settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleLicenseActivate = async () => {
    if (!licenseKey.trim()) {
      setMessage({ type: 'error', text: 'Please enter a license key' });
      return;
    }

    setLicenseLoading(true);
    setMessage({ type: '', text: '' });
    try {
      await api.activateLicense(licenseKey);
      setMessage({ type: 'success', text: '✓ License activated successfully!' });
      setLicenseKey('');
      await loadLicenseInfo();
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Error activating license:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to activate license' });
    } finally {
      setLicenseLoading(false);
    }
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-30 backdrop-blur-sm z-40 transition-opacity duration-300"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-1/2 min-w-[600px] max-w-[800px] bg-white shadow-2xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <h2 className="text-2xl font-bold text-gray-800">Settings</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-full transition-colors"
          >
            <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
                {/* Tabs */}
        <div className="flex border-b border-gray-200 bg-gray-50 px-6">
          {['general', 'openai', 'vllm', 'ollama', 'neo4j', 'ontology', 'license'].map((tab) => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                setMessage({ type: '', text: '' });
              }}
              className={`px-6 py-3 text-sm font-medium transition-all duration-200 border-b-2 ${
                activeTab === tab
                  ? 'text-blue-600 border-blue-600 bg-white'
                  : 'text-gray-600 border-transparent hover:text-gray-800 hover:border-gray-300'
              }`}
            >
              {tab === 'neo4j' ? 'Neo4j' : tab === 'ontology' ? 'Ontology' : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Message */}
        {message.text && (
          <div className={`mx-6 mt-4 p-3 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 
            'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {loading && activeTab !== 'license' && (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          )}

          {/* General Tab */}
          {activeTab === 'general' && !loading && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">LLM Provider</h3>
                <p className="text-sm text-gray-600 mb-3">Choose the language model provider for SQL generation</p>
                <div className="space-y-3">
                  {[
                    { value: 'openai', label: 'OpenAI', desc: 'GPT-4 and GPT-3.5 models' },
                    { value: 'vllm', label: 'vLLM', desc: 'Self-hosted inference server' },
                    { value: 'ollama', label: 'Ollama', desc: 'Local LLM runtime' }
                  ].map((provider) => (
                    <label
                      key={provider.value}
                      className={`block p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        generalSettings.llm_provider === provider.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 bg-white'
                      }`}
                    >
                      <input
                        type="radio"
                        name="llm_provider"
                        value={provider.value}
                        checked={generalSettings.llm_provider === provider.value}
                        onChange={(e) => setGeneralSettings({ ...generalSettings, llm_provider: e.target.value })}
                        className="mr-3"
                      />
                      <span className="font-medium text-gray-800">{provider.label}</span>
                      <p className="text-sm text-gray-600 ml-6">{provider.desc}</p>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Database Schema</h3>
                <p className="text-sm text-gray-600 mb-3">Specify the schema name if your tables are in a specific schema (e.g., "public", "nmsclient")</p>
                <input
                  type="text"
                  placeholder="Schema name (optional)"
                  value={generalSettings.schema_name}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, schema_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-2">Leave empty to search all schemas</p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Context Strategy</h3>
                <p className="text-sm text-gray-600 mb-3">How context is built for SQL generation</p>
                <select
                  value={generalSettings.context_strategy}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, context_strategy: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="auto">Auto (Recommended) - Based on max tokens</option>
                  <option value="concise">Concise - Minimal schema, compact errors</option>
                  <option value="semi">Semi - Key tables with samples</option>
                  <option value="expanded">Expanded - Full schema with relationships</option>
                  <option value="large">Large - Comprehensive with examples</option>
                </select>
                <p className="text-xs text-gray-500 mt-2">
                  Auto adjusts based on max tokens: &lt;3K=concise, 3-6K=semi, 6-10K=expanded, &gt;10K=large
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Max Tokens</h3>
                <p className="text-sm text-gray-600 mb-3">Maximum tokens for context and generation (affects context verbosity)</p>
                <div className="flex items-center space-x-4">
                  <input
                    type="range"
                    min="1000"
                    max="16000"
                    step="1000"
                    value={generalSettings.max_tokens}
                    onChange={(e) => setGeneralSettings({ ...generalSettings, max_tokens: parseInt(e.target.value) })}
                    className="flex-1 h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                  <span className="text-2xl font-bold text-blue-600 min-w-[5rem] text-center">
                    {generalSettings.max_tokens}
                  </span>
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>1K (Fast)</span>
                  <span>16K (Comprehensive)</span>
                </div>
                <p className="text-xs text-blue-600 mt-2">💡 Recommended: 4000 for balanced performance</p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Max Retry Attempts</h3>
                <p className="text-sm text-gray-600 mb-3">Number of retry attempts if the generated SQL query fails</p>
                <div className="flex items-center space-x-4">
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={generalSettings.max_retry}
                    onChange={(e) => setGeneralSettings({ ...generalSettings, max_retry: parseInt(e.target.value) })}
                    className="flex-1 h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                  <span className="text-2xl font-bold text-blue-600 min-w-[3rem] text-center">
                    {generalSettings.max_retry}
                  </span>
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>1 (Fast)</span>
                  <span>10 (Thorough)</span>
                </div>
                <p className="text-xs text-blue-600 mt-2">💡 Tip: Higher values increase accuracy but take more time. Recommended: 3-5 for most queries.</p>
              </div>

              <button
                onClick={handleGeneralSave}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Save General Settings
                  </>
                )}
              </button>
            </div>
          )}

          {/* OpenAI Tab */}
          {activeTab === 'openai' && !loading && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
                <input
                  type="password"
                  placeholder="sk-..."
                  value={openaiSettings.api_key}
                  onChange={(e) => setOpenaiSettings({ ...openaiSettings, api_key: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoComplete="off"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
                <select
                  value={openaiSettings.model}
                  onChange={(e) => setOpenaiSettings({ ...openaiSettings, model: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="gpt-4o-mini-2024-07-18">GPT-4o Mini (Recommended)</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Temperature: {openaiSettings.temperature.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={openaiSettings.temperature}
                  onChange={(e) => setOpenaiSettings({ ...openaiSettings, temperature: parseFloat(e.target.value) })}
                  className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Max Tokens</label>
                <input
                  type="number"
                  value={openaiSettings.max_tokens}
                  onChange={(e) => setOpenaiSettings({ ...openaiSettings, max_tokens: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <button
                onClick={handleOpenAISave}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 transition-colors flex items-center justify-center"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Save OpenAI Settings
                  </>
                )}
              </button>
            </div>
          )}

          {/* vLLM Tab */}
          {activeTab === 'vllm' && !loading && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Server URL</label>
                <input
                  type="text"
                  placeholder="http://localhost:8000/v1/chat/completions"
                  value={vllmSettings.api_url}
                  onChange={(e) => setVllmSettings({ ...vllmSettings, api_url: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Model Path</label>
                <input
                  type="text"
                  placeholder="/models"
                  value={vllmSettings.model}
                  onChange={(e) => setVllmSettings({ ...vllmSettings, model: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Temperature: {vllmSettings.temperature.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={vllmSettings.temperature}
                  onChange={(e) => setVllmSettings({ ...vllmSettings, temperature: parseFloat(e.target.value) })}
                  className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Max Tokens</label>
                <input
                  type="number"
                  value={vllmSettings.max_tokens}
                  onChange={(e) => setVllmSettings({ ...vllmSettings, max_tokens: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <button
                onClick={handleVLLMSave}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 transition-colors flex items-center justify-center"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Save vLLM Settings
                  </>
                )}
              </button>
            </div>
          )}

          {/* Ollama Tab */}
          {activeTab === 'ollama' && !loading && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Server URL</label>
                <input
                  type="text"
                  placeholder="http://localhost:11434/api/chat"
                  value={ollamaSettings.api_url}
                  onChange={(e) => setOllamaSettings({ ...ollamaSettings, api_url: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
                <input
                  type="text"
                  placeholder="mistral:latest"
                  value={ollamaSettings.model}
                  onChange={(e) => setOllamaSettings({ ...ollamaSettings, model: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Temperature: {ollamaSettings.temperature.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={ollamaSettings.temperature}
                  onChange={(e) => setOllamaSettings({ ...ollamaSettings, temperature: parseFloat(e.target.value) })}
                  className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Max Tokens</label>
                <input
                  type="number"
                  value={ollamaSettings.max_tokens}
                  onChange={(e) => setOllamaSettings({ ...ollamaSettings, max_tokens: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <button
                onClick={handleOllamaSave}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 transition-colors flex items-center justify-center"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Save Ollama Settings
                  </>
                )}
              </button>
            </div>
          )}

          {/* Neo4j Tab */}
          {activeTab === 'neo4j' && (
            <Neo4jSettings />
          )}

          {/* Ontology Tab */}
          {activeTab === 'ontology' && (
            <OntologySettings />
          )}

          {/* License Tab */}
          {activeTab === 'license' && (
            <LicenseSettings />
          )}
        </div>
      </div>
    </>
  );
}
