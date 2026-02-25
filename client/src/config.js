// config.js
// If VITE_API_URL is explicitly set (even to empty string), use it.
// Otherwise:
// - local dev on your own machine defaults to localhost backend
// - remote/RunPod dev defaults to same-origin relative paths (via Vite proxy)

const envUrl = import.meta.env.VITE_API_URL;
const isLocalhost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
const defaultUrl = isLocalhost ? 'http://localhost:8002' : '';

export const API_URL = window.API_URL ?? (envUrl !== undefined ? envUrl : defaultUrl);
