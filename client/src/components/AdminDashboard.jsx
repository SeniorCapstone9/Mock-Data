import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, UserPlus, Shield, LogOut, TrendingUp, Tag, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, Legend } from 'recharts';
import { API_URL } from '../config';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const AdminDashboard = () => {
    const [users, setUsers] = useState([]);
    const [newUser, setNewUser] = useState({ username: '', password: '', role: 'doctor' });
    const [analyticsData, setAnalyticsData] = useState(null);
    const [records, setRecords] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        fetchUsers();
        fetchTrends();
        fetchRecords();
    }, []);

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

    const fetchTrends = async () => {
        try {
            const token = localStorage.getItem('token');
            // Admin can access the same analytics endpoint
            const response = await axios.get(`${API_URL}/api/analytics`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setAnalyticsData(response.data);
        } catch (err) {
            console.error(err);
        }
    };

    const fetchUsers = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get(`${API_URL}/api/users`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setUsers(response.data);
        } catch (err) {
            console.error(err);
        }
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        try {
            const token = localStorage.getItem('token');
            await axios.post(`${API_URL}/api/users`, newUser, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setNewUser({ username: '', password: '', role: 'doctor' });
            fetchUsers();
            alert('User created successfully');
        } catch (err) {
            alert('Error creating user');
        }
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
                    <Shield size={32} color="var(--primary)" />
                    <h2>Admin Dashboard</h2>
                </div>
                <button className="btn" onClick={handleLogout}><LogOut size={20} /></button>
            </div>

            <div className="grid" style={{ gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
                {/* Create User Form */}
                <div className="card">
                    <h3><UserPlus size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> Create User</h3>
                    <form onSubmit={handleCreateUser} style={{ marginTop: '1rem' }}>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem' }}>Username</label>
                            <input
                                type="text"
                                value={newUser.username}
                                onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)' }}
                                required
                            />
                        </div>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem' }}>Password</label>
                            <input
                                type="password"
                                value={newUser.password}
                                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)' }}
                                required
                            />
                        </div>
                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem' }}>Role</label>
                            <select
                                value={newUser.role}
                                onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)' }}
                            >
                                <option value="doctor">Doctor</option>
                                <option value="patient">Patient</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                        <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Create User</button>
                    </form>
                </div>

                {/* User List */}
                <div className="card">
                    <h3><Users size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> System Users</h3>
                    <table style={{ width: '100%', marginTop: '1rem', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                <th style={{ textAlign: 'left', padding: '0.5rem' }}>ID</th>
                                <th style={{ textAlign: 'left', padding: '0.5rem' }}>Username</th>
                                <th style={{ textAlign: 'left', padding: '0.5rem' }}>Role</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.id} style={{ borderBottom: '1px solid var(--border)' }}>
                                    <td style={{ padding: '0.5rem' }}>{u.id}</td>
                                    <td style={{ padding: '0.5rem' }}>{u.username}</td>
                                    <td style={{ padding: '0.5rem' }}>
                                        <span className={`status-badge status-${u.role === 'admin' ? 'completed' : 'processing'}`} style={{ textTransform: 'capitalize' }}>
                                            {u.role}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="card" style={{ marginTop: '2rem' }}>
                <h3><FileText size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> All Records (Redacted View)</h3>
                <table style={{ width: '100%', marginTop: '1rem', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                            <th style={{ textAlign: 'left', padding: '0.5rem' }}>ID</th>
                            <th style={{ textAlign: 'left', padding: '0.5rem' }}>Title</th>
                            <th style={{ textAlign: 'left', padding: '0.5rem' }}>Patient</th>
                            <th style={{ textAlign: 'left', padding: '0.5rem' }}>Date</th>
                            <th style={{ textAlign: 'left', padding: '0.5rem' }}>Status</th>
                            <th style={{ textAlign: 'left', padding: '0.5rem' }}>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {records.map(r => (
                            <tr key={r.id} style={{ borderBottom: '1px solid var(--border)' }}>
                                <td style={{ padding: '0.5rem' }}>{r.id}</td>
                                <td style={{ padding: '0.5rem' }}>{r.title}</td>
                                <td style={{ padding: '0.5rem' }}>{r.patient_name}</td>
                                <td style={{ padding: '0.5rem' }}>{new Date(r.created_at).toLocaleDateString()}</td>
                                <td style={{ padding: '0.5rem' }}>
                                    <span className={`status-badge status-${r.status}`}>
                                        {r.status}
                                    </span>
                                </td>
                                <td style={{ padding: '0.5rem' }}>
                                    <button
                                        className="btn btn-primary"
                                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
                                        onClick={() => navigate(`/results/${r.id}`)}
                                    >
                                        View
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="card" style={{ marginTop: '2rem' }}>
                <h3><TrendingUp size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> Daily Medical Trends (Last 7 Days)</h3>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>Evolution of top medical topics over time.</p>
                <div style={{ height: '300px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        {analyticsData && (
                            <AreaChart data={analyticsData.tags_over_time}>
                                <defs>
                                    {analyticsData.top_tags && analyticsData.top_tags.map((tag, index) => (
                                        <linearGradient key={`grad-${tag}`} id={`color-${tag}`} x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={COLORS[index % COLORS.length]} stopOpacity={0.8} />
                                            <stop offset="95%" stopColor={COLORS[index % COLORS.length]} stopOpacity={0} />
                                        </linearGradient>
                                    ))}
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                <XAxis dataKey="date" stroke="var(--text-muted)" />
                                <YAxis stroke="var(--text-muted)" />
                                <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)' }} />
                                <Legend />
                                {analyticsData.top_tags && analyticsData.top_tags.map((tag, index) => (
                                    <Area
                                        type="monotone"
                                        key={tag}
                                        dataKey={tag}
                                        stackId="1"
                                        stroke={COLORS[index % COLORS.length]}
                                        fill={`url(#color-${tag})`}
                                    />
                                ))}
                            </AreaChart>
                        )}
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
