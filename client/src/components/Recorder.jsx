import React, { useState, useRef } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import axios from 'axios';

const Recorder = ({ onUploadStart, onUploadSuccess, onUploadError }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const timerRef = useRef(null);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream);
            chunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                }
            };

            mediaRecorderRef.current.onstop = async () => {
                const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                await uploadAudio(blob);

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorderRef.current.start();
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
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            clearInterval(timerRef.current);
        }
    };

    const uploadAudio = async (blob) => {
        onUploadStart();
        const formData = new FormData();
        formData.append('file', blob, 'recording.webm');

        try {
            const response = await axios.post('http://localhost:8002/api/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            onUploadSuccess(response.data.id);
        } catch (error) {
            console.error("Upload error:", error);
            onUploadError(error);
        }
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
                <button className="btn btn-primary" onClick={startRecording} style={{ fontSize: '1.2rem', padding: '1rem 2rem', borderRadius: '50px' }}>
                    <Mic size={24} /> Start Recording
                </button>
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
