import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom';
import { Stethoscope, ArrowLeft } from 'lucide-react';
import axios from 'axios';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Analytics from './components/Analytics';
import Recorder from './components/Recorder';
import Results from './components/Results';
import AdminDashboard from './components/AdminDashboard';
import PatientPortal from './components/PatientPortal';

// Auth Guard
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return children;
};

// Wrapper for Recorder to handle navigation
const RecordSession = () => {
  const navigate = useNavigate();
  const [viewState, setViewState] = useState('idle'); // idle, uploading
  const [currentRecordId, setCurrentRecordId] = useState(null);

  const handleUploadStart = () => setViewState('uploading');

  const handleUploadSuccess = (id) => {
    setCurrentRecordId(id);
    navigate(`/session/${id}`);
  };

  const handleUploadError = () => {
    setViewState('idle');
    alert("Upload failed");
  };

  // Add Authorization header to axios for upload
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  return (
    <div>
      <button className="btn" onClick={() => navigate('/dashboard')} style={{ marginBottom: '1rem', paddingLeft: 0 }}>
        <ArrowLeft size={20} /> Back to Dashboard
      </button>

      {viewState === 'idle' && (
        <Recorder
          onUploadStart={handleUploadStart}
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
        />
      )}

      {viewState === 'uploading' && (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <h3>Uploading Audio...</h3>
        </div>
      )}
    </div>
  );
};

// Wrapper for Session Details
const SessionDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // Add Authorization header
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  return (
    <div>
      <button className="btn" onClick={() => navigate('/dashboard')} style={{ marginBottom: '1rem', paddingLeft: 0 }}>
        <ArrowLeft size={20} /> Back to Dashboard
      </button>
      <Results recordId={id} />
    </div>
  );
};

function App() {
  return (
    <Router>
      <div className="container">
        <header className="header">
          <div className="logo">
            <Stethoscope size={32} />
            <span>MediScribe AI</span>
          </div>
        </header>

        <main>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/admin" element={
              <ProtectedRoute>
                <AdminDashboard />
              </ProtectedRoute>
            } />
            <Route path="/portal" element={
              <ProtectedRoute>
                <PatientPortal />
              </ProtectedRoute>
            } />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/analytics" element={
              <ProtectedRoute>
                <Analytics />
              </ProtectedRoute>
            } />
            <Route path="/record" element={
              <ProtectedRoute>
                <RecordSession />
              </ProtectedRoute>
            } />
            <Route path="/session/:id" element={
              <ProtectedRoute>
                <SessionDetails />
              </ProtectedRoute>
            } />
            <Route path="/results/:id" element={
              <ProtectedRoute>
                <SessionDetails />
              </ProtectedRoute>
            } />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
