import React, { useState } from 'react';
import { Stethoscope } from 'lucide-react';
import Recorder from './components/Recorder';
import Results from './components/Results';

function App() {
  const [currentRecordId, setCurrentRecordId] = useState(null);
  const [viewState, setViewState] = useState('idle'); // idle, uploading, processing, results

  const handleUploadStart = () => {
    setViewState('uploading');
  };

  const handleUploadSuccess = (id) => {
    setCurrentRecordId(id);
    setViewState('processing');
  };

  const handleUploadError = () => {
    setViewState('idle');
    alert("Upload failed");
  };

  return (
    <div className="container">
      <header className="header">
        <div className="logo">
          <Stethoscope size={32} />
          <span>MediScribe AI</span>
        </div>
        <div>
          {/* User profile or settings could go here */}
        </div>
      </header>

      <main>
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

        {(viewState === 'processing' || viewState === 'results') && (
          <>
            <Results recordId={currentRecordId} />
            <div style={{ textAlign: 'center', marginTop: '2rem' }}>
              <button className="btn btn-primary" onClick={() => {
                setViewState('idle');
                setCurrentRecordId(null);
              }}>
                Start New Session
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
