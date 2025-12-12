import React, { useEffect, useState } from 'react';
import { FileText, Shield, Activity, CheckCircle, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';

const Results = ({ id }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();
    const role = localStorage.getItem('role');

    useEffect(() => {
        if (!id) return;

        const fetchResult = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await axios.get(`${API_URL}/api/results/${id}`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setData(response.data);

                if (response.data.status === 'completed' || response.data.status === 'failed') {
                    setLoading(false);
                }
            } catch (err) {
                console.error("Polling error:", err);
                setError("Failed to fetch results");
                setLoading(false);
            }
        };

        fetchResult(); // Fetch immediately on mount
        const interval = setInterval(fetchResult, 3000); // Poll every 3s

        return () => clearInterval(interval); // Cleanup on unmount
    }, [id]);

    const deleteRecord = async () => {
        if (!confirm("Are you sure you want to delete this record?")) return;
        try {
            const token = localStorage.getItem('token');
            await axios.delete(`${API_URL}/api/records/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            alert("Record deleted");
            navigate('/dashboard');
        } catch (err) {
            alert("Error deleting record");
        }
    };

    if (loading) return (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <Loader2 className="animate-spin" size={48} style={{ margin: '0 auto 1rem', color: 'var(--primary)' }} />
            <h3>Processing Audio...</h3>
            <p style={{ color: 'var(--text-muted)' }}>Transcribing, Diarizing, and Generating Notes</p>
        </div>
    );

    if (error || data?.status === 'failed') return (
        <div className="card" style={{ textAlign: 'center', padding: '3rem', borderColor: 'var(--error)' }}>
            <AlertCircle size={48} style={{ margin: '0 auto 1rem', color: 'var(--error)' }} />
            <h3>Processing Failed</h3>
            <p style={{ color: 'var(--text-muted)' }}>Something went wrong during processing.</p>
        </div>
    );

    return (
        <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
            <div className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    <Shield className="text-primary" size={24} color="var(--primary)" />
                    <h3 style={{ margin: 0 }}>{role === 'admin' ? 'Redacted Transcript' : 'Full Transcript'}</h3>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, color: 'var(--text-main)', maxHeight: '500px', overflowY: 'auto' }}>
                    {role === 'admin' ? data.redacted_transcript : data.full_transcript}
                </div>
            </div>

            <div className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    <Activity className="text-primary" size={24} color="var(--success)" />
                    <h3 style={{ margin: 0 }}>SOAP Note</h3>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, color: 'var(--text-main)', maxHeight: '500px', overflowY: 'auto' }}>
                    {data.soap_summary}
                </div>
            </div>

        </div>
    );
};

export default Results;
