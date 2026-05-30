import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ArcoVue from '@arco-design/web-vue'
import '@arco-design/web-vue/dist/arco.css'

import App from './App.vue'
import router from './router'
import './styles/main.css'

// 启用 Arco Design 官方暗色模式
document.body.setAttribute('arco-theme', 'dark')

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ArcoVue, {
  componentConfig: {
    select: { popupContainer: '#app' },
    popconfirm: { popupContainer: '#app' },
    tooltip: { popupContainer: '#app' },
    popover: { popupContainer: '#app' },
    dropdown: { popupContainer: '#app' },
    modal: { popupContainer: '#app' },
  },
})

app.mount('#app')
