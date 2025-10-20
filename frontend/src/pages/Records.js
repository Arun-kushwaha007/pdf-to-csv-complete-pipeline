import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  Download, 
  Eye, 
  Edit, 
  Trash2, 
  CheckCircle, 
  XCircle,
  AlertCircle,
  MoreVertical
} from 'lucide-react';
import { useAPI } from '../services/api';
import { toast } from 'react-hot-toast';

const Records = () => {
  const { api } = useAPI();
  const [records, setRecords] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    collection_id: '',
    include_duplicates: true,
    is_valid: null,
    search: ''
  });
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [showDuplicates, setShowDuplicates] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadRecords();
  }, [filters]);

  const loadData = async () => {
    try {
      const [collectionsRes, recordsRes] = await Promise.all([
        api.collections.getAll(),
        api.records.getAll()
      ]);
      setCollections(collectionsRes.data);
      setRecords(recordsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadRecords = async () => {
    try {
      const response = await api.records.getAll(filters);
      setRecords(response.data);
    } catch (error) {
      console.error('Error loading records:', error);
      toast.error('Failed to load records');
    }
  };

  const handleValidate = async (recordId, isValid) => {
    try {
      await api.records.validate(recordId, isValid);
      toast.success(`Record marked as ${isValid ? 'valid' : 'invalid'}`);
      loadRecords();
    } catch (error) {
      console.error('Error validating record:', error);
      toast.error('Failed to validate record');
    }
  };

  const handleBulkValidate = async (isValid) => {
    if (selectedRecords.length === 0) {
      toast.error('Please select records to validate');
      return;
    }

    try {
      await api.records.bulkValidate(selectedRecords, isValid);
      toast.success(`${selectedRecords.length} records marked as ${isValid ? 'valid' : 'invalid'}`);
      setSelectedRecords([]);
      loadRecords();
    } catch (error) {
      console.error('Error bulk validating records:', error);
      toast.error('Failed to validate records');
    }
  };

  const handleDelete = async (recordId) => {
    if (window.confirm('Are you sure you want to delete this record?')) {
      try {
        await api.records.delete(recordId);
        toast.success('Record deleted successfully');
        loadRecords();
      } catch (error) {
        console.error('Error deleting record:', error);
        toast.error('Failed to delete record');
      }
    }
  };

  const handleBulkDelete = async () => {
    if (selectedRecords.length === 0) {
      toast.error('Please select records to delete');
      return;
    }

    if (window.confirm(`Are you sure you want to delete ${selectedRecords.length} records?`)) {
      try {
        await api.records.bulkDelete(selectedRecords);
        toast.success(`${selectedRecords.length} records deleted successfully`);
        setSelectedRecords([]);
        loadRecords();
      } catch (error) {
        console.error('Error bulk deleting records:', error);
        toast.error('Failed to delete records');
      }
    }
  };

  const toggleRecordSelection = (recordId) => {
    setSelectedRecords(prev => 
      prev.includes(recordId) 
        ? prev.filter(id => id !== recordId)
        : [...prev, recordId]
    );
  };

  const selectAllRecords = () => {
    setSelectedRecords(records.map(record => record.id));
  };

  const clearSelection = () => {
    setSelectedRecords([]);
  };

  const getRowClass = (record) => {
    if (record.is_duplicate) return 'duplicate-row';
    if (!record.is_valid) return 'invalid-row';
    return 'valid-row';
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
          Records Management
        </h1>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {records.length} records
          </span>
          <button
            onClick={() => setShowDuplicates(!showDuplicates)}
            className={`btn ${showDuplicates ? 'btn-primary' : 'btn-secondary'}`}
          >
            {showDuplicates ? 'Hide' : 'Show'} Duplicates
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
              Status
            </label>
            <select
              value={filters.is_valid === null ? '' : filters.is_valid.toString()}
              onChange={(e) => setFilters({ 
                ...filters, 
                is_valid: e.target.value === '' ? null : e.target.value === 'true'
              })}
              className="input"
            >
              <option value="">All Records</option>
              <option value="true">Valid Only</option>
              <option value="false">Invalid Only</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Duplicates
            </label>
            <select
              value={filters.include_duplicates.toString()}
              onChange={(e) => setFilters({ 
                ...filters, 
                include_duplicates: e.target.value === 'true'
              })}
              className="input"
            >
              <option value="true">Include Duplicates</option>
              <option value="false">Exclude Duplicates</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Search
            </label>
            <input
              type="text"
              placeholder="Search records..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="input"
            />
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedRecords.length > 0 && (
        <div className="card p-4 bg-blue-50 dark:bg-blue-900/20">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
              {selectedRecords.length} record(s) selected
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => handleBulkValidate(true)}
                className="btn btn-success text-xs"
              >
                Mark Valid
              </button>
              <button
                onClick={() => handleBulkValidate(false)}
                className="btn btn-secondary text-xs"
              >
                Mark Invalid
              </button>
              <button
                onClick={handleBulkDelete}
                className="btn btn-danger text-xs"
              >
                Delete Selected
              </button>
              <button
                onClick={clearSelection}
                className="btn btn-secondary text-xs"
              >
                Clear Selection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Records Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={selectedRecords.length === records.length && records.length > 0}
                    onChange={selectedRecords.length === records.length ? clearSelection : selectAllRecords}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th>Name</th>
                <th>Mobile</th>
                <th>Address</th>
                <th>Email</th>
                <th>Source File</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {records.map(record => (
                <tr key={record.id} className={getRowClass(record)}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedRecords.includes(record.id)}
                      onChange={() => toggleRecordSelection(record.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td>
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {record.first_name} {record.last_name}
                      </div>
                      {record.is_duplicate && (
                        <span className="text-xs text-yellow-600 dark:text-yellow-400">
                          Duplicate
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="font-mono text-sm">{record.mobile}</td>
                  <td className="max-w-xs truncate">{record.address}</td>
                  <td>{record.email}</td>
                  <td className="text-sm text-gray-500 dark:text-gray-400">
                    {record.source_file}
                  </td>
                  <td>
                    <div className="flex items-center space-x-2">
                      {record.is_valid ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                      <span className="text-xs">
                        {record.is_valid ? 'Valid' : 'Invalid'}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => handleValidate(record.id, !record.is_valid)}
                        className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                        title={record.is_valid ? 'Mark Invalid' : 'Mark Valid'}
                      >
                        {record.is_valid ? (
                          <XCircle className="h-4 w-4" />
                        ) : (
                          <CheckCircle className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDelete(record.id)}
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

      {records.length === 0 && (
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No records found
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Try adjusting your filters or process some PDFs first
          </p>
        </div>
      )}
    </div>
  );
};

export default Records;
