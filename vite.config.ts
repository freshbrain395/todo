import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  // @ts-ignore
  test: {
    environment: 'happy-dom',
    globals: true
  },
  // Vite options tailored for Tauri development & HMR
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: true,
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 1420
    },
    watch: {
      ignored: ['**/src-tauri/**']
    }
  }
})
