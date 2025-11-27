import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { Key, Sparkles, Shield, RefreshCcw, Clock, Lock, Zap } from 'lucide-react';
import GenerateLicense from './components/GenerateLicense';
import ValidateLicense from './components/ValidateLicense';
import RenewLicense from './components/RenewLicense';
import Card from './components/Card';

function App() {
  const [activeTab, setActiveTab] = useState('generate');

  const tabs = [
    { id: 'generate', label: 'Generate', icon: Sparkles },
    { id: 'validate', label: 'Validate', icon: Shield },
    { id: 'renew', label: 'Renew', icon: RefreshCcw },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-gray-100">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <Key className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">PGAIView License Portal</h1>
                <p className="text-xs text-gray-500">Professional License Management</p>
              </div>
            </div>
            <div className="hidden sm:flex items-center space-x-2 text-xs text-gray-600">
              <div className="flex items-center space-x-1 bg-gray-100 px-3 py-1 rounded-full">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Online</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1">
            <nav className="flex space-x-1" aria-label="Tabs">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 text-sm font-medium rounded-lg transition-all ${
                      activeTab === tab.id
                        ? 'bg-primary-600 text-white shadow-sm'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="hidden sm:inline">{tab.label} License</span>
                    <span className="sm:hidden">{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="mb-8">
          {activeTab === 'generate' && <GenerateLicense />}
          {activeTab === 'validate' && <ValidateLicense />}
          {activeTab === 'renew' && <RenewLicense />}
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
            <Clock className="w-10 h-10 text-blue-600 mb-3" />
            <h3 className="font-semibold text-gray-900 mb-2">Instant Generation</h3>
            <p className="text-sm text-gray-600">
              Create licenses in seconds with our streamlined process
            </p>
          </Card>

          <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
            <Lock className="w-10 h-10 text-green-600 mb-3" />
            <h3 className="font-semibold text-gray-900 mb-2">Secure & Encrypted</h3>
            <p className="text-sm text-gray-600">
              Military-grade encryption protects all your licenses
            </p>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
            <Zap className="w-10 h-10 text-purple-600 mb-3" />
            <h3 className="font-semibold text-gray-900 mb-2">Easy Management</h3>
            <p className="text-sm text-gray-600">
              Validate and renew licenses with just a few clicks
            </p>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0">
            <p className="text-sm text-gray-600">
              © 2025 PGAIView. All rights reserved.
            </p>
            <div className="flex items-center space-x-6 text-sm">
              <a href="#" className="text-gray-600 hover:text-primary-600 transition-colors">
                Documentation
              </a>
              <a href="#" className="text-gray-600 hover:text-primary-600 transition-colors">
                Support
              </a>
              <a href="#" className="text-gray-600 hover:text-primary-600 transition-colors">
                API
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
