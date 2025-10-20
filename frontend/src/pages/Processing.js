import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  FileText, 
  X, 
  CheckCircle, 
  AlertCircle,
  Clock,
  Settings as SettingsIcon
} from 'lucide-react';
import { useAPI } from '../services/api';
import { toast } from 'react-hot-toast';

const Processing = () => {
  const { api } = useAPI();
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState('');
  const [groupSize, setGroupSize] = useState(25);
  const [outputFormat, setOutputFormat] = useState('csv');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCollections();
  }, []);

  useEffect(() => {
    if (currentJob) {
      const interval = setInterval(checkJobStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [currentJob]);

  const loadCollections = async () => {
    try {
      const response = await api.collections.getAll({ status: 'active' });
      setCollections(response.data);
      if (response.data.length > 0) {
        setSelectedCollection(response.data[0].id);
      }
    } catch (error) {
      console.error('Error loading collections:', error);
      toast.error('Failed to load collections');
    } finally {
      setLoading(false);
    }
  };

  const checkJobStatus = async () => {
    if (!currentJob) return;

    try {
      const response = await api.files.getJob(currentJob.id);
      const job = response.data;
      setJobStatus(job);

      if (job.status === 'completed') {
        setProcessing(false);
        toast.success(`Processing completed! ${job.total_records} records extracted.`);
        setCurrentJob(null);
        setJobStatus(null);
        setUploadedFiles([]);
      } else if (job.status === 'failed') {
        setProcessing(false);
        toast.error(`Processing failed: ${job.error_message || 'Unknown error'}`);
        setCurrentJob(null);
        setJobStatus(null);
      }
    } catch (error) {
      console.error('Error checking job status:', error);
    }
  };

  const onDrop = (acceptedFiles) => {
    const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== acceptedFiles.length) {
      toast.error('Only PDF files are allowed');
    }

    const newFiles = pdfFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: file.size,
      status: 'ready'
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);
    toast.success(`${pdfFiles.length} PDF file(s) added`);
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const startProcessing = async () => {
    if (!selectedCollection) {
      toast.error('Please select a collection');
      return;
    }

    if (uploadedFiles.length === 0) {
      toast.error('Please upload at least one PDF file');
      return;
    }

    try {
      setProcessing(true);

      // Create FormData
      const formData = new FormData();
      formData.append('collection_id', selectedCollection);
      formData.append('group_size', groupSize.toString());
      formData.append('output_format', outputFormat);

      uploadedFiles.forEach(fileObj => {
        formData.append('files', fileObj.file);
      });

      // Start processing
      const response = await api.files.upload(formData);
      const job = response.data;
      
      setCurrentJob(job);
      toast.success('Processing started!');
      
    } catch (error) {
      console.error('Error starting processing:', error);
      toast.error('Failed to start processing');
      setProcessing(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true,
    disabled: processing
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
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
          Process PDFs
        </h1>
        <div className="flex items-center space-x-2">
          <SettingsIcon className="h-5 w-5 text-gray-500" />
          <span className="text-sm text-gray-500 dark:text-gray-400">
            AI-powered extraction
          </span>
        </div>
      </div>

      {/* Processing Status */}
      {jobStatus && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Processing Status
            </h3>
            <span className={`status-badge status-${jobStatus.status}`}>
              {jobStatus.status}
            </span>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Files Processed
              </span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {jobStatus.processed_files} / {jobStatus.total_files}
              </span>
            </div>
            
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${(jobStatus.processed_files / jobStatus.total_files) * 100}%`
                }}
              ></div>
            </div>
            
            {jobStatus.total_records && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Records Extracted
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {jobStatus.total_records}
                </span>
              </div>
            )}
            
            {jobStatus.duplicates_found && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Duplicates Found
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {jobStatus.duplicates_found}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Configuration */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Processing Configuration
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Collection
            </label>
            <select
              value={selectedCollection}
              onChange={(e) => setSelectedCollection(e.target.value)}
              disabled={processing}
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
              Group Size
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="range"
                min="1"
                max="50"
                value={groupSize}
                onChange={(e) => setGroupSize(parseInt(e.target.value))}
                disabled={processing}
                className="flex-1"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[3rem]">
                {groupSize}
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              PDFs per batch
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Output Format
            </label>
            <select
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value)}
              disabled={processing}
              className="input"
            >
              <option value="csv">CSV</option>
              <option value="excel">Excel</option>
              <option value="both">Both</option>
            </select>
          </div>
        </div>
      </div>

      {/* File Upload */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Upload PDF Files
        </h3>
        
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragActive
              ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          } ${processing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        >
          <input {...getInputProps()} />
          <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          {isDragActive ? (
            <p className="text-lg text-blue-600 dark:text-blue-400">
              Drop the PDF files here...
            </p>
          ) : (
            <div>
              <p className="text-lg text-gray-600 dark:text-gray-400 mb-2">
                Drag & drop PDF files here, or click to select
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                Multiple files supported
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Uploaded Files ({uploadedFiles.length})
          </h3>
          
          <div className="space-y-2">
            {uploadedFiles.map(fileObj => (
              <div
                key={fileObj.id}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {fileObj.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {formatFileSize(fileObj.size)}
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => removeFile(fileObj.id)}
                  disabled={processing}
                  className="text-gray-400 hover:text-red-500 disabled:opacity-50"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Start Processing */}
      <div className="flex justify-end">
        <button
          onClick={startProcessing}
          disabled={processing || !selectedCollection || uploadedFiles.length === 0}
          className="btn btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {processing ? (
            <>
              <Clock className="h-4 w-4 animate-spin" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <CheckCircle className="h-4 w-4" />
              <span>Start Processing</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default Processing;
