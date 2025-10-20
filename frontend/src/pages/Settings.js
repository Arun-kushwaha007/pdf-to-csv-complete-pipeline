import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Database, 
  Cloud, 
  Shield, 
  Bell,
  Save,
  RefreshCw
} from 'lucide-react';
import { useAPI } from '../services/api';
import { toast } from 'react-hot-toast';

const Settings = () => {
  const { api } = useAPI();
  const [settings, setSettings] = useState({
    // Database settings
    db_host: '',
    db_port: 5432,
    db_name: '',
    db_user: '',
    
    // Processing settings
    default_group_size: 25,
    max_group_size: 100,
    max_concurrent_jobs: 5,
    
    // Export settings
    default_export_format: 'csv',
    default_encoding: 'utf-8',
    default_delimiter: ',',
    
    // System settings
    log_level: 'INFO',
    max_file_size: 100,
    
    // Notifications
    email_notifications: false,
    processing_complete_notifications: true,
    error_notifications: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      // In a real app, this would load from the backend
      // For now, we'll use default values
      setLoading(false);
    } catch (error) {
      console.error('Error loading settings:', error);
      toast.error('Failed to load settings');
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      // In a real app, this would save to the backend
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      toast.success('Settings saved successfully');
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (window.confirm('Are you sure you want to reset all settings to default values?')) {
      setSettings({
        db_host: '',
        db_port: 5432,
        db_name: '',
        db_user: '',
        default_group_size: 25,
        max_group_size: 100,
        max_concurrent_jobs: 5,
        default_export_format: 'csv',
        default_encoding: 'utf-8',
        default_delimiter: ',',
        log_level: 'INFO',
        max_file_size: 100,
        email_notifications: false,
        processing_complete_notifications: true,
        error_notifications: true
      });
      toast.success('Settings reset to defaults');
    }
  };

  const handleTestConnection = async () => {
    try {
      await api.system.health();
      toast.success('Database connection successful');
    } catch (error) {
      console.error('Error testing connection:', error);
      toast.error('Database connection failed');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="space-y-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <div className="flex space-x-3">
          <button
            onClick={handleReset}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Reset</span>
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn btn-primary flex items-center space-x-2"
          >
            <Save className="h-4 w-4" />
            <span>{saving ? 'Saving...' : 'Save Settings'}</span>
          </button>
        </div>
      </div>

      {/* Database Settings */}
      <div className="card p-6">
        <div className="flex items-center mb-4">
          <Database className="h-6 w-6 text-blue-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Database Configuration
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Database Host
            </label>
            <input
              type="text"
              value={settings.db_host}
              onChange={(e) => setSettings({ ...settings, db_host: e.target.value })}
              className="input"
              placeholder="localhost"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Port
            </label>
            <input
              type="number"
              value={settings.db_port}
              onChange={(e) => setSettings({ ...settings, db_port: parseInt(e.target.value) })}
              className="input"
              placeholder="5432"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Database Name
            </label>
            <input
              type="text"
              value={settings.db_name}
              onChange={(e) => setSettings({ ...settings, db_name: e.target.value })}
              className="input"
              placeholder="pdf2csv_db"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Username
            </label>
            <input
              type="text"
              value={settings.db_user}
              onChange={(e) => setSettings({ ...settings, db_user: e.target.value })}
              className="input"
              placeholder="postgres"
            />
          </div>
        </div>
        
        <div className="mt-4">
          <button
            onClick={handleTestConnection}
            className="btn btn-secondary"
          >
            Test Connection
          </button>
        </div>
      </div>

      {/* Processing Settings */}
      <div className="card p-6">
        <div className="flex items-center mb-4">
          <SettingsIcon className="h-6 w-6 text-green-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Processing Configuration
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Default Group Size
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={settings.default_group_size}
              onChange={(e) => setSettings({ ...settings, default_group_size: parseInt(e.target.value) })}
              className="input"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              PDFs per batch
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Max Group Size
            </label>
            <input
              type="number"
              min="1"
              max="200"
              value={settings.max_group_size}
              onChange={(e) => setSettings({ ...settings, max_group_size: parseInt(e.target.value) })}
              className="input"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Maximum PDFs per batch
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Max Concurrent Jobs
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={settings.max_concurrent_jobs}
              onChange={(e) => setSettings({ ...settings, max_concurrent_jobs: parseInt(e.target.value) })}
              className="input"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Simultaneous processing jobs
            </p>
          </div>
        </div>
      </div>

      {/* Export Settings */}
      <div className="card p-6">
        <div className="flex items-center mb-4">
          <Cloud className="h-6 w-6 text-purple-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Export Configuration
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Default Export Format
            </label>
            <select
              value={settings.default_export_format}
              onChange={(e) => setSettings({ ...settings, default_export_format: e.target.value })}
              className="input"
            >
              <option value="csv">CSV</option>
              <option value="excel">Excel</option>
              <option value="both">Both</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Default Encoding
            </label>
            <select
              value={settings.default_encoding}
              onChange={(e) => setSettings({ ...settings, default_encoding: e.target.value })}
              className="input"
            >
              <option value="utf-8">UTF-8</option>
              <option value="latin-1">Latin-1</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Default Delimiter
            </label>
            <select
              value={settings.default_delimiter}
              onChange={(e) => setSettings({ ...settings, default_delimiter: e.target.value })}
              className="input"
            >
              <option value=",">Comma (,)</option>
              <option value=";">Semicolon (;)</option>
              <option value="\t">Tab</option>
            </select>
          </div>
        </div>
      </div>

      {/* System Settings */}
      <div className="card p-6">
        <div className="flex items-center mb-4">
          <Shield className="h-6 w-6 text-red-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            System Configuration
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Log Level
            </label>
            <select
              value={settings.log_level}
              onChange={(e) => setSettings({ ...settings, log_level: e.target.value })}
              className="input"
            >
              <option value="DEBUG">Debug</option>
              <option value="INFO">Info</option>
              <option value="WARNING">Warning</option>
              <option value="ERROR">Error</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Max File Size (MB)
            </label>
            <input
              type="number"
              min="1"
              max="1000"
              value={settings.max_file_size}
              onChange={(e) => setSettings({ ...settings, max_file_size: parseInt(e.target.value) })}
              className="input"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Maximum upload size per file
            </p>
          </div>
        </div>
      </div>

      {/* Notification Settings */}
      <div className="card p-6">
        <div className="flex items-center mb-4">
          <Bell className="h-6 w-6 text-yellow-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Notification Settings
          </h3>
        </div>
        
        <div className="space-y-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.email_notifications}
              onChange={(e) => setSettings({ ...settings, email_notifications: e.target.checked })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Enable email notifications
            </span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.processing_complete_notifications}
              onChange={(e) => setSettings({ ...settings, processing_complete_notifications: e.target.checked })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Notify when processing completes
            </span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.error_notifications}
              onChange={(e) => setSettings({ ...settings, error_notifications: e.target.checked })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Notify on errors
            </span>
          </label>
        </div>
      </div>
    </div>
  );
};

export default Settings;
