// config.js
// If VITE_API_URL is explicitly set (even to empty string), use it.
// Otherwise fallback to localhost.

const envUrl = import.meta.env.VITE_API_URL;
export const API_URL = window.API_URL ?? (envUrl !== undefined ? envUrl : 'http://localhost:8002');
