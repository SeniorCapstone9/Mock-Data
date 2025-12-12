import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Calendar, FileText, LogOut, User, CheckSquare } from 'lucide-react';
import { API_URL } from '../config';

const PatientPortal = () => {
    const [records, setRecords] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchRecords = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await axios.get(`${API_URL}/api/records`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setRecords(response.data);
            } catch (err) {
                console.error(err);
            }
        };
        fetchRecords();
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        navigate('/login');
    };

    return (
        <div>
            <div className="header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <User size={32} color="var(--primary)" />
                    <h2>My Health Portal</h2>
                </div>
                <button className="btn" onClick={handleLogout}><LogOut size={20} /></button>
            </div>

            <div className="grid">
                {records.map((record) => (
                    <div key={record.id} className="card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
                                <Calendar size={16} />
                                {new Date(record.created_at).toLocaleDateString()}
                            </div>
                            <span className={`status-badge status-${record.status}`}>{record.status}</span>
                        </div>
                        <h3 style={{ marginBottom: '0.5rem' }}>{record.title || "Untitled Visit"}</h3>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                            Duration: {record.duration ? `${Math.round(record.duration)}s` : '-'}
                        </p>

                        {record.soap_summary && (
                            <div style={{ background: 'var(--surface)', padding: '1rem', borderRadius: '8px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: '500' }}>
                                    <FileText size={16} /> Summary
                                </div>
                                <p style={{ fontSize: '0.9rem', lineHeight: '1.5' }}>
                                    {record.soap_summary.substring(0, 150)}...
                                </p>
                            </div>
                        )}

                        {record.action_items && record.action_items.length > 0 && (
                            <div style={{ background: '#ecfdf5', padding: '1rem', borderRadius: '8px', marginTop: '1rem', border: '1px solid #a7f3d0' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: '500', color: '#047857' }}>
                                    <CheckSquare size={16} /> Doctor's Orders
                                </div>
                                <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#065f46' }}>
                                    {record.action_items.map((item, idx) => (
                                        <li key={idx} style={{ marginBottom: '0.25rem' }}>{item}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        <button
                            className="btn"
                            style={{ marginTop: '1rem', width: '100%', border: '1px solid var(--border)' }}
                            onClick={() => navigate(`/session/${record.id}`)}
                        >
                            View Full Details
                        </button>
                    </div>
                ))}
                {records.length === 0 && (
                    <div className="card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem' }}>
                        <p>No medical records found.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PatientPortal;
