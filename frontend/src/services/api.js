import React, { createContext, useContext } from 'react';
import axios from 'axios';

const APIContext = createContext();

export const useAPI = () => {
  const context = useContext(APIContext);
  if (!context) {
    throw new Error('useAPI must be used within an APIProvider');
  }
  return context;
};

export const APIProvider = ({ children }) => {
  // Create axios instance
  const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || '/api',
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  api.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  api.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      if (error.response?.status === 401) {
        // Handle unauthorized access
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  // API methods
  const apiMethods = {
    // Collections
    collections: {
      getAll: (params = {}) => api.get('/collections', { params }),
      getById: (id) => api.get(`/collections/${id}`),
      create: (data) => api.post('/collections', data),
      update: (id, data) => api.put(`/collections/${id}`, data),
      delete: (id) => api.delete(`/collections/${id}`),
      archive: (id) => api.post(`/collections/${id}/archive`),
      unarchive: (id) => api.post(`/collections/${id}/unarchive`),
      getStats: (id) => api.get(`/collections/${id}/stats`),
    },

    // Files
    files: {
      upload: (formData) => api.post('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000, // 5 minutes for file uploads
      }),
      getJob: (jobId) => api.get(`/files/jobs/${jobId}`),
      getJobs: (params = {}) => api.get('/files/jobs', { params }),
      cancelJob: (jobId) => api.delete(`/files/jobs/${jobId}`),
    },

    // Records
    records: {
      getAll: (params = {}) => api.get('/records', { params }),
      getById: (id) => api.get(`/records/${id}`),
      update: (id, data) => api.put(`/records/${id}`, data),
      delete: (id) => api.delete(`/records/${id}`),
      validate: (id, isValid) => api.post(`/records/${id}/validate`, { is_valid: isValid }),
      getDuplicates: (params = {}) => api.get('/records/duplicates/groups', { params }),
      resolveDuplicates: (groupId, keepRecordId) => api.post('/records/duplicates/resolve', {
        duplicate_group_id: groupId,
        keep_record_id: keepRecordId,
      }),
      bulkValidate: (recordIds, isValid) => api.post('/records/bulk/validate', {
        record_ids: recordIds,
        is_valid: isValid,
      }),
      bulkDelete: (recordIds) => api.delete('/records/bulk/delete', {
        data: { record_ids: recordIds },
      }),
      getSummary: (params = {}) => api.get('/records/stats/summary', { params }),
    },

    // Exports
    exports: {
      generate: (data) => api.post('/exports/generate', data),
      get: (id) => api.get(`/exports/${id}`),
      download: (id) => api.get(`/exports/${id}/download`, { responseType: 'blob' }),
      getHistory: (params = {}) => api.get('/exports/history/list', { params }),
      delete: (id) => api.delete(`/exports/${id}`),
      bulkDelete: (exportIds) => api.delete('/exports/bulk/delete', {
        data: { export_ids: exportIds },
      }),
    },

    // System
    system: {
      health: () => api.get('/health'),
      stats: () => api.get('/stats'),
    },
  };

  const value = {
    api: apiMethods,
    axios: api,
  };

  return (
    <APIContext.Provider value={value}>
      {children}
    </APIContext.Provider>
  );
};
