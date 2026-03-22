import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

export function useLocale() {
  const { locale, availableLocales, t } = useI18n()

  const currentLocale = computed(() => locale.value)

  const localeOptions = [
    { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
    { code: 'en-US', name: 'English', flag: '🇺🇸' },
  ]

  function setLocale(code: string) {
    locale.value = code
    localStorage.setItem('locale', code)
    document.documentElement.setAttribute('lang', code)
  }

  function getLocaleFromStorage(): string {
    return localStorage.getItem('locale') || 'zh-CN'
  }

  return {
    locale,
    currentLocale,
    availableLocales,
    localeOptions,
    setLocale,
    getLocaleFromStorage,
    t,
  }
}