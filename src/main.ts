import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { initBackendStorage } from './utils/aiStorage'

initBackendStorage().finally(() => {
  createApp(App).mount('#app')
})
