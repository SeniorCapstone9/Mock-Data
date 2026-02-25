import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Upload, Play, Bell, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { API_URL } from '../config';

const severityMeta = {
    info: { color: '#2563eb', icon: Info },
    warning: { color: '#d97706', icon: AlertTriangle },
    critical: { color: '#dc2626', icon: AlertCircle }
};

const Notifications = () => {
    const navigate = useNavigate();
    const [jsonInput, setJsonInput] = useState('');
    const [csvFile, setCsvFile] = useState(null);
    const [runDays, setRunDays] = useState(7);
    const [runSymptoms, setRunSymptoms] = useState('');
    const [severityFilter, setSeverityFilter] = useState('');
    const [locationFilter, setLocationFilter] = useState('');
    const [symptomFilter, setSymptomFilter] = useState('');
    const [feed, setFeed] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [selectedDetail, setSelectedDetail] = useState(null);
    const [distribution, setDistribution] = useState(null);
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState('');
    const [emailRecipients, setEmailRecipients] = useState('');
    const [includeEmail, setIncludeEmail] = useState(true);
    const [deliveryLog, setDeliveryLog] = useState([]);

    const authHeaders = useMemo(() => {
        const token = localStorage.getItem('token');
        return token ? { Authorization: `Bearer ${token}` } : {};
    }, []);

    const loadFeed = async () => {
        try {
            const params = { days: 7, limit: 200 };
            if (severityFilter) params.severity = severityFilter;
            if (locationFilter) params.location = locationFilter.toUpperCase();
            if (symptomFilter) params.symptom = symptomFilter;

            const response = await axios.get(`${API_URL}/api/notifications`, {
                params,
                headers: authHeaders
            });
            setFeed(response.data || []);

            if ((response.data || []).length === 0) {
                setSelectedId(null);
                setSelectedDetail(null);
                setDistribution(null);
            }
        } catch (err) {
            console.error(err);
            setMessage('Failed to load notifications.');
        }
    };

    const loadDetail = async (id) => {
        try {
            const [detailResp, distResp] = await Promise.all([
                axios.get(`${API_URL}/api/notifications/${id}`, { headers: authHeaders }),
                axios.get(`${API_URL}/api/notifications/${id}/distribution`, { headers: authHeaders })
            ]);
            setSelectedDetail(detailResp.data);
            setDistribution(distResp.data);
            const deliveryResp = await axios.get(`${API_URL}/api/notifications/${id}/deliveries`, { headers: authHeaders });
            setDeliveryLog(deliveryResp.data || []);
        } catch (err) {
            console.error(err);
            setMessage('Failed to load notification details.');
        }
    };

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
            return;
        }
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.role === 'patient') {
                navigate('/portal');
                return;
            }
        } catch (err) {
            console.error(err);
            navigate('/login');
            return;
        }
        loadFeed();
    }, [navigate]);

    useEffect(() => {
        loadFeed();
    }, [severityFilter, locationFilter, symptomFilter]);

    useEffect(() => {
        if (selectedId) {
            loadDetail(selectedId);
        }
    }, [selectedId]);

    const handleImportJson = async () => {
        setBusy(true);
        setMessage('');
        try {
            const parsed = JSON.parse(jsonInput || '{}');
            const visits = Array.isArray(parsed) ? parsed : parsed.visits;
            if (!Array.isArray(visits) || visits.length === 0) {
                throw new Error('JSON must be an array or an object with a visits array.');
            }

            const response = await axios.post(
                `${API_URL}/api/notification-visits/import`,
                { visits, source: 'temp' },
                { headers: authHeaders }
            );
            setMessage(`Imported ${response.data.inserted} visit records.`);
        } catch (err) {
            console.error(err);
            setMessage(err.response?.data?.detail || err.message || 'JSON import failed.');
        } finally {
            setBusy(false);
        }
    };

    const handleImportCsv = async () => {
        if (!csvFile) {
            setMessage('Choose a CSV file first.');
            return;
        }
        setBusy(true);
        setMessage('');
        try {
            const formData = new FormData();
            formData.append('file', csvFile);
            formData.append('source', 'temp');

            const response = await axios.post(`${API_URL}/api/notification-visits/import-csv`, formData, {
                headers: {
                    ...authHeaders,
                    'Content-Type': 'multipart/form-data'
                }
            });
            setMessage(`Imported ${response.data.inserted} visit records from CSV.`);
        } catch (err) {
            console.error(err);
            const detail = err.response?.data?.detail;
            if (typeof detail === 'string') {
                setMessage(detail);
            } else if (detail?.errors?.length) {
                setMessage(detail.errors[0]);
            } else {
                setMessage('CSV import failed.');
            }
        } finally {
            setBusy(false);
        }
    };

    const handleRunEngine = async () => {
        setBusy(true);
        setMessage('');
        try {
            const symptomList = runSymptoms
                .split(',')
                .map((s) => s.trim())
                .filter(Boolean);

            const payload = {
                days: Number(runDays) || 7,
                source: 'temp',
                delete_source_after_run: true
            };
            if (symptomList.length > 0) payload.symptoms = symptomList;

            const response = await axios.post(`${API_URL}/api/notifications/run`, payload, { headers: authHeaders });
            setMessage(
                `Engine complete: ${response.data.groups_processed} groups processed, ${response.data.alerts_upserted} alerts upserted, ${response.data.deleted_source_visits} temp visits cleaned up.`
            );
            await loadFeed();
        } catch (err) {
            console.error(err);
            setMessage(err.response?.data?.detail || 'Failed to run notification engine.');
        } finally {
            setBusy(false);
        }
    };

    const handleSendNotification = async () => {
        if (!selectedId) {
            setMessage('Select a notification first.');
            return;
        }

        setBusy(true);
        setMessage('');
        try {
            const emails = emailRecipients.split(',').map((v) => v.trim()).filter(Boolean);

            const response = await axios.post(
                `${API_URL}/api/notifications/${selectedId}/send`,
                {
                    emails,
                    include_email: includeEmail
                },
                { headers: authHeaders }
            );

            setMessage(`Sent ${response.data.sent}, failed ${response.data.failed}.`);
            const deliveryResp = await axios.get(`${API_URL}/api/notifications/${selectedId}/deliveries`, { headers: authHeaders });
            setDeliveryLog(deliveryResp.data || []);
        } catch (err) {
            console.error(err);
            setMessage(err.response?.data?.detail || 'Failed to send notification.');
        } finally {
            setBusy(false);
        }
    };

    return (
        <div>
            <div className="header" style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button className="btn" onClick={() => navigate('/dashboard')} style={{ paddingLeft: 0 }}>
                        <ArrowLeft size={20} />
                    </button>
                    <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Bell size={24} /> Notification System
                    </h2>
                </div>
            </div>

            <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div className="card">
                    <h3>Import JSON Visits</h3>
                    <p style={{ color: 'var(--text-muted)', marginTop: 0 }}>Expected fields: visit_date, location, symptoms.</p>
                    <textarea
                        value={jsonInput}
                        onChange={(e) => setJsonInput(e.target.value)}
                        placeholder='{"visits":[{"visit_date":"2026-02-15","location":"FL","symptoms":["flu","fever"]}]}'
                        style={{ width: '100%', minHeight: '140px', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)' }}
                    />
                    <button className="btn btn-primary" onClick={handleImportJson} disabled={busy} style={{ marginTop: '0.75rem' }}>
                        <Upload size={16} /> Import JSON
                    </button>
                </div>

                <div className="card">
                    <h3>Import CSV Visits</h3>
                    <p style={{ color: 'var(--text-muted)', marginTop: 0 }}>Headers: visit_date, location, symptoms</p>
                    <input
                        type="file"
                        accept=".csv,text/csv"
                        onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                    />
                    <button className="btn btn-primary" onClick={handleImportCsv} disabled={busy} style={{ marginTop: '0.75rem' }}>
                        <Upload size={16} /> Import CSV
                    </button>

                    <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                        <h3 style={{ marginTop: 0 }}>Run Engine</h3>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                            <input
                                type="number"
                                min={1}
                                max={365}
                                value={runDays}
                                onChange={(e) => setRunDays(e.target.value)}
                                style={{ width: '90px', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)' }}
                            />
                            <input
                                type="text"
                                value={runSymptoms}
                                onChange={(e) => setRunSymptoms(e.target.value)}
                                placeholder="optional symptoms (comma-separated)"
                                style={{ flex: 1, minWidth: '220px', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)' }}
                            />
                            <button className="btn btn-primary" onClick={handleRunEngine} disabled={busy}>
                                <Play size={16} /> Run
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="card" style={{ marginBottom: '1rem' }}>
                <h3>Feed Filters</h3>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} style={{ padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                        <option value="">All Severities</option>
                        <option value="info">Info</option>
                        <option value="warning">Warning</option>
                        <option value="critical">Critical</option>
                    </select>
                    <input
                        value={locationFilter}
                        onChange={(e) => setLocationFilter(e.target.value.toUpperCase())}
                        placeholder="State code (FL)"
                        maxLength={2}
                        style={{ width: '140px', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)' }}
                    />
                    <input
                        value={symptomFilter}
                        onChange={(e) => setSymptomFilter(e.target.value)}
                        placeholder="Symptom"
                        style={{ minWidth: '220px', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)' }}
                    />
                </div>
                {message && (
                    <div style={{ marginTop: '0.75rem', color: 'var(--text-muted)' }}>
                        {message}
                    </div>
                )}
            </div>

            <div className="grid" style={{ gridTemplateColumns: '1.2fr 1fr', gap: '1rem' }}>
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)' }}>
                        <h3 style={{ margin: 0 }}>Notification Feed</h3>
                    </div>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead style={{ borderBottom: '1px solid var(--border)' }}>
                            <tr>
                                <th style={{ textAlign: 'left', padding: '0.75rem' }}>Severity</th>
                                <th style={{ textAlign: 'left', padding: '0.75rem' }}>Date</th>
                                <th style={{ textAlign: 'left', padding: '0.75rem' }}>Location</th>
                                <th style={{ textAlign: 'left', padding: '0.75rem' }}>Message</th>
                            </tr>
                        </thead>
                        <tbody>
                            {feed.map((item) => {
                                const meta = severityMeta[item.severity] || severityMeta.info;
                                const Icon = meta.icon;
                                return (
                                    <tr
                                        key={item.id}
                                        onClick={() => setSelectedId(item.id)}
                                        style={{
                                            cursor: 'pointer',
                                            borderBottom: '1px solid var(--border)',
                                            background: selectedId === item.id ? 'var(--background)' : 'transparent'
                                        }}
                                    >
                                        <td style={{ padding: '0.75rem', color: meta.color, fontWeight: 600 }}>
                                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                                                <Icon size={14} /> {item.severity}
                                            </span>
                                        </td>
                                        <td style={{ padding: '0.75rem' }}>{new Date(item.group_date).toLocaleDateString()}</td>
                                        <td style={{ padding: '0.75rem' }}>{item.location}</td>
                                        <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>{item.message}</td>
                                    </tr>
                                );
                            })}
                            {feed.length === 0 && (
                                <tr>
                                    <td colSpan={4} style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                        No alerts found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="card">
                    <h3>Notification Detail</h3>
                    {!selectedDetail && <p style={{ color: 'var(--text-muted)' }}>Select an alert to view details.</p>}

                    {selectedDetail && (
                        <div>
                            <p><strong>Severity:</strong> {selectedDetail.severity}</p>
                            <p><strong>Date:</strong> {new Date(selectedDetail.group_date).toLocaleDateString()}</p>
                            <p><strong>Location:</strong> {selectedDetail.location}</p>
                            <p><strong>Symptom:</strong> {selectedDetail.symptom}</p>
                            <p><strong>Total Visits:</strong> {selectedDetail.total_visits}</p>
                            <p><strong>Symptom Count:</strong> {selectedDetail.symptom_count}</p>
                            <p><strong>Rate:</strong> {(selectedDetail.rate * 100).toFixed(1)}%</p>
                            <p><strong>Threshold Used:</strong> {(selectedDetail.threshold_used * 100).toFixed(0)}%</p>
                            <p style={{ color: 'var(--text-muted)' }}>{selectedDetail.message}</p>

                            <h4 style={{ marginTop: '1rem' }}>Distribution Skew</h4>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                        <th style={{ textAlign: 'left', padding: '0.5rem' }}>Symptom</th>
                                        <th style={{ textAlign: 'right', padding: '0.5rem' }}>Count</th>
                                        <th style={{ textAlign: 'right', padding: '0.5rem' }}>Rate</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(distribution?.distribution || []).map((row) => (
                                        <tr key={row.symptom} style={{ borderBottom: '1px solid var(--border)' }}>
                                            <td style={{ padding: '0.5rem' }}>{row.symptom}</td>
                                            <td style={{ padding: '0.5rem', textAlign: 'right' }}>{row.count}</td>
                                            <td style={{ padding: '0.5rem', textAlign: 'right' }}>{(row.rate * 100).toFixed(1)}%</td>
                                        </tr>
                                    ))}
                                    {(!distribution || distribution.distribution.length === 0) && (
                                        <tr>
                                            <td colSpan={3} style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                                No distribution data.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>

                            <h4 style={{ marginTop: '1rem' }}>Send Alert</h4>
                            <div style={{ display: 'grid', gap: '0.5rem' }}>
                                <input
                                    type="text"
                                    value={emailRecipients}
                                    onChange={(e) => setEmailRecipients(e.target.value)}
                                    placeholder="Emails (comma-separated)"
                                    style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)' }}
                                />
                                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                    <label style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
                                        <input type="checkbox" checked={includeEmail} onChange={(e) => setIncludeEmail(e.target.checked)} />
                                        Email
                                    </label>
                                </div>
                                <button className="btn btn-primary" onClick={handleSendNotification} disabled={busy}>
                                    Send Notification
                                </button>
                            </div>

                            <h4 style={{ marginTop: '1rem' }}>Delivery History</h4>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                        <th style={{ textAlign: 'left', padding: '0.5rem' }}>Time</th>
                                        <th style={{ textAlign: 'left', padding: '0.5rem' }}>Channel</th>
                                        <th style={{ textAlign: 'left', padding: '0.5rem' }}>Recipient</th>
                                        <th style={{ textAlign: 'left', padding: '0.5rem' }}>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {deliveryLog.map((row) => (
                                        <tr key={row.id} style={{ borderBottom: '1px solid var(--border)' }}>
                                            <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>
                                                {new Date(row.created_at).toLocaleString()}
                                            </td>
                                            <td style={{ padding: '0.5rem' }}>{row.channel}</td>
                                            <td style={{ padding: '0.5rem' }}>{row.recipient}</td>
                                            <td style={{ padding: '0.5rem' }}>
                                                <span style={{ color: row.status === 'sent' ? '#16a34a' : '#dc2626' }}>
                                                    {row.status}
                                                </span>
                                                {row.error_message ? ` (${row.error_message})` : ''}
                                            </td>
                                        </tr>
                                    ))}
                                    {deliveryLog.length === 0 && (
                                        <tr>
                                            <td colSpan={4} style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                                No delivery attempts yet.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Notifications;
