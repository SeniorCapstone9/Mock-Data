import React, { useEffect, useState } from 'react';
import { FileText, Shield, Activity, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';

const Results = ({ recordId }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!recordId) return;

        const pollInterval = setInterval(async () => {
            try {
                const response = await axios.get(`http://localhost:8002/api/results/${recordId}`);
                setData(response.data);

                if (response.data.status === 'completed' || response.data.status === 'failed') {
                    setLoading(false);
                    clearInterval(pollInterval);
                }
            } catch (err) {
                console.error("Polling error:", err);
                setError("Failed to fetch results");
                setLoading(false);
                clearInterval(pollInterval);
            }
        }, 2000);

        return () => clearInterval(pollInterval);
    }, [recordId]);

    if (!data && loading) return (
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
        <div className="grid">
            <div className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    <Shield className="text-primary" size={24} color="var(--primary)" />
                    <h3 style={{ margin: 0 }}>Redacted Transcript</h3>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, color: 'var(--text-main)', maxHeight: '500px', overflowY: 'auto' }}>
                    {data.redacted_transcript}
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
