import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN.yaml'
import enUS from './locales/en-US.yaml'

// Default to English, fallback to saved preference
const savedLocale = localStorage.getItem('locale') || 'en-US'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const messages: any = {
  'zh-CN': zhCN,
  'en-US': enUS,
}

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en-US',
  messages,
})

export default i18n