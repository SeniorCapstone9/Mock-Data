import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Lock } from 'lucide-react';

import { API_URL } from '../config';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setError(''); // Clear previous error

        try {
            // Use FormData from the form element directly to handle autofill correctly
            const formData = new FormData(e.currentTarget);

            // Log what we are sending for debugging (safe to remove later)
            console.log("Logging in with:", Object.fromEntries(formData));

            const response = await axios.post(`${API_URL}/token`, formData);
            localStorage.setItem('token', response.data.access_token);
            localStorage.setItem('role', response.data.role);

            if (response.data.role === 'admin') navigate('/admin');
            else if (response.data.role === 'patient') navigate('/portal');
            else navigate('/dashboard');
        } catch (err) {
            console.error("Login failed:", err);
            setError('Invalid credentials');
        }
    };

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
            <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div style={{ display: 'inline-flex', padding: '1rem', borderRadius: '50%', background: 'var(--primary)', color: 'white', marginBottom: '1rem' }}>
                        <Lock size={32} />
                    </div>
                    <h2>Admin Login</h2>
                </div>

                <form onSubmit={handleLogin}>
                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Username</label>
                        <input
                            type="text"
                            name="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            style={{ width: '100%', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}
                            required
                        />
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Password</label>
                        <input
                            type="password"
                            name="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            style={{ width: '100%', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}
                            required
                        />
                    </div>

                    {error && <p style={{ color: 'var(--error)', marginBottom: '1rem' }}>{error}</p>}

                    <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                        Sign In
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Login;
