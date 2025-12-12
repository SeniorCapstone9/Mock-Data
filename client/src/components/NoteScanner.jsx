import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import axios from 'axios';
import { Camera, Upload, RefreshCw, FileText, Loader2 } from 'lucide-react';
import { API_URL } from '../config';

const NoteScanner = ({ refreshNotes = null }) => {
    const [mode, setMode] = useState('camera'); // 'camera' or 'upload'
    const [image, setImage] = useState(null);
    const [imageFile, setImageFile] = useState(null);
    const [processing, setProcessing] = useState(false);

    const webcamRef = useRef(null);
    const navigate = useNavigate();

    const capture = useCallback(() => {
        const imageSrc = webcamRef.current.getScreenshot();
        setImage(imageSrc);
        // Convert base64 to file
        fetch(imageSrc)
            .then(res => res.blob())
            .then(blob => {
                const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
                setImageFile(file);
            });
    }, [webcamRef]);

    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            setImageFile(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                setImage(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const processImage = async () => {
        if (!imageFile) return;
        setProcessing(true);
        try {
            const formData = new FormData();
            formData.append('file', imageFile);

            const token = localStorage.getItem('token');
            const response = await axios.post(`${API_URL}/api/scan-note`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    Authorization: `Bearer ${token}`
                }
            });

            if (typeof refreshNotes === 'function') {
                await refreshNotes();
            }
            reset();
            navigate(`/notes/${response.data.id}`);
        } catch (err) {
            console.error(err);
            if (err.response && err.response.status === 401) {
                alert("Session expired. Please log in again.");
                navigate('/login');
            } else {
                alert("Failed to process image.");
            }
        } finally {
            setProcessing(false);
        }
    };

    const reset = () => {
        setImage(null);
        setImageFile(null);
    };

    return (
        <div className="card">
            <h3><Camera size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> Scan New Note</h3>

            <div style={{ margin: '1rem 0', display: 'flex', gap: '1rem' }}>
                <button
                    className={`btn ${mode === 'camera' ? 'btn-primary' : ''}`}
                    onClick={() => setMode('camera')}
                    style={{ flex: 1, backgroundColor: mode === 'camera' ? 'var(--primary)' : 'var(--bg-main)' }}
                >
                    Camera
                </button>
                <button
                    className={`btn ${mode === 'upload' ? 'btn-primary' : ''}`}
                    onClick={() => setMode('upload')}
                    style={{ flex: 1, backgroundColor: mode === 'upload' ? 'var(--primary)' : 'var(--bg-main)' }}
                >
                    Upload
                </button>
            </div>

            <div style={{ minHeight: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#000', borderRadius: '8px', overflow: 'hidden', position: 'relative' }}>

                {!image ? (
                    mode === 'camera' ? (
                        <>
                            <Webcam
                                audio={false}
                                ref={webcamRef}
                                screenshotFormat="image/jpeg"
                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            />
                            <button
                                onClick={capture}
                                className="btn btn-primary"
                                style={{ position: 'absolute', bottom: '20px', borderRadius: '50%', width: '60px', height: '60px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                            >
                                <Camera size={30} />
                            </button>
                        </>
                    ) : (
                        <div style={{ padding: '2rem', textAlign: 'center', color: 'white' }}>
                            <Upload size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                            <input
                                type="file"
                                accept="image/*,application/pdf"
                                onChange={handleFileUpload}
                                style={{ display: 'block', margin: '0 auto' }}
                            />
                        </div>
                    )
                ) : (
                    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                        {image && imageFile && imageFile.type === 'application/pdf' ? (
                            <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', flexDirection: 'column' }}>
                                <FileText size={48} />
                                <p>{imageFile.name}</p>
                            </div>
                        ) : (
                            <img src={image} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                        )}

                        <button
                            onClick={reset}
                            className="btn"
                            style={{ position: 'absolute', top: '10px', right: '10px', background: 'rgba(0,0,0,0.5)', color: 'white' }}
                        >
                            <RefreshCw size={20} /> Retake
                        </button>
                    </div>
                )}
            </div>

            {image && (
                <div style={{ marginTop: '1rem' }}>
                    <button
                        className="btn btn-primary"
                        style={{ width: '100%', padding: '1rem' }}
                        onClick={processImage}
                        disabled={processing}
                    >
                        {processing ? <><Loader2 className="animate-spin" /> Processing Document...</> : 'Extract Text with AI'}
                    </button>
                    <p style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                        Note: Processing may take 5-10 seconds.
                    </p>
                </div>
            )}
        </div>
    );
};

export default NoteScanner;
