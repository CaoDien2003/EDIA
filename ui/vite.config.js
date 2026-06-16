import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,        // bind 0.0.0.0 so remote/VS Code SSH can reach it
    port: 3000,
    strictPort: true,
  },
})
