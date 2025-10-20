import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './contexts/ThemeContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Collections from './pages/Collections';
import Processing from './pages/Processing';
import Records from './pages/Records';
import Exports from './pages/Exports';
import Settings from './pages/Settings';
import { APIProvider } from './services/api';

function App() {
  return (
    <ThemeProvider>
      <APIProvider>
        <Router>
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/collections" element={<Collections />} />
                <Route path="/processing" element={<Processing />} />
                <Route path="/records" element={<Records />} />
                <Route path="/exports" element={<Exports />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: 'var(--toast-bg)',
                  color: 'var(--toast-color)',
                },
              }}
            />
          </div>
        </Router>
      </APIProvider>
    </ThemeProvider>
  );
}

export default App;
