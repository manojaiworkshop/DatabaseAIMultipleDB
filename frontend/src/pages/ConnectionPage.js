import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, Loader2, CheckCircle, XCircle, Server } from 'lucide-react';
import { api } from '../services/api';

const ConnectionPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [formData, setFormData] = useState({
    database_type: 'postgresql',
    host: 'localhost',
    port: 5432,
    database: '',
    username: 'postgres',
    password: '',
    sid: '',
    service_name: '',
    file_path: '',
    use_docker: false,
    docker_container: '',
  });

  // Clear any residual data on mount
  useEffect(() => {
    // Clear localStorage and sessionStorage to ensure fresh start
    localStorage.clear();
    sessionStorage.clear();
    
    // Prevent going back to chat page after logout
    // Replace current history entry
    window.history.replaceState(null, '', '/');
    
    // Add popstate listener to prevent back navigation
    const handlePopState = (e) => {
      // Prevent navigation back to chat
      window.history.pushState(null, '', '/');
    };
    
    window.addEventListener('popstate', handlePopState);
    
    // Cleanup
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    let newValue = type === 'checkbox' ? checked : value;
    
    // Update form data
    const updatedFormData = {
      ...formData,
      [name]: newValue
    };
    
    // Set default ports when database type changes
    if (name === 'database_type') {
      switch (newValue) {
        case 'postgresql':
          updatedFormData.port = 5432;
          updatedFormData.username = 'postgres';
          break;
        case 'oracle':
          updatedFormData.port = 1521;
          updatedFormData.username = 'system';
          break;
        case 'mysql':
          updatedFormData.port = 3306;
          updatedFormData.username = 'root';
          break;
        case 'sqlite':
          updatedFormData.port = '';
          updatedFormData.host = '';
          updatedFormData.username = '';
          break;
        default:
          break;
      }
    }
    
    setFormData(updatedFormData);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await api.connectDatabase(formData);
      
      if (response.success) {
        setSuccess(`Connected successfully! Database: ${response.database_info.database}`);
        
        // Extract schema from connection response
        const schema = response.database_info?.schema || null;
        
        // Navigate to chat with schema data
        setTimeout(() => {
          navigate('/chat', { 
            state: { 
              schema: schema,
              databaseInfo: response.database_info 
            } 
          });
        }, 1000);
      } else {
        setError(response.message || 'Connection failed');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Connection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-500 rounded-full mb-4">
            <Database className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">DatabaseAI</h1>
          <p className="text-gray-600">Connect to your database to get started</p>
        </div>

        {/* Connection Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Database Type Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Database Type
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <button
                  type="button"
                  onClick={() => handleChange({ target: { name: 'database_type', value: 'postgresql' } })}
                  className={`p-4 border-2 rounded-lg flex flex-col items-center justify-center gap-2 transition-all ${
                    formData.database_type === 'postgresql'
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Server className="w-6 h-6" />
                  <span className="text-sm font-medium">PostgreSQL</span>
                </button>
                
                <button
                  type="button"
                  onClick={() => handleChange({ target: { name: 'database_type', value: 'oracle' } })}
                  className={`p-4 border-2 rounded-lg flex flex-col items-center justify-center gap-2 transition-all ${
                    formData.database_type === 'oracle'
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Database className="w-6 h-6" />
                  <span className="text-sm font-medium">Oracle</span>
                </button>
                
                <button
                  type="button"
                  onClick={() => handleChange({ target: { name: 'database_type', value: 'mysql' } })}
                  className={`p-4 border-2 rounded-lg flex flex-col items-center justify-center gap-2 transition-all ${
                    formData.database_type === 'mysql'
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Database className="w-6 h-6" />
                  <span className="text-sm font-medium">MySQL</span>
                </button>
                
                <button
                  type="button"
                  onClick={() => handleChange({ target: { name: 'database_type', value: 'sqlite' } })}
                  className={`p-4 border-2 rounded-lg flex flex-col items-center justify-center gap-2 transition-all ${
                    formData.database_type === 'sqlite'
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Database className="w-6 h-6" />
                  <span className="text-sm font-medium">SQLite</span>
                </button>
              </div>
            </div>

            {/* Conditional Fields based on Database Type */}
            {formData.database_type !== 'sqlite' && (
              <>
                {/* Docker Info Banner for All Database Types */}
                {formData.database_type !== 'sqlite' && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <div className="flex items-start">
                      <Server className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-blue-900 mb-1">
                          {formData.database_type === 'postgresql' && 'PostgreSQL Connection Tip'}
                          {formData.database_type === 'mysql' && 'MySQL Connection Tip'}
                          {formData.database_type === 'oracle' && 'Oracle Connection Tip'}
                          {formData.database_type === 'neo4j' && 'Neo4j Connection Tip'}
                        </p>
                        <p className="text-sm text-blue-700">
                          {formData.database_type === 'postgresql' && (
                            <>
                              If running in Docker with our compose file, use <code className="bg-blue-100 px-1 rounded">postgres-db</code> as host (default port: 5432, user: postgres, password: postgres123).
                              <br />
                              For external PostgreSQL, use <code className="bg-blue-100 px-1 rounded">localhost</code> or your server's IP/hostname.
                            </>
                          )}
                          {formData.database_type === 'mysql' && (
                            <>
                              If running in Docker with our compose file, use <code className="bg-blue-100 px-1 rounded">mysql-db</code> as host (default port: 3306, user: root, password: mysql123).
                              <br />
                              For external MySQL, use <code className="bg-blue-100 px-1 rounded">localhost</code> or your server's IP/hostname.
                            </>
                          )}
                          {formData.database_type === 'oracle' && (
                            <>
                              If running in Docker with our compose file, use <code className="bg-blue-100 px-1 rounded">oracle-db</code> as host (default port: 1521, service: XEPDB1, user: system, password: oracle123).
                              <br />
                              For external Oracle, use <code className="bg-blue-100 px-1 rounded">localhost</code> or your server's IP/hostname.
                            </>
                          )}
                          {formData.database_type === 'neo4j' && (
                            <>
                              If running in Docker with our compose file, use <code className="bg-blue-100 px-1 rounded">neo4j-db</code> as host (default ports: 7474/7687, user: neo4j, password: neo4j123).
                              <br />
                              For external Neo4j, use <code className="bg-blue-100 px-1 rounded">localhost</code> or your server's IP/hostname.
                            </>
                          )}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Host & Port */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Host
                    </label>
                    <input
                      type="text"
                      name="host"
                      value={formData.host}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder={formData.database_type === 'oracle' ? 'oracle-db' : 'localhost'}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Port
                    </label>
                    <input
                      type="number"
                      name="port"
                      value={formData.port}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder={formData.database_type === 'oracle' ? '1521' : formData.database_type === 'mysql' ? '3306' : '5432'}
                      required
                    />
                  </div>
                </div>

                {/* Database Name / SID / Service Name */}
                {formData.database_type === 'oracle' ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        SID (Optional)
                      </label>
                      <input
                        type="text"
                        name="sid"
                        value={formData.sid}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="ORCL"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Service Name (Optional)
                      </label>
                      <input
                        type="text"
                        name="service_name"
                        value={formData.service_name}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="XEPDB1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Provide either SID or Service Name (default for Oracle XE: XEPDB1)</p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Database Name
                    </label>
                    <input
                      type="text"
                      name="database"
                      value={formData.database}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder="my_database"
                      required
                    />
                  </div>
                )}

                {/* Username & Password */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Username
                    </label>
                    <input
                      type="text"
                      name="username"
                      value={formData.username}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder={formData.database_type === 'oracle' ? 'system' : formData.database_type === 'mysql' ? 'root' : 'postgres'}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Password
                    </label>
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                </div>
              </>
            )}

            {/* SQLite File Path */}
            {formData.database_type === 'sqlite' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Database File Path
                </label>
                <input
                  type="text"
                  name="file_path"
                  value={formData.file_path}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="/path/to/database.db"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Absolute path to your SQLite database file</p>
              </div>
            )}

            {/* Docker Options */}
            <div className="border-t pt-6">
              <div className="flex items-center mb-4">
                <input
                  type="checkbox"
                  name="use_docker"
                  id="use_docker"
                  checked={formData.use_docker}
                  onChange={handleChange}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <label htmlFor="use_docker" className="ml-2 text-sm font-medium text-gray-700">
                  Use Docker Container
                </label>
              </div>

              {formData.use_docker && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Docker Container Name
                  </label>
                  <input
                    type="text"
                    name="docker_container"
                    value={formData.docker_container}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="postgres"
                  />
                </div>
              )}
            </div>

            {/* Error/Success Messages */}
            {error && (
              <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
                <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {success && (
              <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                <p className="text-sm text-green-700">{success}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-500 hover:bg-primary-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Connecting...
                </>
              ) : (
                'Connect to Database'
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-gray-500 text-sm mt-6">
          Your connection details are secure and only stored in memory
        </p>
      </div>
    </div>
  );
};

export default ConnectionPage;
