<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Languages } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const { locale } = useI18n()

const languages = [
  { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
  { code: 'en-US', name: 'English', flag: '🇺🇸' },
]

const currentLang = computed(() => locale.value)

function switchLanguage(code: string) {
  locale.value = code
  localStorage.setItem('locale', code)
}
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="ghost" size="icon" aria-label="Switch language">
        <Languages class="h-4 w-4" />
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end">
      <DropdownMenuItem
        v-for="lang in languages"
        :key="lang.code"
        :class="{ 'bg-accent': currentLang === lang.code }"
        role="menuitem"
        @click="switchLanguage(lang.code)"
      >
        <span class="mr-2">{{ lang.flag }}</span>
        {{ lang.name }}
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>