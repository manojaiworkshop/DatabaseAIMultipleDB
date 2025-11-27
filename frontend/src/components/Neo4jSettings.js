import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Database, 
  Check, 
  X, 
  RefreshCw, 
  Activity,
  AlertCircle,
  Loader,
  Zap
} from 'lucide-react';
import { testNeo4jConnection, syncSchemaToNeo4j, getNeo4jStatus, updateSettings, getSettings } from '../services/api';

const Neo4jSettings = () => {
  const [config, setConfig] = useState({
    enabled: false,
    uri: 'bolt://localhost:7687',
    username: 'neo4j',
    password: '',
    database: 'neo4j',
    auto_sync: true,
    max_relationship_depth: 2,
    include_in_context: true
  });

  const [status, setStatus] = useState({
    enabled: false,
    connected: false,
    message: '',
    statistics: null
  });

  const [testing, setTesting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState(null);

  useEffect(() => {
    loadSettings();
    loadStatus();
  }, []);

  const loadSettings = async () => {
    try {
      // Use the getSettings API to get all settings including neo4j
      const response = await getSettings();
      if (response.success && response.settings && response.settings.neo4j) {
        setConfig({ ...config, ...response.settings.neo4j });
      }
    } catch (error) {
      console.error('Failed to load Neo4j settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStatus = async () => {
    try {
      const statusData = await getNeo4jStatus();
      setStatus(statusData);
    } catch (error) {
      console.error('Failed to load Neo4j status:', error);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    try {
      const result = await testNeo4jConnection({
        uri: config.uri,
        username: config.username,
        password: config.password,
        database: config.database
      });

      if (result.success) {
        setSaveStatus({ type: 'success', message: '✅ Connection successful!' });
      } else {
        setSaveStatus({ type: 'error', message: `❌ ${result.message}` });
      }

      setTimeout(() => setSaveStatus(null), 5000);
    } catch (error) {
      setSaveStatus({ type: 'error', message: `❌ Connection failed: ${error.message}` });
      setTimeout(() => setSaveStatus(null), 5000);
    } finally {
      setTesting(false);
    }
  };

  const handleSyncSchema = async (clearExisting = false) => {
    if (!config.enabled) {
      setSaveStatus({ 
        type: 'error', 
        message: '❌ Cannot sync: Neo4j is disabled. Please enable it first.' 
      });
      setTimeout(() => setSaveStatus(null), 5000);
      return;
    }

    if (!status.connected) {
      setSaveStatus({ 
        type: 'error', 
        message: '❌ Cannot sync: Neo4j is not connected. Please check your connection settings and test connection.' 
      });
      setTimeout(() => setSaveStatus(null), 5000);
      return;
    }

    setSyncing(true);
    try {
      const result = await syncSchemaToNeo4j({ clear_existing: clearExisting });
      
      if (result.success) {
        setSaveStatus({ 
          type: 'success', 
          message: `✅ Schema synced! ${result.statistics?.tables || 0} tables processed` 
        });
        await loadStatus(); // Refresh status to show updated statistics
      } else {
        setSaveStatus({ type: 'error', message: `❌ Sync failed: ${result.message}` });
      }

      setTimeout(() => setSaveStatus(null), 5000);
    } catch (error) {
      setSaveStatus({ type: 'error', message: `❌ Sync failed: ${error.message}` });
      setTimeout(() => setSaveStatus(null), 5000);
    } finally {
      setSyncing(false);
    }
  };

  const handleSave = async () => {
    try {
      const response = await updateSettings('neo4j', config);
      
      if (response.success) {
        setSaveStatus({ type: 'success', message: '✅ Settings saved successfully!' });
        await loadStatus(); // Refresh status
      } else {
        setSaveStatus({ type: 'error', message: `❌ Failed to save: ${response.message}` });
      }

      setTimeout(() => setSaveStatus(null), 5000);
    } catch (error) {
      setSaveStatus({ type: 'error', message: `❌ Save failed: ${error.message}` });
      setTimeout(() => setSaveStatus(null), 5000);
    }
  };

  const handleChange = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  // Auto-save when toggling enabled state
  const handleToggleEnabled = async (newEnabled) => {
    const oldEnabled = config.enabled;
    setConfig(prev => ({ ...prev, enabled: newEnabled }));
    
    try {
      const response = await updateSettings('neo4j', { ...config, enabled: newEnabled });
      
      if (response.success) {
        setSaveStatus({ 
          type: 'success', 
          message: `✅ Neo4j ${newEnabled ? 'enabled' : 'disabled'} successfully!` 
        });
        await loadStatus();
      } else {
        // Revert on failure
        setConfig(prev => ({ ...prev, enabled: oldEnabled }));
        setSaveStatus({ type: 'error', message: `❌ Failed to update: ${response.message}` });
      }

      setTimeout(() => setSaveStatus(null), 5000);
    } catch (error) {
      // Revert on failure
      setConfig(prev => ({ ...prev, enabled: oldEnabled }));
      setSaveStatus({ type: 'error', message: `❌ Update failed: ${error.message}` });
      setTimeout(() => setSaveStatus(null), 5000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">Loading Neo4j settings...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Status */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <Database className="w-8 h-8 text-blue-600 mt-1" />
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                Neo4j Knowledge Graph
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Enhance SQL generation with graph-based relationship understanding
              </p>
            </div>
          </div>
          
          {status.connected ? (
            <div className="flex items-center space-x-2 bg-green-100 text-green-800 px-3 py-1 rounded-full">
              <Activity className="w-4 h-4" />
              <span className="text-sm font-medium">Connected</span>
            </div>
          ) : status.enabled ? (
            <div className="flex items-center space-x-2 bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm font-medium">Disconnected</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 bg-gray-100 text-gray-600 px-3 py-1 rounded-full">
              <X className="w-4 h-4" />
              <span className="text-sm font-medium">Disabled</span>
            </div>
          )}
        </div>

        {/* Statistics */}
        {status.statistics && (
          <div className="mt-4 grid grid-cols-4 gap-4">
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="text-2xl font-bold text-blue-600">{status.statistics.tables || 0}</div>
              <div className="text-xs text-gray-600">Tables</div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="text-2xl font-bold text-blue-600">{status.statistics.columns || 0}</div>
              <div className="text-xs text-gray-600">Columns</div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="text-2xl font-bold text-blue-600">{status.statistics.nodes || 0}</div>
              <div className="text-xs text-gray-600">Nodes</div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="text-2xl font-bold text-blue-600">{status.statistics.relationships || 0}</div>
              <div className="text-xs text-gray-600">Relationships</div>
            </div>
          </div>
        )}
      </div>

      {/* Enable/Disable Toggle */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <div className="flex items-center justify-between">
          <div>
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={config.enabled}
                onChange={(e) => handleToggleEnabled(e.target.checked)}
                className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="text-base font-medium text-gray-900">
                Enable Knowledge Graph
              </span>
            </label>
            <p className="text-sm text-gray-500 ml-8 mt-1">
              Use Neo4j to build a graph representation of your database schema for better SQL generation
            </p>
          </div>
          <Zap className={`w-6 h-6 ${config.enabled ? 'text-blue-500' : 'text-gray-400'}`} />
        </div>
      </div>

      {/* Connection Settings */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Connection Settings</h4>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Neo4j URI
            </label>
            <input
              type="text"
              value={config.uri}
              onChange={(e) => handleChange('uri', e.target.value)}
              placeholder="bolt://localhost:7687"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={!config.enabled}
            />
            <p className="text-xs text-gray-500 mt-1">
              Connection URI (bolt:// or neo4j://)
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <input
                type="text"
                value={config.username}
                onChange={(e) => handleChange('username', e.target.value)}
                placeholder="neo4j"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={!config.enabled}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                value={config.password}
                onChange={(e) => handleChange('password', e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={!config.enabled}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Database Name
            </label>
            <input
              type="text"
              value={config.database}
              onChange={(e) => handleChange('database', e.target.value)}
              placeholder="neo4j"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={!config.enabled}
            />
          </div>

          <button
            onClick={handleTestConnection}
            disabled={!config.enabled || testing}
            className="w-full flex items-center justify-center space-x-2 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {testing ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                <span>Testing Connection...</span>
              </>
            ) : (
              <>
                <Shield className="w-5 h-5" />
                <span>Test Connection</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Graph Settings */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Graph Settings</h4>
        
        <div className="space-y-4">
          <label className="flex items-start space-x-3">
            <input
              type="checkbox"
              checked={config.auto_sync}
              onChange={(e) => handleChange('auto_sync', e.target.checked)}
              disabled={!config.enabled}
              className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500 mt-1"
            />
            <div>
              <span className="text-sm font-medium text-gray-900">Auto-sync Schema</span>
              <p className="text-xs text-gray-500 mt-1">
                Automatically sync database schema to graph on connection
              </p>
            </div>
          </label>

          <label className="flex items-start space-x-3">
            <input
              type="checkbox"
              checked={config.include_in_context}
              onChange={(e) => handleChange('include_in_context', e.target.checked)}
              disabled={!config.enabled}
              className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500 mt-1"
            />
            <div>
              <span className="text-sm font-medium text-gray-900">Include in Context</span>
              <p className="text-xs text-gray-500 mt-1">
                Include graph insights in SQL agent prompts for better query generation
              </p>
            </div>
          </label>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Relationship Depth: {config.max_relationship_depth}
            </label>
            <input
              type="range"
              min="1"
              max="5"
              value={config.max_relationship_depth}
              onChange={(e) => handleChange('max_relationship_depth', parseInt(e.target.value))}
              disabled={!config.enabled}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1 (Direct)</span>
              <span>5 (Deep)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sync Actions */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Sync Actions</h4>
        
        {!config.enabled && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-yellow-800">
                Neo4j is currently <strong>disabled</strong>. Enable it above to sync your database schema to the knowledge graph.
              </p>
            </div>
          </div>
        )}

        {config.enabled && !status.connected && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-800">
                Neo4j is <strong>enabled</strong> but <strong>not connected</strong>. Please verify your connection settings and test the connection before syncing.
              </p>
            </div>
          </div>
        )}

        {config.enabled && status.connected && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <Check className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-green-800">
                Neo4j is <strong>connected</strong> and ready to sync. Click the buttons below to sync your database schema.
              </p>
            </div>
          </div>
        )}
        
        <div className="space-y-3">
          <button
            onClick={() => handleSyncSchema(false)}
            disabled={!config.enabled || !status.connected || syncing}
            className="w-full flex items-center justify-center space-x-2 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            title={!config.enabled ? "Enable Neo4j first" : !status.connected ? "Connect to Neo4j first" : "Sync schema to graph"}
          >
            {syncing ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                <span>Syncing...</span>
              </>
            ) : (
              <>
                <RefreshCw className="w-5 h-5" />
                <span>Sync Schema to Graph</span>
              </>
            )}
          </button>

          <button
            onClick={() => handleSyncSchema(true)}
            disabled={!config.enabled || !status.connected || syncing}
            className="w-full flex items-center justify-center space-x-2 bg-orange-600 text-white py-2 px-4 rounded-lg hover:bg-orange-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            title={!config.enabled ? "Enable Neo4j first" : !status.connected ? "Connect to Neo4j first" : "Clear existing graph and rebuild"}
          >
            <RefreshCw className="w-5 h-5" />
            <span>Clear & Rebuild Graph</span>
          </button>

          <p className="text-xs text-gray-500 text-center">
            {!config.enabled 
              ? "Enable Neo4j above to use knowledge graph features"
              : !status.connected
              ? "Test connection above before syncing"
              : "Sync your database schema to the knowledge graph for enhanced query understanding"
            }
          </p>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="flex-1">
          {saveStatus && (
            <div
              className={`text-sm px-4 py-2 rounded-lg ${
                saveStatus.type === 'success'
                  ? 'bg-green-50 text-green-800 border border-green-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}
            >
              {saveStatus.message}
            </div>
          )}
        </div>
        <button
          onClick={handleSave}
          className="ml-4 flex items-center space-x-2 bg-blue-600 text-white py-2 px-6 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Check className="w-5 h-5" />
          <span>Save Settings</span>
        </button>
      </div>
    </div>
  );
};

export default Neo4jSettings;
