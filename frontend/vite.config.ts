import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  server: command === 'serve' ? {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: ['.trycloudflare.com'],
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
  } : undefined,
  build: { outDir: 'dist', emptyOutDir: true },
}))
