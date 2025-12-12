import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { FileText, Loader2, AlertCircle } from 'lucide-react';
import { API_URL } from '../config';

const NoteDetails = ({ noteId }) => {
    const [note, setNote] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!noteId) return;

        const fetchNote = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await axios.get(`${API_URL}/api/notes/${noteId}`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setNote(response.data);
            } catch (err) {
                console.error(err);
                setError('Failed to load OCR note.');
            } finally {
                setLoading(false);
            }
        };

        fetchNote();
    }, [noteId]);

    if (loading) return (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <Loader2 className="animate-spin" size={48} style={{ margin: '0 auto 1rem', color: 'var(--primary)' }} />
            <h3>Loading OCR Note...</h3>
        </div>
    );

    if (error) return (
        <div className="card" style={{ textAlign: 'center', padding: '3rem', borderColor: 'var(--error)' }}>
            <AlertCircle size={48} style={{ margin: '0 auto 1rem', color: 'var(--error)' }} />
            <h3>Unable to load note</h3>
            <p style={{ color: 'var(--text-muted)' }}>{error}</p>
        </div>
    );

    return (
        <div className="grid">
            <div className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    <FileText className="text-primary" size={24} color="var(--primary)" />
                    <div>
                        <h3 style={{ margin: 0 }}>OCR Text</h3>
                        <div style={{ marginTop: '0.25rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                            Note #{note?.id}{note?.created_at ? ` • ${new Date(note.created_at).toLocaleString()}` : ''}
                        </div>
                    </div>
                </div>

                <textarea
                    value={note?.extracted_text || ''}
                    readOnly
                    style={{
                        width: '100%',
                        minHeight: '520px',
                        padding: '1rem',
                        borderRadius: '8px',
                        border: '1px solid var(--border)',
                        background: 'var(--bg-main)',
                        color: 'var(--text-main)',
                        fontFamily: 'monospace',
                        lineHeight: '1.5'
                    }}
                />
            </div>
        </div>
    );
};

export default NoteDetails;
