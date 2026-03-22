import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN.yaml'
import enUS from './locales/en-US.yaml'

const savedLocale = localStorage.getItem('locale') || 'zh-CN'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en-US',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
})

export default i18n