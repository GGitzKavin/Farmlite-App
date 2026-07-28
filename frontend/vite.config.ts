import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('firebase')) return 'firebase';
          if (id.includes('recharts')) return 'charts';
          if (id.includes('jspdf') || id.includes('html2canvas')) return 'pdf';
          if (id.includes('framer-motion')) return 'motion';
          return undefined;
        },
      },
    },
  },
})
