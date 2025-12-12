import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { Activity, Clock, FileText, CheckCircle, TrendingUp, Heart, Tag, ArrowLeft } from 'lucide-react';
import { API_URL } from '../config';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const KPICard = ({ title, value, icon: Icon, color }) => (
    <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ padding: '1rem', borderRadius: '50%', background: `${color}20`, color: color }}>
            <Icon size={24} />
        </div>
        <div>
            <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.875rem' }}>{title}</p>
            <h3 style={{ margin: 0, fontSize: '1.5rem' }}>{value}</h3>
        </div>
    </div>
);

const Analytics = () => {
    const [data, setData] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) {
                    navigate('/login');
                    return;
                }
                const response = await axios.get(`${API_URL}/api/analytics`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setData(response.data);
            } catch (err) {
                console.error(err);
            }
        };
        fetchAnalytics();
    }, [navigate]);

    if (!data) return <div className="container">Loading...</div>;

    return (
        <div>
            <div className="header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button className="btn" onClick={() => navigate('/dashboard')} style={{ paddingLeft: 0 }}>
                        <ArrowLeft size={20} />
                    </button>
                    <h2>Analytics Dashboard</h2>
                </div>
            </div>

            <div className="grid" style={{ marginBottom: '2rem' }}>
                <KPICard title="Total Sessions" value={data.total_sessions} icon={FileText} color="#2563eb" />
                <KPICard title="Total Duration (mins)" value={data.total_duration} icon={Clock} color="#10b981" />
                <KPICard title="Avg. Confidence" value={`${data.avg_confidence}%`} icon={CheckCircle} color="#f59e0b" />
                <KPICard title="Total Words" value={data.total_words.toLocaleString()} icon={Activity} color="#8b5cf6" />
            </div>

            <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                <div className="card">
                    <h3><TrendingUp size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> Activity Trend</h3>
                    <div style={{ height: '300px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data.activity}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                <XAxis dataKey="date" stroke="var(--text-muted)" />
                                <YAxis stroke="var(--text-muted)" />
                                <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)' }} />
                                <Line type="monotone" dataKey="count" stroke="var(--primary)" strokeWidth={2} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="card">
                    <h3><Heart size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> Patient Sentiment</h3>
                    <div style={{ height: '300px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={data.sentiment}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {data.sentiment && data.sentiment.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)' }} />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="card" style={{ gridColumn: '1 / -1' }}>
                    <h3><Tag size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> Daily Medical Trends (Last 7 Days)</h3>
                    <div style={{ height: '300px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={data.tags_over_time}>
                                <defs>
                                    {data.top_tags && data.top_tags.map((tag, index) => (
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
                                {data.top_tags && data.top_tags.map((tag, index) => (
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
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Analytics;
