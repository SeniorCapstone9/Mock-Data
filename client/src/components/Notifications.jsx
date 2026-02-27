import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Bell, AlertTriangle, AlertCircle, Info, Send } from 'lucide-react';
import { API_URL } from '../config';

const severityMeta = {
    info: { color: '#2563eb', icon: Info },
    warning: { color: '#d97706', icon: AlertTriangle },
    critical: { color: '#dc2626', icon: AlertCircle }
};

const Notifications = () => {
    const navigate = useNavigate();
    
    // Core Data State
    const [feed, setFeed] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [selectedDetail, setSelectedDetail] = useState(null);
    const [distribution, setDistribution] = useState(null);
    const [deliveryLog, setDeliveryLog] = useState([]);
    
    // Filter State
    const [severityFilter, setSeverityFilter] = useState('');
    const [locationFilter, setLocationFilter] = useState('');
    const [symptomFilter, setSymptomFilter] = useState('');
    
    // UI State
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState('');
    const [emailRecipients, setEmailRecipients] = useState('');
    const [includeEmail, setIncludeEmail] = useState(true);

    const authHeaders = useMemo(() => {
        const token = localStorage.getItem('token');
        return token ? { Authorization: `Bearer ${token}` } : {};
    }, []);

    // Fetches the alerts from the DB
    const loadFeed = async () => {
        try {
            const params = { limit: 200 };
            if (severityFilter) params.severity = severityFilter;
            if (locationFilter) params.location = locationFilter.toUpperCase();
            if (symptomFilter) params.symptom = symptomFilter;

            const response = await axios.get(`${API_URL}/api/notifications`, {
                params,
                headers: authHeaders
            });
            setFeed(response.data || []);
            setMessage(''); // Clear any previous errors on success
        } catch (err) {
            console.error(err);
            setMessage('Failed to load notifications from database.');
        }
    };

    const loadDetail = async (id) => {
        try {
            const [detailResp, distResp, deliveryResp] = await Promise.all([
                axios.get(`${API_URL}/api/notifications/${id}`, { headers: authHeaders }),
                axios.get(`${API_URL}/api/notifications/${id}/distribution`, { headers: authHeaders }),
                axios.get(`${API_URL}/api/notifications/${id}/deliveries`, { headers: authHeaders })
            ]);
            setSelectedDetail(detailResp.data);
            setDistribution(distResp.data);
            setDeliveryLog(deliveryResp.data || []);
        } catch (err) {
            console.error(err);
            setMessage('Failed to load notification details.');
        }
    };

    // Auth and Initial Load
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) { navigate('/login'); return; }
        loadFeed();
    }, [navigate]);

    // Live filtering
    useEffect(() => {
        loadFeed();
    }, [severityFilter, locationFilter, symptomFilter]);

    useEffect(() => {
        if (selectedId) loadDetail(selectedId);
    }, [selectedId]);

    const handleSendNotification = async () => {
        if (!selectedId) return;
        setBusy(true);
        setMessage('');
        try {
            const emails = emailRecipients.split(',').map((v) => v.trim()).filter(Boolean);
            const response = await axios.post(
                `${API_URL}/api/notifications/${selectedId}/send`,
                { emails, include_email: includeEmail },
                { headers: authHeaders }
            );
            setMessage(`Delivery attempt: ${response.data.sent} sent.`);
            loadDetail(selectedId); // Refresh history
        } catch (err) {
            setMessage('Failed to send notification.');
        } finally {
            setBusy(false);
        }
    };

    // --- DATA SPLITTING LOGIC ---
    const respiratoryAlerts = feed.filter(
        (item) => !item.message.includes("CHRONIC ALERT")
    );
    
    const chronicAlerts = feed.filter(
        (item) => item.message.includes("CHRONIC ALERT")
    );

    return (
        <div className="notifications-container">
            <div className="header" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button className="btn" onClick={() => navigate('/dashboard')} style={{ paddingLeft: 0 }}>
                        <ArrowLeft size={20} />
                    </button>
                    <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <Bell size={28} color="var(--primary)" /> Population Health Alerts
                    </h2>
                </div>
                {message && <div className="status-message" style={{ color: 'var(--primary)', fontWeight: 500 }}>{message}</div>}
            </div>

            {/* Live Filter Bar */}
            <div className="card" style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ marginTop: 0, fontSize: '1rem' }}>Filter Alerts</h3>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} style={{ padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border)', flex: 1 }}>
                        <option value="">All Severities</option>
                        <option value="critical">Critical</option>
                        <option value="warning">Warning</option>
                        <option value="info">Info</option>
                    </select>
                    <input
                        value={locationFilter}
                        onChange={(e) => setLocationFilter(e.target.value.toUpperCase())}
                        placeholder="Location (e.g. FL)"
                        maxLength={2}
                        style={{ width: '150px', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border)' }}
                    />
                    <input
                        value={symptomFilter}
                        onChange={(e) => setSymptomFilter(e.target.value)}
                        placeholder="Search Symptom..."
                        style={{ flex: 2, padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border)' }}
                    />
                </div>
            </div>

            <div className="grid" style={{ gridTemplateColumns: '1.3fr 1fr', gap: '1.5rem' }}>
                
                {/* --- LEFT COLUMN: STACKED TABLES --- */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '70vh' }}>                    
                    {/* TABLE 1: Respiratory History */}
                    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                        <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)', background: '#f8fafc' }}>
                            <h3 style={{ margin: 0 }}>Respiratory History</h3>
                        </div>
                        <div style={{ maxHeight: '32vh', overflowY: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead style={{ position: 'sticky', top: 0, background: 'white', zIndex: 1, borderBottom: '2px solid var(--border)' }}>
                                    <tr>
                                        <th style={{ textAlign: 'left', padding: '1rem' }}>Severity</th>
                                        <th style={{ textAlign: 'left', padding: '1rem' }}>Date</th>
                                        <th style={{ textAlign: 'left', padding: '1rem' }}>Loc</th>
                                        <th style={{ textAlign: 'left', padding: '1rem' }}>Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {respiratoryAlerts.map((item) => {
                                        const meta = severityMeta[item.severity] || severityMeta.info;
                                        const Icon = meta.icon;
                                        return (
                                            <tr
                                                key={item.id}
                                                onClick={() => setSelectedId(item.id)}
                                                style={{
                                                    cursor: 'pointer',
                                                    borderBottom: '1px solid var(--border)',
                                                    background: selectedId === item.id ? '#eff6ff' : 'transparent'
                                                }}
                                            >
                                                <td style={{ padding: '1rem', color: meta.color, fontWeight: 700 }}>
                                                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                                                        <Icon size={16} /> {item.severity.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td style={{ padding: '1rem' }}>{new Date(item.group_date).toLocaleDateString()}</td>
                                                <td style={{ padding: '1rem' }}>{item.location}</td>
                                                <td style={{ padding: '1rem', fontSize: '0.9rem' }}>{item.message}</td>
                                            </tr>
                                        );
                                    })}
                                    {respiratoryAlerts.length === 0 && (
                                        <tr><td colSpan="4" style={{ padding: '1rem', textAlign: 'center', color: 'gray' }}>No acute alerts found.</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* TABLE 2: Chronic History */}
                    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                        <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)', background: '#f8fafc' }}>
                            <h3 style={{ margin: 0 }}>Chronic History</h3>
                        </div>
                        <div style={{ maxHeight: '32vh', overflowY: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead style={{ position: 'sticky', top: 0, background: 'white', zIndex: 1, borderBottom: '2px solid var(--border)' }}>
                                    <tr>
                                        <th style={{ textAlign: 'left', padding: '1rem' }}>Severity</th>
                                        <th style={{ textAlign: 'left', padding: '1rem' }}>Date</th>
                                        <th style={{ textAlign: 'left', padding: '1rem' }}>Loc</th>
                                        <th style={{ textAlign: 'left', padding: '1rem' }}>Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {chronicAlerts.map((item) => {
                                        const meta = severityMeta[item.severity] || severityMeta.info;
                                        const Icon = meta.icon;
                                        return (
                                            <tr
                                                key={item.id}
                                                onClick={() => setSelectedId(item.id)}
                                                style={{
                                                    cursor: 'pointer',
                                                    borderBottom: '1px solid var(--border)',
                                                    background: selectedId === item.id ? '#eff6ff' : 'transparent'
                                                }}
                                            >
                                                <td style={{ padding: '1rem', color: meta.color, fontWeight: 700 }}>
                                                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                                                        <Icon size={16} /> {item.severity.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td style={{ padding: '1rem' }}>{new Date(item.group_date).toLocaleDateString()}</td>
                                                <td style={{ padding: '1rem' }}>{item.location}</td>
                                                <td style={{ padding: '1rem', fontSize: '0.9rem' }}>{item.message}</td>
                                            </tr>
                                        );
                                    })}
                                    {chronicAlerts.length === 0 && (
                                        <tr><td colSpan="4" style={{ padding: '1rem', textAlign: 'center', color: 'gray' }}>No chronic alerts found.</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* --- RIGHT COLUMN: DETAIL PANE --- */}
                <div className="card detail-pane">
                    <h3>Alert Insight</h3>
                    {!selectedDetail ? (
                        <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
                            <Bell size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                            <p>Select an alert from the feed to investigate details.</p>
                        </div>
                    ) : (
                        <div className="detail-content animate-fade-in">
                            <div className="severity-badge" style={{ background: severityMeta[selectedDetail.severity].color, color: 'white', padding: '0.25rem 0.75rem', borderRadius: '20px', display: 'inline-block', fontSize: '0.8rem', fontWeight: 700, marginBottom: '1rem' }}>
                                {selectedDetail.severity.toUpperCase()}
                            </div>
                            
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                                <div><small>DATE</small><div>{new Date(selectedDetail.group_date).toLocaleDateString()}</div></div>
                                <div><small>LOCATION</small><div>{selectedDetail.location}</div></div>
                                <div><small>PREVALENCE</small><div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{(selectedDetail.rate * 100).toFixed(1)}%</div></div>
                                <div><small>TOTAL VISITS</small><div>{selectedDetail.total_visits}</div></div>
                            </div>

                            <h4 style={{ borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>Symptom Distribution</h4>
                            <div style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '1.5rem' }}>
                                <table style={{ width: '100%', fontSize: '0.9rem' }}>
                                <tbody>
                                {Object.entries(distribution?.distribution || {}).map(([symptom, rate]) => (
                                <tr key={symptom}>
                                 <td style={{ padding: '0.4rem 0', textTransform: 'capitalize' }}>{symptom}</td>
                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{(rate * 100).toFixed(1)}%</td>
                                    </tr>
                                        ))}
                                </tbody>
                                </table>
                            </div>

                            <h4 style={{ marginBottom: '1rem' }}>Clinical Actions</h4>
                            <div className="action-box" style={{ background: '#f1f5f9', padding: '1rem', borderRadius: '12px' }}>
                                <input
                                    type="text"
                                    value={emailRecipients}
                                    onChange={(e) => setEmailRecipients(e.target.value)}
                                    placeholder="Enter Physician Emails..."
                                    style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #cbd5e1', marginBottom: '0.75rem' }}
                                />
                                <button className="btn btn-primary" onClick={handleSendNotification} disabled={busy} style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                                    <Send size={18} /> {busy ? 'Processing...' : 'Dispatch Alert'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Notifications;