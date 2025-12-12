import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, FileText, BarChart2, Shield, Zap, CheckCircle, ArrowRight } from 'lucide-react';

const LandingPage = () => {
    const navigate = useNavigate();

    return (
        <div className="animate-fade-in">
            {/* Hero Section */}
            <div style={{
                textAlign: 'center',
                padding: '4rem 1rem 6rem',
                background: 'radial-gradient(circle at top, rgba(37,99,235,0.1) 0%, transparent 70%)'
            }}>
                <div style={{
                    display: 'inline-block',
                    padding: '0.5rem 1rem',
                    borderRadius: '50px',
                    background: 'rgba(37,99,235,0.1)',
                    color: 'var(--primary)',
                    fontWeight: '600',
                    fontSize: '0.9rem',
                    marginBottom: '1.5rem',
                    border: '1px solid rgba(37,99,235,0.2)'
                }}>
                    ✨ AI-Powered Medical Scribing
                </div>
                <h1 style={{
                    fontSize: '3.5rem',
                    fontWeight: '800',
                    letterSpacing: '-0.02em',
                    marginBottom: '1.5rem',
                    background: 'linear-gradient(135deg, var(--text-main) 0%, var(--primary) 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    lineHeight: 1.1
                }}>
                    Focus on Patients,<br />Not Paperwork.
                </h1>
                <p style={{
                    fontSize: '1.25rem',
                    color: 'var(--text-muted)',
                    maxWidth: '700px',
                    margin: '0 auto 2.5rem',
                    lineHeight: 1.6
                }}>
                    MediScribe AI listens to your consultations and automatically generates accurate, redacted SOAP notes and analytics in seconds.
                </p>

                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                    <button
                        className="btn btn-primary"
                        onClick={() => navigate('/login')}
                        style={{
                            fontSize: '1.1rem',
                            padding: '0.8rem 2rem',
                            borderRadius: '50px',
                            boxShadow: '0 4px 14px 0 rgba(37,99,235,0.39)'
                        }}
                    >
                        Get Started <ArrowRight size={20} style={{ marginLeft: '0.5rem', verticalAlign: 'text-bottom' }} />
                    </button>
                    <button
                        className="btn"
                        onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
                        style={{
                            fontSize: '1.1rem',
                            padding: '0.8rem 2rem',
                            borderRadius: '50px',
                            background: 'var(--surface)',
                            border: '1px solid var(--border)'
                        }}
                    >
                        Learn More
                    </button>
                </div>
            </div>

            {/* Features Grid */}
            <div id="features" style={{ padding: '4rem 1rem', maxWidth: '1200px', margin: '0 auto' }}>
                <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
                    {/* Feature 1 */}
                    <div className="card" style={{ padding: '2rem', borderTop: '4px solid var(--primary)' }}>
                        <div style={{
                            width: '50px', height: '50px',
                            borderRadius: '12px',
                            background: 'rgba(37,99,235,0.1)',
                            color: 'var(--primary)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            marginBottom: '1.5rem'
                        }}>
                            <Mic size={24} />
                        </div>
                        <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Ambient Listening</h3>
                        <p style={{ color: 'var(--text-muted)', lineHeight: 1.6 }}>
                            Simply press record. Our AI intelligently captures dialogue, distinguishing between doctor and patient speakers automatically.
                        </p>
                    </div>

                    {/* Feature 2 */}
                    <div className="card" style={{ padding: '2rem', borderTop: '4px solid #10b981' }}>
                        <div style={{
                            width: '50px', height: '50px',
                            borderRadius: '12px',
                            background: 'rgba(16,185,129,0.1)',
                            color: '#10b981',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            marginBottom: '1.5rem'
                        }}>
                            <Zap size={24} />
                        </div>
                        <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Instant SOAP Notes</h3>
                        <p style={{ color: 'var(--text-muted)', lineHeight: 1.6 }}>
                            Turn 15 minutes of conversation into a structured SOAP note in under 30 seconds. No more late-night charting.
                        </p>
                    </div>

                    {/* Feature 3 */}
                    <div className="card" style={{ padding: '2rem', borderTop: '4px solid #f59e0b' }}>
                        <div style={{
                            width: '50px', height: '50px',
                            borderRadius: '12px',
                            background: 'rgba(245,158,11,0.1)',
                            color: '#f59e0b',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            marginBottom: '1.5rem'
                        }}>
                            <BarChart2 size={24} />
                        </div>
                        <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Population Analytics</h3>
                        <p style={{ color: 'var(--text-muted)', lineHeight: 1.6 }}>
                            Track disease trends, patient sentiment, and clinic metrics effortlessly with our built-in analytics dashboard.
                        </p>
                    </div>
                </div>
            </div>

            {/* Footer / Trust Section */}
            <div style={{ textAlign: 'center', padding: '4rem 1rem', borderTop: '1px solid var(--border)', marginTop: '4rem' }}>
                <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '0.9rem' }}>Trusted by Modern Clinics</p>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '3rem', flexWrap: 'wrap', opacity: 0.6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold', fontSize: '1.2rem' }}><Shield size={20} /> SecureHealth</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold', fontSize: '1.2rem' }}><CheckCircle size={20} /> MediCare+</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold', fontSize: '1.2rem' }}><FileText size={20} /> DocAssist</div>
                </div>
            </div>
        </div>
    );
};

export default LandingPage;
