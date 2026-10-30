import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // No Gateway yet (port set by E0-04): forward to the catalog service meanwhile.
    proxy: {
      '/api': 'http://127.0.0.1:8002',
    },
  },
})
