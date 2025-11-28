import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Send, Loader2, Database, Settings, LogOut, 
  MessageSquare, Code, Copy, Check, ChevronLeft, ChevronRight 
} from 'lucide-react';
import { api } from '../services/api';
import DataTable from '../components/DataTable';
import SettingsDrawer from '../components/SettingsDrawer';
import SchemaTreeView from '../components/SchemaTreeView';
import LicenseModal from '../components/LicenseModal';

const ChatPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [llmProvider, setLlmProvider] = useState('vllm');
  const [showSettings, setShowSettings] = useState(false);
  const [maxRetries] = useState(3);
  const [schemaName, setSchemaName] = useState('');
  const [retryStatus, setRetryStatus] = useState('');
  const [copiedId, setCopiedId] = useState(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(320); // Default width in pixels
  const [isResizing, setIsResizing] = useState(false);
  const [databaseSchema, setDatabaseSchema] = useState(null);
  const [showLicenseModal, setShowLicenseModal] = useState(false);
  const [licenseInfo, setLicenseInfo] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle sidebar resize
  const startResizing = () => {
    setIsResizing(true);
    document.body.classList.add('resizing-sidebar');
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isResizing) {
        const newWidth = e.clientX;
        if (newWidth >= 200 && newWidth <= 600) { // Min 200px, Max 600px
          setSidebarWidth(newWidth);
        }
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.body.classList.remove('resizing-sidebar');
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.classList.remove('resizing-sidebar');
    };
  }, [isResizing]);

  // Prevent back navigation after login
  useEffect(() => {
    // Define handleDisconnect inside useEffect or use useCallback
    const handleBackButton = async () => {
      try {
        await api.disconnectDatabase();
      } catch (err) {
        console.error('Error disconnecting from backend:', err);
      }
      
      localStorage.clear();
      sessionStorage.clear();
      window.history.replaceState(null, '', '/');
      navigate('/', { replace: true });
    };

    // Push a new state to history to prevent back button
    window.history.pushState(null, '', window.location.pathname);
    
    // Listen for popstate (back button)
    const handlePopState = (e) => {
      // Push forward again to prevent going back
      window.history.pushState(null, '', window.location.pathname);
      
      // Optionally show a warning message
      if (window.confirm('Are you sure you want to logout? All your chat history will be lost.')) {
        handleBackButton();
      }
    };
    
    window.addEventListener('popstate', handlePopState);
    
    // Cleanup
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [navigate]);

  // Fetch database schema on mount
  useEffect(() => {
    const fetchSchema = async () => {
      // First, check if schema was passed from ConnectionPage
      const passedSchema = location.state?.schema;
      
      if (passedSchema) {
        console.log('Using schema from connection:', passedSchema);
        setDatabaseSchema(passedSchema);
        return;
      }
      
      // Fallback: fetch from API if not passed
      try {
        const data = await api.getDatabaseSnapshot();
        console.log('Fetched schema from API:', data);
        
        if (data && data.tables) {
          setDatabaseSchema({
            database_name: data.database_name || 'Database',
            tables: data.tables,
            total_tables: data.table_count || Object.keys(data.tables).length
          });
        } else {
          console.warn('Invalid schema data:', data);
          setDatabaseSchema(null);
        }
      } catch (error) {
        console.error('Failed to fetch schema:', error);
        // Show user-friendly message but don't crash
        setDatabaseSchema(null);
      }
    };
    fetchSchema();
  }, [location]);

  // Load LLM provider from settings on mount
  useEffect(() => {
    const loadProvider = async () => {
      try {
        const data = await api.getSettings();
        if (data && data.settings && data.settings.llm && data.settings.llm.provider) {
          setLlmProvider(data.settings.llm.provider);
        }
      } catch (error) {
        console.error('Failed to load provider settings:', error);
        // Keep default provider if loading fails
      }
    };
    loadProvider();
  }, []);

  // Check license status on mount
  useEffect(() => {
    const checkLicense = async () => {
      try {
        const response = await api.getLicenseInfo();
        if (response.success && response.license_info) {
          setLicenseInfo(response.license_info);
        }
      } catch (error) {
        console.log('No active license found');
      }
    };
    checkLicense();
  }, []);

  // Toast notification handler
  const showToastNotification = (message) => {
    setToastMessage(message);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  // Copy to clipboard handler
  const copyToClipboard = async (text, id) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      showToastNotification('Copied to clipboard!');
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
      showToastNotification('Failed to copy');
    }
  };

  // Schema tree copy handler
  const handleSchemaCopy = (text, type) => {
    showToastNotification(`${type === 'table' ? 'Table' : 'Column'} name copied: ${text}`);
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);
    setRetryStatus('');

    try {
      const response = await api.queryDatabase({
        question: inputValue,
        conversation_history: messages.map(m => ({
          role: m.role,
          content: m.content
        })),
        max_retries: maxRetries,
        schema_name: schemaName || null
      });

      // Show retry status if any retries happened
      if (response.retry_count > 0) {
        setRetryStatus(`✓ Query succeeded after ${response.retry_count} ${response.retry_count === 1 ? 'retry' : 'retries'}`);
      }

      const assistantMessage = {
        role: 'assistant',
        content: response.explanation || 'Query executed successfully',
        sql: response.sql_query,
        results: response.results,
        columns: response.columns,
        rowCount: response.row_count,
        executionTime: response.execution_time,
        retryCount: response.retry_count,
        errorsEncountered: response.errors_encountered || [],
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Query error:', err);
      
      // Check if it's a license error (403)
      if (err.response?.status === 403) {
        setLoading(false);
        setShowLicenseModal(true);
        // Remove the user message since query failed
        setMessages(prev => prev.slice(0, -1));
        setInputValue(userMessage.content); // Restore the input
        return;
      }
      
      // Handle error response
      let errorContent = 'Failed to process query';
      let errorDetails = null;
      
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        
        // Check if detail is an object (error from agent)
        if (typeof detail === 'object') {
          errorContent = detail.error || detail.message || 'Failed to generate valid SQL';
          errorDetails = {
            retryCount: detail.retry_count || 0,
            errors: detail.errors || [],
            sqlQuery: detail.sql_query
          };
        } else {
          // Detail is a string
          errorContent = detail;
        }
      } else if (err.message) {
        errorContent = err.message;
      }
      
      const errorMessage = {
        role: 'error',
        content: errorContent,
        timestamp: new Date().toISOString(),
        ...(errorDetails && {
          retryCount: errorDetails.retryCount,
          errorsEncountered: errorDetails.errors,
          sql: errorDetails.sqlQuery
        })
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    // Show confirmation dialog
    if (!window.confirm('Are you sure you want to logout? All your chat history will be lost.')) {
      return; // User cancelled
    }
    
    try {
      // Call backend to disconnect and clear session
      await api.disconnectDatabase();
    } catch (err) {
      console.error('Error disconnecting from backend:', err);
      // Continue with logout even if backend call fails
    }
    
    // Clear all frontend state
    setMessages([]);
    setDatabaseSchema(null);
    setInputValue('');
    setSchemaName('');
    setRetryStatus('');
    
    // Clear any localStorage or sessionStorage
    localStorage.clear();
    sessionStorage.clear();
    
    // Replace history state to prevent going back
    window.history.replaceState(null, '', '/');
    
    // Navigate to login page
    navigate('/', { replace: true });
  };

  const handleLicenseActivated = (info) => {
    setLicenseInfo(info);
    showToastNotification('License activated successfully!');
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">`
      {/* Toast Notification */}
      {showToast && (
        <div className="fixed top-4 right-4 z-50 animate-fade-in">
          <div className="bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2">
            <Check className="w-5 h-5" />
            <span className="font-medium">{toastMessage}</span>
          </div>
        </div>
      )}

      {/* License Modal */}
      <LicenseModal
        isOpen={showLicenseModal}
        onClose={() => setShowLicenseModal(false)}
        onLicenseActivated={handleLicenseActivated}
      />

      {/* Settings Drawer */}
      <SettingsDrawer
        open={showSettings}
        onClose={async () => {
          setShowSettings(false);
          // Refresh provider after settings change
          try {
            const data = await api.getSettings();
            if (data && data.settings && data.settings.llm && data.settings.llm.provider) {
              setLlmProvider(data.settings.llm.provider);
            }
          } catch (error) {
            console.error('Failed to refresh provider settings:', error);
          }
        }}
      />

      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Sidebar Toggle Button */}
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title={sidebarCollapsed ? 'Expand Schema' : 'Collapse Schema'}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-5 h-5 text-gray-600" />
            ) : (
              <ChevronLeft className="w-5 h-5 text-gray-600" />
            )}
          </button>
          
          <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
            <Database className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">PGAIView</h1>
            <p className="text-xs text-gray-500">Chat with your database</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* LLM Provider Badge */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg text-sm">
            <span className="text-gray-600">LLM:</span>
            <span className="font-medium text-gray-900 uppercase">{llmProvider}</span>
          </div>

          {/* Settings Button */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Settings"
          >
            <Settings className="w-5 h-5 text-gray-600" />
          </button>

          {/* Disconnect Button */}
          <button
            onClick={handleDisconnect}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Disconnect"
          >
            <LogOut className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </header>

      {/* Retry Status */}
      {retryStatus && (
        <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2">
          <p className="text-sm text-yellow-800">{retryStatus}</p>
        </div>
      )}

      {/* Main Content Area with Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Schema Tree */}
        <div
          style={{ width: sidebarCollapsed ? 0 : `${sidebarWidth}px` }}
          className={`bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30 border-r border-gray-200 transition-all duration-300 ease-in-out overflow-hidden relative ${
            isResizing ? 'select-none' : ''
          }`}
        >
          <div className="h-full flex flex-col">
            <div className="px-4 py-3 border-b border-gray-200 bg-white/60 backdrop-blur-sm">
              <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <Database className="w-4 h-4" />
                Database Schema
              </h2>
            </div>
            <div className="flex-1 overflow-hidden">
              <SchemaTreeView 
                onCopy={handleSchemaCopy}
                filteredSchema={databaseSchema}
              />
            </div>
          </div>

          {/* Resize Handle */}
          {!sidebarCollapsed && (
            <div
              className="absolute top-0 right-0 w-1 h-full cursor-ew-resize hover:bg-blue-400 transition-colors group"
              onMouseDown={startResizing}
            >
              <div className="absolute right-0 top-1/2 transform -translate-y-1/2 w-1 h-12 bg-gray-300 group-hover:bg-blue-500 rounded-full transition-colors"></div>
            </div>
          )}
        </div>

        {/* Right Side - Chat Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.length === 0 && (
                <div className="text-center py-12">
                  <MessageSquare className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    Start a conversation
                  </h2>
                  <p className="text-gray-500 max-w-md mx-auto">
                    Ask questions about your database in natural language. 
                    For example: "Show me all users" or "What are the top 10 products by sales?"
                  </p>
                </div>
              )}

              {messages.map((message, index) => (
                <MessageBubble 
                  key={index} 
                  message={message} 
                  onCopy={copyToClipboard}
                  copiedId={copiedId}
                  messageId={`msg-${index}`}
                />
              ))}

              {loading && (
                <div className="flex items-center gap-3 text-gray-500">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span className="text-sm">Processing your query...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Form */}
          <div className="bg-white border-t border-gray-200 px-4 py-4">
            <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask a question about your database..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !inputValue.trim()}
                  className="px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Send className="w-5 h-5" />
                  <span className="hidden sm:inline">Send</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

