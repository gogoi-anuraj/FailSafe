import { defineConfig } from 'vite'
import react      from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],

  server: {
    port: 3000,
    // Proxy only used in development.
    // In production the frontend calls VITE_API_URL directly.
    proxy: {
      '/api': {
        target     : 'http://localhost:8000',
        changeOrigin: true,
        rewrite    : (path) => path.replace(/^\/api/, ''),
      },
    },
  },

  build: {
    outDir     : 'dist',
    sourcemap  : false,    // disable in prod for smaller bundle
    chunkSizeWarningLimit: 1000,
  },
})
