import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Calendar, FileAudio, ChevronRight, LogOut, BarChart2, Activity, Mic, FileText, ExternalLink } from 'lucide-react';
import Recorder from './Recorder';
import NoteScanner from './NoteScanner';

const Dashboard = () => {
    const [user, setUser] = useState({ username: '', role: '' });
    const [records, setRecords] = useState([]);
    const [stats, setStats] = useState({ total_sessions: 0, total_duration: 0 });
    const [notes, setNotes] = useState([]);
    const [noteStats, setNoteStats] = useState({ total_scans: 0, last_scan_at: null });
    const [activeTab, setActiveTab] = useState('record'); // 'record', 'notes', 'list'
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const tab = params.get('tab');
        if (tab === 'notes') setActiveTab('notes');
        if (tab === 'record') setActiveTab('record');
    }, [location.search]);

    useEffect(() => {
        // Decode token for user info
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                setUser({ username: payload.sub, role: payload.role });
            } catch (e) {
                console.error("Invalid token", e);
            }
        } else {
            navigate('/login');
        }

        fetchRecords();
    }, [navigate]);

    useEffect(() => {
        if (activeTab === 'notes') {
            fetchNotes();
        }
    }, [activeTab]);

    const fetchRecords = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) return;
            const response = await axios.get('http://localhost:8002/api/records', {
                headers: { Authorization: `Bearer ${token}` }
            });
            setRecords(response.data);

            // Calc stats
            const total_duration = response.data.reduce((acc, curr) => acc + curr.duration, 0);
            setStats({
                total_sessions: response.data.length,
                total_duration: Math.round(total_duration / 60)
            });
        } catch (err) {
            console.error(err);
        }
    };

    const fetchNotes = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) return;
            const response = await axios.get('http://localhost:8002/api/notes', {
                headers: { Authorization: `Bearer ${token}` }
            });

            const fetchedNotes = response.data || [];
            setNotes(fetchedNotes);
            setNoteStats({
                total_scans: fetchedNotes.length,
                last_scan_at: fetchedNotes.length > 0 ? fetchedNotes[0].created_at : null
            });

        } catch (err) {
            console.error(err);
        }
    };

    const getNoteFileUrl = (note) => {
        const rawPath = note?.image_path;
        if (!rawPath) return null;
        const parts = rawPath.split(/[/\\]+/);
        const filename = parts[parts.length - 1];
        if (!filename) return null;
        return `http://localhost:8002/temp/${filename}`;
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        navigate('/login');
    };

    return (
        <div>
            <div className="header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Activity size={32} color="var(--primary)" />
                    <h2>Doctor Dashboard</h2>
                </div>

                {/* Tabs */}
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button
                        className={`btn ${activeTab === 'record' ? 'btn-primary' : ''}`}
                        onClick={() => setActiveTab('record')}
                        style={{ border: activeTab !== 'record' ? '1px solid var(--border)' : 'none' }}
                    >
                        <Mic size={16} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} /> Audio Session
                    </button>
                    <button
                        className={`btn ${activeTab === 'notes' ? 'btn-primary' : ''}`}
                        onClick={() => setActiveTab('notes')}
                        style={{ border: activeTab !== 'notes' ? '1px solid var(--border)' : 'none' }}
                    >
                        <FileText size={16} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} /> Scan Notes
                    </button>
                </div>

                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }} onClick={() => navigate('/analytics')}>
                        <BarChart2 size={20} />
                    </button>
                    <button className="btn" style={{ background: 'var(--secondary)', color: 'white' }} onClick={handleLogout}>
                        <LogOut size={20} />
                    </button>
                </div>
            </div>

            {/* Tab: Audio Recorder */}
            {activeTab === 'record' && (
                <div className="animate-fade-in" style={{ marginBottom: '2rem' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
                        <div className="card">
                            <h3 style={{ marginBottom: '1rem' }}>Welcome, Dr. {user.username || 'User'}</h3>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                <div style={{ background: 'var(--bg-main)', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{stats.total_sessions}</div>
                                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Sessions</div>
                                </div>
                                <div style={{ background: 'var(--bg-main)', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{stats.total_duration}m</div>
                                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Recorded</div>
                                </div>
                            </div>
                        </div>
                        <Recorder
                            onUploadStart={() => { }}
                            onUploadSuccess={(id) => { fetchRecords(); alert("Session Processed!"); }}
                            onUploadError={(e) => alert("Error uploading: " + e)}
                        />
                    </div>
                </div>
            )}

            {/* Tab: Note Scanner */}
            {activeTab === 'notes' && (
                <div className="animate-fade-in" style={{ marginBottom: '2rem' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
                        <div className="card">
                            <h3 style={{ marginBottom: '1rem' }}>Scanned Notes</h3>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                <div style={{ background: 'var(--bg-main)', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{noteStats.total_scans}</div>
                                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Scans</div>
                                </div>
                                <div style={{ background: 'var(--bg-main)', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                                        {noteStats.last_scan_at ? new Date(noteStats.last_scan_at).toLocaleDateString() : '-'}
                                    </div>
                                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Last Scan</div>
                                </div>
                            </div>
                            <div style={{ marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.4 }}>
                                Click a row in the table below to open its OCR text.
                            </div>
                        </div>
                        <NoteScanner
                            refreshNotes={fetchNotes}
                        />
                    </div>
                </div>
            )}

            {activeTab === 'record' && (
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)' }}>
                        <h3>Recent Audio Sessions</h3>
                    </div>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead style={{ background: 'var(--background)', borderBottom: '1px solid var(--border)' }}>
                            <tr>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Date</th>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Patient</th>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Title</th>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Duration</th>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Status</th>
                                <th style={{ padding: '1rem', textAlign: 'right' }}>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {records.map((record) => (
                                <tr
                                    key={record.id}
                                    style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
                                    onClick={() => navigate(`/session/${record.id}`)}
                                >
                                    <td style={{ padding: '1rem' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <Calendar size={16} color="var(--text-muted)" />
                                            {new Date(record.created_at).toLocaleDateString()}
                                        </div>
                                    </td>
                                    <td style={{ padding: '1rem' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem' }}>
                                                {record.patient_name ? record.patient_name[0].toUpperCase() : '?'}
                                            </div>
                                            {record.patient_name}
                                        </div>
                                    </td>
                                    <td style={{ padding: '1rem' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '500' }}>
                                            <FileAudio size={16} color="var(--primary)" />
                                            {record.title}
                                        </div>
                                    </td>
                                    <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>
                                        {record.duration ? `${Math.round(record.duration)}s` : '-'}
                                    </td>
                                    <td style={{ padding: '1rem' }}>
                                        <span className={`status-badge status-${record.status}`}>
                                            {record.status}
                                        </span>
                                    </td>
                                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                                        <ChevronRight size={20} color="var(--text-muted)" />
                                    </td>
                                </tr>
                            ))}
                            {records.length === 0 && (
                                <tr>
                                    <td colSpan="6" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                        No sessions found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {activeTab === 'notes' && (
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)' }}>
                        <h3>Recent Scanned Notes</h3>
                    </div>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead style={{ background: 'var(--background)', borderBottom: '1px solid var(--border)' }}>
                            <tr>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Date</th>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Document</th>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Preview</th>
                                <th style={{ padding: '1rem', textAlign: 'right' }}>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {notes.map((note) => {
                                const url = getNoteFileUrl(note);
                                return (
                                    <tr
                                        key={note.id}
                                        style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
                                        onClick={() => navigate(`/notes/${note.id}`)}
                                    >
                                        <td style={{ padding: '1rem' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <Calendar size={16} color="var(--text-muted)" />
                                                {new Date(note.created_at).toLocaleDateString()}
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '500' }}>
                                                <FileText size={16} color="var(--primary)" />
                                                Note #{note.id}
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem', color: 'var(--text-muted)', maxWidth: '520px' }}>
                                            <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {note.extracted_text || '-'}
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem', textAlign: 'right' }}>
                                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', alignItems: 'center' }}>
                                                {url && (
                                                    <a
                                                        href={url}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        onClick={(e) => e.stopPropagation()}
                                                        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-muted)' }}
                                                        title="Open uploaded file"
                                                    >
                                                        <ExternalLink size={16} />
                                                    </a>
                                                )}
                                                <ChevronRight size={20} color="var(--text-muted)" />
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                            {notes.length === 0 && (
                                <tr>
                                    <td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                        No scanned notes found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
