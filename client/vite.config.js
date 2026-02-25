import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: true,
    proxy: {
      '/api': 'http://127.0.0.1:8002',
      '/token': 'http://127.0.0.1:8002',
      '/temp': 'http://127.0.0.1:8002',
      '/docs': 'http://127.0.0.1:8002',
      '/openapi.json': 'http://127.0.0.1:8002',
    },
  }
})
