import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  Download, 
  Edit, 
  Save, 
  RefreshCw, 
  Check, 
  X, 
  FileText,
  Code,
  AlertCircle,
  CheckCircle,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';
import { 
  getOntologySettings, 
  updateOntologySettings, 
  generateDynamicOntology,
  downloadOntologyFile,
  listOntologyFiles
} from '../services/api';

function OntologySettings() {
  const [enabled, setEnabled] = useState(false);
  const [dynamicEnabled, setDynamicEnabled] = useState(true);
  const [format, setFormat] = useState('owl'); // 'owl' or 'yml'
  const [ontologyContent, setOntologyContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [message, setMessage] = useState(null);
  const [ontologyFiles, setOntologyFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadSettings();
    loadOntologyFiles();
  }, []);

  // Add a visibility change effect to refresh files when tab becomes active
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        loadOntologyFiles();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const loadSettings = async () => {
    try {
      const response = await getOntologySettings();
      if (response.data.success) {
        const settings = response.data.settings;
        setEnabled(settings.enabled || false);
        setDynamicEnabled(settings.dynamic_generation?.enabled || false);
        setOntologyContent(settings.content || '');
        setStats(settings.stats || null);
      }
    } catch (error) {
      console.error('Failed to load ontology settings:', error);
      showMessage('error', 'Failed to load settings');
    }
  };

  const loadOntologyFiles = async () => {
    try {
      const response = await listOntologyFiles();
      if (response.data.success) {
        setOntologyFiles(response.data.files || []);
      }
    } catch (error) {
      console.error('Failed to load ontology files:', error);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const response = await updateOntologySettings({
        enabled,
        dynamic_generation: {
          enabled: dynamicEnabled
        },
        content: ontologyContent,
        format
      });

      if (response.data.success) {
        showMessage('success', 'Ontology settings saved successfully');
        setIsEditing(false);
        loadSettings();
      } else {
        showMessage('error', response.data.message || 'Failed to save');
      }
    } catch (error) {
      console.error('Save error:', error);
      showMessage('error', 'Failed to save ontology settings');
    } finally {
      setIsSaving(false);
    }
  };

  // Auto-save when toggling enabled/disabled states
  const handleToggleEnabled = async () => {
    const newEnabled = !enabled;
    setEnabled(newEnabled);
    
    try {
      const response = await updateOntologySettings({
        enabled: newEnabled,
        dynamic_generation: {
          enabled: dynamicEnabled
        },
        content: ontologyContent,
        format
      });

      if (response.data.success) {
        showMessage('success', `Ontology ${newEnabled ? 'enabled' : 'disabled'} successfully`);
      } else {
        // Revert on failure
        setEnabled(!newEnabled);
        showMessage('error', response.data.message || 'Failed to update settings');
      }
    } catch (error) {
      console.error('Toggle error:', error);
      // Revert on failure
      setEnabled(!newEnabled);
      showMessage('error', 'Failed to update ontology settings');
    }
  };

  const handleToggleDynamicEnabled = async () => {
    const newDynamicEnabled = !dynamicEnabled;
    setDynamicEnabled(newDynamicEnabled);
    
    try {
      const response = await updateOntologySettings({
        enabled,
        dynamic_generation: {
          enabled: newDynamicEnabled
        },
        content: ontologyContent,
        format
      });

      if (response.data.success) {
        showMessage('success', `Dynamic generation ${newDynamicEnabled ? 'enabled' : 'disabled'} successfully`);
      } else {
        // Revert on failure
        setDynamicEnabled(!newDynamicEnabled);
        showMessage('error', response.data.message || 'Failed to update settings');
      }
    } catch (error) {
      console.error('Toggle error:', error);
      // Revert on failure
      setDynamicEnabled(!newDynamicEnabled);
      showMessage('error', 'Failed to update dynamic generation settings');
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const response = await generateDynamicOntology({
        force_regenerate: true,
        export_format: 'both'
      });

      if (response.data.success) {
        const data = response.data;
        showMessage(
          'success', 
          `✅ Ontology generated for database "${data.database}": ${data.concepts_count} concepts, ${data.properties_count} properties, ${data.relationships_count} relationships from ${data.tables_analyzed} tables`
        );
        loadSettings();
        loadOntologyFiles();
      } else {
        showMessage('error', response.data.message || 'Failed to generate ontology');
      }
    } catch (error) {
      console.error('Generate error:', error);
      
      // Check if it's a no-connection error
      if (error.response?.status === 400) {
        showMessage(
          'error', 
          error.response.data.detail || 'Please connect to a database first from the main chat page before generating ontology.'
        );
      } else if (error.response?.data?.detail) {
        showMessage('error', error.response.data.detail);
      } else {
        showMessage('error', 'Failed to generate ontology. Please check console for details.');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async (filename) => {
    try {
      const response = await downloadOntologyFile(filename);
      
      // Create blob and download
      const blob = new Blob([response.data], { 
        type: filename.endsWith('.owl') ? 'application/rdf+xml' : 'text/yaml' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      showMessage('success', 'Downloaded successfully');
    } catch (error) {
      console.error('Download error:', error);
      showMessage('error', 'Failed to download file');
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      setOntologyContent(e.target.result);
      setFormat(file.name.endsWith('.owl') ? 'owl' : 'yml');
      setIsEditing(true);
      showMessage('success', 'File loaded successfully');
    };
    reader.readAsText(file);
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Ontology Configuration</h3>
          <p className="text-sm text-gray-600 mt-1">
            Manage domain ontologies for semantic SQL generation
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={isGenerating || !dynamicEnabled}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title={!dynamicEnabled ? 'Enable dynamic generation first' : 'Generate ontology from current database schema'}
          >
            <RefreshCw className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
            {isGenerating ? 'Generating...' : 'Generate Ontology'}
          </button>
        </div>
      </div>

      {/* Connection Warning */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-medium text-blue-900 mb-1">Database Connection Required</h4>
            <p className="text-sm text-blue-700">
              To generate an ontology, you must first connect to a database from the main chat page. 
              The ontology will be created based on the connected database's schema.
            </p>
          </div>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`flex items-center gap-2 p-4 rounded-lg ${
          message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Enable/Disable Toggle */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="space-y-4">
          {/* Main Ontology Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-gray-900">Enable Ontology</h4>
              <p className="text-sm text-gray-600">Use ontology for semantic SQL generation</p>
            </div>
            <button
              onClick={handleToggleEnabled}
              className={`relative inline-flex items-center h-8 w-14 rounded-full transition-colors ${
                enabled ? 'bg-green-500' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block w-6 h-6 transform rounded-full bg-white transition-transform ${
                  enabled ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
              {enabled ? (
                <Check className="absolute left-2 w-4 h-4 text-white" />
              ) : (
                <X className="absolute right-2 w-4 h-4 text-gray-600" />
              )}
            </button>
          </div>

          {/* Dynamic Generation Toggle */}
          <div className="flex items-center justify-between pt-4 border-t">
            <div>
              <h4 className="font-medium text-gray-900">Dynamic Generation</h4>
              <p className="text-sm text-gray-600">Auto-generate ontology from database schema</p>
            </div>
            <button
              onClick={handleToggleDynamicEnabled}
              disabled={!enabled}
              className={`relative inline-flex items-center h-8 w-14 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                dynamicEnabled ? 'bg-blue-500' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block w-6 h-6 transform rounded-full bg-white transition-transform ${
                  dynamicEnabled ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      {stats && enabled && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200 p-6">
          <h4 className="font-medium text-gray-900 mb-4">Current Ontology Statistics</h4>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">{stats.concepts || 0}</div>
              <div className="text-sm text-gray-600">Concepts</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{stats.properties || 0}</div>
              <div className="text-sm text-gray-600">Properties</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{stats.relationships || 0}</div>
              <div className="text-sm text-gray-600">Relationships</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">{stats.tables || 0}</div>
              <div className="text-sm text-gray-600">Tables</div>
            </div>
          </div>
          {stats.generated_at && (
            <div className="text-xs text-gray-500 mt-4 text-center">
              Generated: {new Date(stats.generated_at).toLocaleString()}
            </div>
          )}
        </div>
      )}

      {/* Format Selection */}
      {enabled && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h4 className="font-medium text-gray-900 mb-4">Ontology Format</h4>
          <div className="flex gap-4">
            <button
              onClick={() => setFormat('owl')}
              className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border-2 transition-all ${
                format === 'owl'
                  ? 'border-purple-500 bg-purple-50 text-purple-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <Code className="w-5 h-5" />
              <div className="text-left">
                <div className="font-medium">OWL (RDF/XML)</div>
                <div className="text-xs text-gray-600">W3C Standard Format</div>
              </div>
            </button>
            
            <button
              onClick={() => setFormat('yml')}
              className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border-2 transition-all ${
                format === 'yml'
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <FileText className="w-5 h-5" />
              <div className="text-left">
                <div className="font-medium">YAML</div>
                <div className="text-xs text-gray-600">Human-Readable Format</div>
              </div>
            </button>
          </div>
        </div>
      )}

      {/* Editor */}
      {enabled && !dynamicEnabled && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">Manual Ontology Definition</h4>
            <div className="flex gap-2">
              <label className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 cursor-pointer transition-colors">
                <Upload className="w-4 h-4" />
                Upload File
                <input
                  type="file"
                  accept=".owl,.yml,.yaml"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
              
              {isEditing ? (
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Edit className="w-4 h-4" />
                  Edit
                </button>
              )}
            </div>
          </div>

          <textarea
            value={ontologyContent}
            onChange={(e) => setOntologyContent(e.target.value)}
            disabled={!isEditing}
            placeholder={format === 'owl' 
              ? '<?xml version="1.0"?>\n<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"...'
              : 'concepts:\n  - name: Customer\n    description: ...\n    properties:\n      - ...'
            }
            className="w-full h-96 p-4 font-mono text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600"
          />
        </div>
      )}

      {/* Exported Files */}
      {enabled && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">Exported Ontology Files</h4>
            <button
              onClick={loadOntologyFiles}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              title="Refresh file list"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-blue-800">
                Files are filtered by your current database connection. Switch databases to see different ontology files.
              </span>
            </div>
          </div>

          {ontologyFiles.length > 0 ? (
            <div className="space-y-2">
              {ontologyFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {file.filename.endsWith('.owl') ? (
                      <Code className="w-5 h-5 text-purple-600" />
                    ) : (
                      <FileText className="w-5 h-5 text-blue-600" />
                    )}
                    <div>
                      <div className="font-medium text-gray-900">{file.filename}</div>
                      <div className="text-xs text-gray-600">
                        {formatFileSize(file.size)} • {new Date(file.timestamp).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => handleDownload(file.filename)}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p>No ontology files found for current database connection</p>
              <p className="text-sm mt-1">Generate an ontology to create files</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default OntologySettings;
