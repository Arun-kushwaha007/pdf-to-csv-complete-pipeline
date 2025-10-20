import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FolderOpen, 
  Upload, 
  Database, 
  Download, 
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { useAPI } from '../services/api';
import { toast } from 'react-hot-toast';

const Dashboard = () => {
  const { api } = useAPI();
  const [stats, setStats] = useState({
    collections: 0,
    records: 0,
    processing_jobs: 0,
  });
  const [recentCollections, setRecentCollections] = useState([]);
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load stats
      const statsResponse = await api.system.stats();
      setStats(statsResponse.data);

      // Load recent collections
      const collectionsResponse = await api.collections.getAll({ limit: 5 });
      setRecentCollections(collectionsResponse.data);

      // Load recent processing jobs
      const jobsResponse = await api.files.getJobs({ limit: 5 });
      setRecentJobs(jobsResponse.data);

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
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
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 dark:text-green-400';
      case 'processing':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'failed':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
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
          Dashboard
        </h1>
        <div className="flex space-x-3">
          <Link
            to="/collections"
            className="btn btn-secondary flex items-center space-x-2"
          >
            <FolderOpen className="h-4 w-4" />
            <span>Manage Collections</span>
          </Link>
          <Link
            to="/processing"
            className="btn btn-primary flex items-center space-x-2"
          >
            <Upload className="h-4 w-4" />
            <span>Process PDFs</span>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <FolderOpen className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Total Collections
              </p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {stats.collections}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Database className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Total Records
              </p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {stats.records.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Processing Jobs
              </p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {stats.processing_jobs}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Collections */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Recent Collections
            </h3>
            <Link
              to="/collections"
              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {recentCollections.length > 0 ? (
              recentCollections.map((collection) => (
                <div
                  key={collection.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {collection.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {collection.client_name}
                    </p>
                  </div>
                  <span className={`status-badge status-${collection.status}`}>
                    {collection.status}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                No collections found
              </p>
            )}
          </div>
        </div>

        {/* Recent Processing Jobs */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Recent Processing Jobs
            </h3>
            <Link
              to="/processing"
              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {recentJobs.length > 0 ? (
              recentJobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(job.status)}
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        Job {job.id.slice(0, 8)}...
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {job.processed_files}/{job.total_files} files
                      </p>
                    </div>
                  </div>
                  <span className={`text-xs font-medium ${getStatusColor(job.status)}`}>
                    {job.status}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                No processing jobs found
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            to="/collections"
            className="flex items-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
          >
            <FolderOpen className="h-6 w-6 text-blue-600 dark:text-blue-400 mr-3" />
            <div>
              <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                Create Collection
              </p>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Organize your data
              </p>
            </div>
          </Link>

          <Link
            to="/processing"
            className="flex items-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
          >
            <Upload className="h-6 w-6 text-green-600 dark:text-green-400 mr-3" />
            <div>
              <p className="text-sm font-medium text-green-900 dark:text-green-100">
                Process PDFs
              </p>
              <p className="text-xs text-green-700 dark:text-green-300">
                Extract contacts
              </p>
            </div>
          </Link>

          <Link
            to="/records"
            className="flex items-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg hover:bg-yellow-100 dark:hover:bg-yellow-900/30 transition-colors"
          >
            <Database className="h-6 w-6 text-yellow-600 dark:text-yellow-400 mr-3" />
            <div>
              <p className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                View Records
              </p>
              <p className="text-xs text-yellow-700 dark:text-yellow-300">
                Manage data
              </p>
            </div>
          </Link>

          <Link
            to="/exports"
            className="flex items-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
          >
            <Download className="h-6 w-6 text-purple-600 dark:text-purple-400 mr-3" />
            <div>
              <p className="text-sm font-medium text-purple-900 dark:text-purple-100">
                Export Data
              </p>
              <p className="text-xs text-purple-700 dark:text-purple-300">
                Download results
              </p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
