import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  FolderOpen, 
  Archive, 
  Edit, 
  Trash2, 
  MoreVertical,
  Calendar,
  User,
  Database
} from 'lucide-react';
import { useAPI } from '../services/api';
import { toast } from 'react-hot-toast';

const Collections = () => {
  const { api } = useAPI();
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingCollection, setEditingCollection] = useState(null);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    client_name: '',
    description: ''
  });

  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      setLoading(true);
      const response = await api.collections.getAll();
      setCollections(response.data);
    } catch (error) {
      console.error('Error loading collections:', error);
      toast.error('Failed to load collections');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await api.collections.create(formData);
      toast.success('Collection created successfully');
      setShowCreateModal(false);
      setFormData({ name: '', client_name: '', description: '' });
      loadCollections();
    } catch (error) {
      console.error('Error creating collection:', error);
      toast.error('Failed to create collection');
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    try {
      await api.collections.update(editingCollection.id, formData);
      toast.success('Collection updated successfully');
      setShowEditModal(false);
      setEditingCollection(null);
      setFormData({ name: '', client_name: '', description: '' });
      loadCollections();
    } catch (error) {
      console.error('Error updating collection:', error);
      toast.error('Failed to update collection');
    }
  };

  const handleDelete = async (collectionId) => {
    if (window.confirm('Are you sure you want to delete this collection?')) {
      try {
        await api.collections.delete(collectionId);
        toast.success('Collection deleted successfully');
        loadCollections();
      } catch (error) {
        console.error('Error deleting collection:', error);
        toast.error('Failed to delete collection');
      }
    }
  };

  const handleArchive = async (collectionId) => {
    try {
      await api.collections.archive(collectionId);
      toast.success('Collection archived successfully');
      loadCollections();
    } catch (error) {
      console.error('Error archiving collection:', error);
      toast.error('Failed to archive collection');
    }
  };

  const handleUnarchive = async (collectionId) => {
    try {
      await api.collections.unarchive(collectionId);
      toast.success('Collection unarchived successfully');
      loadCollections();
    } catch (error) {
      console.error('Error unarchiving collection:', error);
      toast.error('Failed to unarchive collection');
    }
  };

  const openEditModal = (collection) => {
    setEditingCollection(collection);
    setFormData({
      name: collection.name,
      client_name: collection.client_name,
      description: collection.description || ''
    });
    setShowEditModal(true);
  };

  const filteredCollections = collections.filter(collection => {
    const matchesFilter = filter === 'all' || collection.status === filter;
    const matchesSearch = collection.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         collection.client_name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
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
          Collections
        </h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Create Collection</span>
        </button>
      </div>

      {/* Filters */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search collections..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input"
            />
          </div>
          <div className="flex space-x-2">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="input"
            >
              <option value="all">All Collections</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>
      </div>

      {/* Collections Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCollections.map(collection => (
          <div key={collection.id} className="card p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <FolderOpen className="h-8 w-8 text-blue-600" />
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    {collection.name}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {collection.client_name}
                  </p>
                </div>
              </div>
              <span className={`status-badge status-${collection.status}`}>
                {collection.status}
              </span>
            </div>

            {collection.description && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {collection.description}
              </p>
            )}

            <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 mb-4">
              <Calendar className="h-4 w-4 mr-1" />
              <span>Created {formatDate(collection.created_at)}</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex space-x-2">
                <button
                  onClick={() => openEditModal(collection)}
                  className="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                  title="Edit"
                >
                  <Edit className="h-4 w-4" />
                </button>
                <button
                  onClick={() => collection.status === 'active' ? handleArchive(collection.id) : handleUnarchive(collection.id)}
                  className="p-2 text-gray-400 hover:text-yellow-600 dark:hover:text-yellow-400"
                  title={collection.status === 'active' ? 'Archive' : 'Unarchive'}
                >
                  <Archive className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(collection.id)}
                  className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <button className="btn btn-secondary text-xs">
                View Details
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredCollections.length === 0 && (
        <div className="text-center py-12">
          <FolderOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No collections found
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            {searchTerm || filter !== 'all' 
              ? 'Try adjusting your search or filter criteria'
              : 'Get started by creating your first collection'
            }
          </p>
          {!searchTerm && filter === 'all' && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary"
            >
              Create Collection
            </button>
          )}
        </div>
      )}

      {/* Create Collection Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowCreateModal(false)} />
            
            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <form onSubmit={handleCreate}>
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Create New Collection
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Collection Name
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="input"
                        placeholder="Enter collection name"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Client Name
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.client_name}
                        onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                        className="input"
                        placeholder="Enter client name"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Description
                      </label>
                      <textarea
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="input"
                        rows={3}
                        placeholder="Enter description (optional)"
                      />
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="btn btn-primary w-full sm:w-auto sm:ml-3"
                  >
                    Create Collection
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

      {/* Edit Collection Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowEditModal(false)} />
            
            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <form onSubmit={handleEdit}>
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Edit Collection
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Collection Name
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="input"
                        placeholder="Enter collection name"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Client Name
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.client_name}
                        onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                        className="input"
                        placeholder="Enter client name"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Description
                      </label>
                      <textarea
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="input"
                        rows={3}
                        placeholder="Enter description (optional)"
                      />
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="btn btn-primary w-full sm:w-auto sm:ml-3"
                  >
                    Update Collection
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
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

export default Collections;
