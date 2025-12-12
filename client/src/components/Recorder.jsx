import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Upload, Loader2 } from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../config';

const Recorder = ({ onUploadStart, onUploadSuccess, onUploadError }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [mediaRecorder, setMediaRecorder] = useState(null); // Changed from useRef to useState
    const [patients, setPatients] = useState([]);
    const [selectedPatient, setSelectedPatient] = useState('');
    const chunksRef = useRef([]);
    const timerRef = useRef(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        // Fetch patients for dropdown
        const fetchPatients = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await axios.get(`${API_URL}/api/patients`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setPatients(response.data);
            } catch (err) {
                console.error("Failed to fetch patients", err);
            }
        };
        fetchPatients();
    }, []);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const newMediaRecorder = new MediaRecorder(stream);
            setMediaRecorder(newMediaRecorder); // Set the new MediaRecorder instance
            chunksRef.current = [];

            newMediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                }
            };

            newMediaRecorder.onstop = async () => {
                const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                await uploadAudio(blob);

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            newMediaRecorder.start();
            setIsRecording(true);

            // Start timer
            setRecordingTime(0);
            timerRef.current = setInterval(() => {
                setRecordingTime(prev => prev + 1);
            }, 1000);

        } catch (err) {
            console.error("Error accessing microphone:", err);
            alert("Could not access microphone. Please check permissions.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            setIsRecording(false);
            clearInterval(timerRef.current);
        }
    };

    const uploadAudio = async (fileOrBlob, filename) => {
        if (isUploading) return;
        setIsUploading(true);
        onUploadStart && onUploadStart();

        const formData = new FormData();
        formData.append('file', fileOrBlob, filename || 'recording.webm');
        if (selectedPatient) {
            formData.append('patient_id', selectedPatient);
        }

        try {
            const token = localStorage.getItem('token');
            const response = await axios.post(`${API_URL}/api/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    Authorization: token ? `Bearer ${token}` : undefined,
                },
            });
            onUploadSuccess && onUploadSuccess(response.data.id);
        } catch (error) {
            console.error("Upload error:", error);
            onUploadError && onUploadError(error);
        } finally {
            setIsUploading(false);
        }
    };

    const handlePickFile = () => {
        if (isUploading || isRecording) return;
        fileInputRef.current?.click();
    };

    const handleFileSelected = async (e) => {
        const file = e.target.files?.[0];
        // Reset input so selecting the same file again triggers onChange
        e.target.value = '';
        if (!file) return;

        await uploadAudio(file, file.name);
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Medical Scribe Recorder</h2>
                <p style={{ color: 'var(--text-muted)' }}>Click to start recording your session</p>
            </div>

            <div style={{
                fontSize: '3rem',
                fontWeight: '800',
                fontVariantNumeric: 'tabular-nums',
                marginBottom: '2rem',
                color: isRecording ? 'var(--error)' : 'var(--text-main)'
            }}>
                {formatTime(recordingTime)}
            </div>

            {!isRecording ? (
                <div style={{ width: '100%', maxWidth: '300px', margin: '0 auto' }}>
                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem' }}>Select Patient</label>
                        <select
                            value={selectedPatient}
                            onChange={(e) => setSelectedPatient(e.target.value)}
                            style={{ width: '100%', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}
                        >
                            <option value="">-- Select Patient --</option>
                            {patients.map(p => (
                                <option key={p.id} value={p.id}>{p.username}</option>
                            ))}
                        </select>
                    </div>
                    <button
                        className="btn btn-primary"
                        onClick={startRecording}
                        disabled={isUploading}
                        style={{ width: '100%', fontSize: '1.2rem', padding: '1rem 2rem', borderRadius: '50px' }}
                    >
                        {isUploading ? <Loader2 className="animate-spin" size={24} /> : <Mic size={24} />} Start Recording
                    </button>

                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="audio/*,video/*"
                        onChange={handleFileSelected}
                        style={{ display: 'none' }}
                    />

                    <button
                        className="btn"
                        onClick={handlePickFile}
                        disabled={isUploading}
                        style={{ width: '100%', marginTop: '0.75rem', fontSize: '1.05rem', padding: '0.9rem 2rem', borderRadius: '50px', border: '1px solid var(--border)' }}
                    >
                        {isUploading ? <Loader2 className="animate-spin" size={22} /> : <Upload size={22} />} Upload Audio File
                    </button>
                </div>
            ) : (
                <button className="btn btn-danger" onClick={stopRecording} style={{ fontSize: '1.2rem', padding: '1rem 2rem', borderRadius: '50px' }}>
                    <Square size={24} fill="currentColor" /> Stop Recording
                </button>
            )}

            {isRecording && (
                <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', color: 'var(--error)' }}>
                    <div className="animate-pulse" style={{ width: 10, height: 10, background: 'currentColor', borderRadius: '50%' }}></div>
                    Recording in progress...
                </div>
            )}
        </div>
    );
};

export default Recorder;
