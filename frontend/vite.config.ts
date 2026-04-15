import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite dev server proxies /api to the Flask backend at 5057 so the
// React app can use relative fetch URLs in both dev and prod.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5057',
        changeOrigin: true,
      },
    },
  },
})
