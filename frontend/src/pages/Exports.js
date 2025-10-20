import React, { useState, useEffect } from 'react';
import { 
  Download, 
  FileText, 
  Calendar, 
  CheckCircle, 
  Clock, 
  XCircle,
  Trash2,
  Filter
} from 'lucide-react';
import { useAPI } from '../services/api';
import { toast } from 'react-hot-toast';

const Exports = () => {
  const { api } = useAPI();
  const [exports, setExports] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filters, setFilters] = useState({
    collection_id: '',
    export_type: '',
    status: ''
  });

  // Form state
  const [formData, setFormData] = useState({
    collection_id: '',
    export_type: 'csv',
    include_duplicates: false,
    include_invalid: false,
    group_by: 'collection',
    encoding: 'utf-8',
    delimiter: ','
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadExports();
  }, [filters]);

  const loadData = async () => {
    try {
      const [collectionsRes, exportsRes] = await Promise.all([
        api.collections.getAll(),
        api.exports.getHistory()
      ]);
      setCollections(collectionsRes.data);
      setExports(exportsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadExports = async () => {
    try {
      const response = await api.exports.getHistory(filters);
      setExports(response.data);
    } catch (error) {
      console.error('Error loading exports:', error);
      toast.error('Failed to load exports');
    }
  };

  const handleCreateExport = async (e) => {
    e.preventDefault();
    try {
      await api.exports.generate(formData);
      toast.success('Export started successfully');
      setShowCreateModal(false);
      setFormData({
        collection_id: '',
        export_type: 'csv',
        include_duplicates: false,
        include_invalid: false,
        group_by: 'collection',
        encoding: 'utf-8',
        delimiter: ','
      });
      loadExports();
    } catch (error) {
      console.error('Error creating export:', error);
      toast.error('Failed to create export');
    }
  };

  const handleDownload = async (exportId) => {
    try {
      const response = await api.exports.download(exportId);
      
      // Create blob and download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `export_${exportId}.${response.headers['content-type']?.includes('excel') ? 'xlsx' : 'csv'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Download started');
    } catch (error) {
      console.error('Error downloading export:', error);
      toast.error('Failed to download export');
    }
  };

  const handleDelete = async (exportId) => {
    if (window.confirm('Are you sure you want to delete this export?')) {
      try {
        await api.exports.delete(exportId);
        toast.success('Export deleted successfully');
        loadExports();
      } catch (error) {
        console.error('Error deleting export:', error);
        toast.error('Failed to delete export');
      }
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'processing':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
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
          Export Management
        </h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center space-x-2"
        >
          <Download className="h-4 w-4" />
          <span>Create Export</span>
        </button>
      </div>

      {/* Filters */}
      <div className="card p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Collection
            </label>
            <select
              value={filters.collection_id}
              onChange={(e) => setFilters({ ...filters, collection_id: e.target.value })}
              className="input"
            >
              <option value="">All Collections</option>
              {collections.map(collection => (
                <option key={collection.id} value={collection.id}>
                  {collection.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Export Type
            </label>
            <select
              value={filters.export_type}
              onChange={(e) => setFilters({ ...filters, export_type: e.target.value })}
              className="input"
            >
              <option value="">All Types</option>
              <option value="csv">CSV</option>
              <option value="excel">Excel</option>
              <option value="zip">ZIP</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="input"
            >
              <option value="">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Exports List */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Status</th>
                <th>File Size</th>
                <th>Records</th>
                <th>Created</th>
                <th>Completed</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {exports.map(exportItem => (
                <tr key={exportItem.id}>
                  <td>
                    <div className="flex items-center space-x-2">
                      <FileText className="h-4 w-4 text-gray-500" />
                      <span className="font-medium text-gray-900 dark:text-white">
                        {exportItem.export_type.toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(exportItem.status)}
                      <span className={`status-badge status-${exportItem.status}`}>
                        {exportItem.status}
                      </span>
                    </div>
                  </td>
                  <td className="text-sm text-gray-600 dark:text-gray-400">
                    {formatFileSize(exportItem.file_size)}
                  </td>
                  <td className="text-sm text-gray-600 dark:text-gray-400">
                    {exportItem.record_count || 'N/A'}
                  </td>
                  <td className="text-sm text-gray-600 dark:text-gray-400">
                    {formatDate(exportItem.created_at)}
                  </td>
                  <td className="text-sm text-gray-600 dark:text-gray-400">
                    {exportItem.completed_at ? formatDate(exportItem.completed_at) : 'N/A'}
                  </td>
                  <td>
                    <div className="flex space-x-1">
                      {exportItem.status === 'completed' && (
                        <button
                          onClick={() => handleDownload(exportItem.id)}
                          className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(exportItem.id)}
                        className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {exports.length === 0 && (
        <div className="text-center py-12">
          <Download className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No exports found
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Create your first export to get started
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            Create Export
          </button>
        </div>
      )}

      {/* Create Export Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowCreateModal(false)} />
            
            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <form onSubmit={handleCreateExport}>
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Create New Export
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Collection
                      </label>
                      <select
                        required
                        value={formData.collection_id}
                        onChange={(e) => setFormData({ ...formData, collection_id: e.target.value })}
                        className="input"
                      >
                        <option value="">Select a collection</option>
                        {collections.map(collection => (
                          <option key={collection.id} value={collection.id}>
                            {collection.name} ({collection.client_name})
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Export Type
                      </label>
                      <select
                        value={formData.export_type}
                        onChange={(e) => setFormData({ ...formData, export_type: e.target.value })}
                        className="input"
                      >
                        <option value="csv">CSV</option>
                        <option value="excel">Excel</option>
                        <option value="zip">ZIP (Multiple formats)</option>
                      </select>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Encoding
                        </label>
                        <select
                          value={formData.encoding}
                          onChange={(e) => setFormData({ ...formData, encoding: e.target.value })}
                          className="input"
                        >
                          <option value="utf-8">UTF-8</option>
                          <option value="latin-1">Latin-1</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Delimiter
                        </label>
                        <select
                          value={formData.delimiter}
                          onChange={(e) => setFormData({ ...formData, delimiter: e.target.value })}
                          className="input"
                        >
                          <option value=",">Comma (,)</option>
                          <option value=";">Semicolon (;)</option>
                          <option value="\t">Tab</option>
                        </select>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.include_duplicates}
                          onChange={(e) => setFormData({ ...formData, include_duplicates: e.target.checked })}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          Include duplicate records
                        </span>
                      </label>
                      
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.include_invalid}
                          onChange={(e) => setFormData({ ...formData, include_invalid: e.target.checked })}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          Include invalid records
                        </span>
                      </label>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="btn btn-primary w-full sm:w-auto sm:ml-3"
                  >
                    Create Export
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="btn btn-secondary w-full sm:w-auto mt-3 sm:mt-0"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Exports;
