import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, Calendar, FileAudio, ChevronRight, LogOut, BarChart2 } from 'lucide-react';

const Dashboard = () => {
    const [records, setRecords] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchRecords = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) {
                    navigate('/login');
                    return;
                }
                const response = await axios.get('http://localhost:8002/api/records', {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setRecords(response.data);
            } catch (err) {
                navigate('/login');
            }
        };
        fetchRecords();
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <div>
            <div className="header">
                <h2>Session History</h2>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }} onClick={() => navigate('/analytics')}>
                        <BarChart2 size={20} /> Analytics
                    </button>
                    <button className="btn btn-primary" onClick={() => navigate('/record')}>
                        <Plus size={20} /> New Session
                    </button>
                    <button className="btn" style={{ background: 'var(--secondary)', color: 'white' }} onClick={handleLogout}>
                        <LogOut size={20} />
                    </button>
                </div>
            </div>

            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
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
                                <td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                    No sessions found. Start a new recording.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Dashboard;
