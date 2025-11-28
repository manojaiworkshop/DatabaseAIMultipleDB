import React, { useState, useEffect } from 'react';
import { Upload, Database, Trash2, CheckCircle, XCircle, AlertCircle, Info } from 'lucide-react';
import { api } from '../services/api';

const RAGSettings = ({ onClose }) => {
  const [ragConfig, setRagConfig] = useState({
    enabled: false,
    qdrant_url: 'http://localhost:6333',
    collection_name: 'query_history',
    embedding_model: 'all-MiniLM-L6-v2',
    top_k: 3,
    similarity_threshold: 0.7,
    include_in_context: true
  });
  
  const [ragStatus, setRagStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [statistics, setStatistics] = useState(null);

  useEffect(() => {
    loadRAGSettings();
    loadRAGStatus();
    loadStatistics();
  }, []);

  const loadRAGSettings = async () => {
    try {
      // Use getSettings() to get ALL settings, same as Neo4j
      const response = await api.getSettings();
      if (response.success && response.settings && response.settings.rag) {
        // Replace entire config with loaded settings from config file
        setRagConfig({ ...ragConfig, ...response.settings.rag });
      }
    } catch (error) {
      console.error('Failed to load RAG settings:', error);
    }
  };

  const loadRAGStatus = async () => {
    try {
      const response = await api.getRagStatus();
      setRagStatus(response.data);
    } catch (error) {
      console.error('Failed to load RAG status:', error);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await api.getRagStatistics();
      if (response.data.success) {
        setStatistics(response.data);
      }
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setMessage(null);

    try {
      await api.updateSettings('rag', ragConfig);
      setMessage({ type: 'success', text: 'RAG settings saved successfully!' });
      loadRAGStatus();
      loadStatistics();
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: `Failed to save settings: ${error.response?.data?.detail || error.message}` 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.name.endsWith('.csv')) {
      setUploadFile(file);
    } else {
      setMessage({ type: 'error', text: 'Please select a CSV file' });
    }
  };

  const handleUploadCSV = async () => {
    if (!uploadFile) {
      setMessage({ type: 'error', text: 'Please select a file' });
      return;
    }

    setLoading(true);
    setUploadProgress('Uploading...');
    setMessage(null);

    try {
      const response = await api.uploadRagCsv(uploadFile);
      setUploadProgress(null);
      setUploadFile(null);
      setShowUploadModal(false);
      
      setMessage({ 
        type: 'success', 
        text: `Upload complete! ${response.data.success_count} queries added successfully.` +
              (response.data.error_count > 0 ? ` ${response.data.error_count} errors.` : '')
      });
      
      loadStatistics();
    } catch (error) {
      setUploadProgress(null);
      setMessage({ 
        type: 'error', 
        text: `Upload failed: ${error.response?.data?.detail || error.message}` 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to clear all queries from the RAG database? This action cannot be undone.')) {
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      await api.clearRagDatabase();
      setMessage({ type: 'success', text: 'All queries cleared successfully!' });
      loadStatistics();
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: `Failed to clear database: ${error.response?.data?.detail || error.message}` 
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = () => {
    if (!ragStatus) return <AlertCircle className="text-gray-400" size={16} />;
    
    if (ragStatus.status === 'connected') {
      return <CheckCircle className="text-green-500" size={16} />;
    } else if (ragStatus.status === 'disabled') {
      return <AlertCircle className="text-yellow-500" size={16} />;
    } else {
      return <XCircle className="text-red-500" size={16} />;
    }
  };

  const getStatusText = () => {
    if (!ragStatus) return 'Loading...';
    
    if (ragStatus.status === 'connected') {
      return `Connected (${ragStatus.vector_count || 0} queries stored)`;
    } else if (ragStatus.status === 'disabled') {
      return 'Disabled';
    } else {
      return `Error: ${ragStatus.message}`;
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800">RAG Settings</h2>
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className="text-sm text-gray-600">{getStatusText()}</span>
        </div>
      </div>

      {message && (
        <div className={`mb-4 p-3 rounded-lg ${
          message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        }`}>
          <div className="flex items-center">
            {message.type === 'success' ? 
              <CheckCircle size={18} className="mr-2" /> : 
              <XCircle size={18} className="mr-2" />
            }
            <span>{message.text}</span>
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start">
          <Info className="text-blue-500 mr-3 mt-1 flex-shrink-0" size={20} />
          <div className="text-sm text-blue-800">
            <p className="font-semibold mb-1">What is RAG?</p>
            <p>
              RAG (Retrieval-Augmented Generation) uses past successful queries to help generate better SQL. 
              When you ask a question, it finds similar questions you've asked before and uses them as examples for the AI.
            </p>
          </div>
        </div>
      </div>

      {/* Statistics */}
      {statistics && statistics.enabled && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold text-gray-700 mb-3">Statistics</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Total Queries</p>
              <p className="text-2xl font-bold text-gray-800">{statistics.total_queries || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Top K Results</p>
              <p className="text-2xl font-bold text-gray-800">{statistics.top_k}</p>
            </div>
          </div>
        </div>
      )}

      {/* RAG Configuration */}
      <div className="space-y-4 mb-6">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="ragEnabled"
            checked={ragConfig.enabled}
            onChange={(e) => setRagConfig({ ...ragConfig, enabled: e.target.checked })}
            className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="ragEnabled" className="text-sm font-medium text-gray-700">
            Enable RAG
          </label>
        </div>

        {ragConfig.enabled && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Qdrant URL
              </label>
              <input
                type="text"
                value={ragConfig.qdrant_url}
                onChange={(e) => setRagConfig({ ...ragConfig, qdrant_url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="http://localhost:6333"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Collection Name
              </label>
              <input
                type="text"
                value={ragConfig.collection_name}
                onChange={(e) => setRagConfig({ ...ragConfig, collection_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="query_history"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Embedding Model
              </label>
              <input
                type="text"
                value={ragConfig.embedding_model}
                onChange={(e) => setRagConfig({ ...ragConfig, embedding_model: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="all-MiniLM-L6-v2"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Top K Results
                </label>
                <input
                  type="number"
                  value={ragConfig.top_k}
                  onChange={(e) => setRagConfig({ ...ragConfig, top_k: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="10"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Similarity Threshold
                </label>
                <input
                  type="number"
                  value={ragConfig.similarity_threshold}
                  onChange={(e) => setRagConfig({ ...ragConfig, similarity_threshold: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  max="1"
                  step="0.1"
                />
              </div>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="includeInContext"
                checked={ragConfig.include_in_context}
                onChange={(e) => setRagConfig({ ...ragConfig, include_in_context: e.target.checked })}
                className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="includeInContext" className="text-sm font-medium text-gray-700">
                Include RAG in SQL generation context
              </label>
            </div>
          </>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-3 mb-6">
        <button
          onClick={handleSave}
          disabled={loading}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          <Database size={18} className="mr-2" />
          {loading ? 'Saving...' : 'Save Settings'}
        </button>

        {ragConfig.enabled && (
          <>
            <button
              onClick={() => setShowUploadModal(true)}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400"
            >
              <Upload size={18} className="mr-2" />
              Upload CSV
            </button>

            <button
              onClick={handleClearAll}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400"
            >
              <Trash2 size={18} className="mr-2" />
              Clear All
            </button>
          </>
        )}
      </div>

      {/* CSV Format Info */}
      {ragConfig.enabled && (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <h3 className="font-semibold text-gray-700 mb-2">CSV File Format</h3>
          <p className="text-sm text-gray-600 mb-2">
            Your CSV file should have the following columns:
          </p>
          <code className="block p-2 bg-white border border-gray-300 rounded text-xs overflow-x-auto">
            user_query,sql_query,database_type,schema_name,success
          </code>
          <p className="text-xs text-gray-500 mt-2">
            Example: "Show all users","SELECT * FROM users","postgresql","public",true
          </p>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Upload CSV File</h3>
            
            <div className="mb-4">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              {uploadFile && (
                <p className="mt-2 text-sm text-gray-600">Selected: {uploadFile.name}</p>
              )}
            </div>

            {uploadProgress && (
              <p className="mb-4 text-sm text-gray-600">{uploadProgress}</p>
            )}

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowUploadModal(false);
                  setUploadFile(null);
                  setUploadProgress(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handleUploadCSV}
                disabled={!uploadFile || loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Upload
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RAGSettings;
