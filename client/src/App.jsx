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
import NoteDetails from './components/NoteDetails';

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
  const role = localStorage.getItem('role');

  // Add Authorization header
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  const handleDelete = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    const ok = window.confirm('Delete this transcript/session? This cannot be undone.');
    if (!ok) return;

    try {
      await axios.delete(`http://localhost:8002/api/records/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      alert('Failed to delete session.');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginBottom: '1rem' }}>
        <button className="btn" onClick={() => navigate('/dashboard')} style={{ paddingLeft: 0 }}>
          <ArrowLeft size={20} /> Back to Dashboard
        </button>
        {role !== 'patient' && (
          <button className="btn" onClick={handleDelete} style={{ background: 'var(--error)', color: 'white', border: 'none' }}>
            Delete
          </button>
        )}
      </div>
      <Results recordId={id} />
    </div>
  );
};

// Wrapper for OCR Note Details
const NoteDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  const handleDelete = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    const ok = window.confirm('Delete this scanned note? This cannot be undone.');
    if (!ok) return;

    try {
      await axios.delete(`http://localhost:8002/api/notes/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      navigate('/dashboard?tab=notes');
    } catch (err) {
      console.error(err);
      alert('Failed to delete note.');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginBottom: '1rem' }}>
        <button className="btn" onClick={() => navigate('/dashboard?tab=notes')} style={{ paddingLeft: 0 }}>
          <ArrowLeft size={20} /> Back to Dashboard
        </button>
        <button className="btn" onClick={handleDelete} style={{ background: 'var(--error)', color: 'white', border: 'none' }}>
          Delete
        </button>
      </div>
      <NoteDetails noteId={id} />
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
            <Route path="/notes/:id" element={
              <ProtectedRoute>
                <NoteDetailsPage />
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