const MessageBubble = ({ message, onCopy, copiedId, messageId }) => {
  const isUser = message.role === 'user';
  const isError = message.role === 'error';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-3xl w-full ${isUser ? 'ml-12' : 'mr-12'}`}>
        {/* Message Header */}
        <div className={`flex items-center gap-2 mb-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span className="text-xs font-medium text-gray-500">
            {isUser ? 'You' : isError ? 'Error' : 'Assistant'}
          </span>
          <span className="text-xs text-gray-400">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>

        {/* Message Content */}
        <div
          className={`rounded-2xl p-4 relative ${
            isUser
              ? 'bg-primary-500 text-white'
              : isError
              ? 'bg-red-50 border border-red-200'
              : 'bg-white border border-gray-200'
          }`}
        >
          {/* Copy button for user messages */}
          {isUser && (
            <button
              onClick={() => onCopy(message.content, `${messageId}-user`)}
              className="absolute top-2 right-2 p-1.5 hover:bg-primary-600 rounded-lg transition-colors"
              title="Copy message"
            >
              {copiedId === `${messageId}-user` ? (
                <Check className="w-4 h-4 text-white" />
              ) : (
                <Copy className="w-4 h-4 text-white" />
              )}
            </button>
          )}

          <p className={`text-sm ${isUser ? 'pr-8' : ''} ${isError ? 'text-red-700' : ''}`}>
            {message.content}
          </p>

          {/* Retry Information */}
          {message.retryCount > 0 && (
            <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-xs text-yellow-800">
                ⚡ Query succeeded after {message.retryCount} {message.retryCount === 1 ? 'retry' : 'retries'}
              </p>
              {message.errorsEncountered && message.errorsEncountered.length > 0 && (
                <details className="mt-2">
                  <summary className="text-xs text-yellow-700 cursor-pointer hover:underline">
                    View errors encountered
                  </summary>
                  <div className="mt-2 space-y-1">
                    {message.errorsEncountered.map((error, i) => (
                      <p key={i} className="text-xs text-yellow-600 font-mono bg-yellow-100 p-1 rounded">
                        Attempt {i + 1}: {error}
                      </p>
                    ))}
                  </div>
                </details>
              )}
            </div>
          )}

          {/* SQL Query Display */}
          {message.sql && (
            <div className="mt-4 bg-gray-900 rounded-lg p-3 relative">
              {/* Copy button for SQL */}
              <button
                onClick={() => onCopy(message.sql, `${messageId}-sql`)}
                className="absolute top-2 right-2 p-1.5 hover:bg-gray-800 rounded-lg transition-colors z-10"
                title="Copy SQL"
              >
                {copiedId === `${messageId}-sql` ? (
                  <Check className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4 text-gray-400" />
                )}
              </button>
              
              <div className="flex items-center gap-2 mb-2">
                <Code className="w-4 h-4 text-gray-400" />
                <span className="text-xs font-medium text-gray-400">SQL Query</span>
              </div>
              <pre className="text-xs text-green-400 font-mono overflow-x-auto pr-8">
                {message.sql}
              </pre>
            </div>
          )}

          {/* Results Table */}
          {message.results && message.results.length > 0 && (
            <DataTable 
              columns={message.columns}
              data={message.results}
              rowCount={message.rowCount}
              executionTime={message.executionTime}
            />
          )}

          {/* Empty Results */}
          {message.results && message.results.length === 0 && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg text-center">
              <p className="text-sm text-gray-600">No results found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
