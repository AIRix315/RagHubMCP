<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Home,
  Settings,
  Database,
  BarChart3,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  Layers,
  TestTube,
  FlaskConical,
} from 'lucide-vue-next'
import { useSidebar } from '@/composables/useSidebar'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Button } from '@/components/ui/button'

const { t } = useI18n()
const route = useRoute()
const {
  isCollapsed,
  isMobile,
  toggleCollapsed,
  SIDEBAR_WIDTH_EXPANDED,
  SIDEBAR_WIDTH_COLLAPSED,
} = useSidebar()

// Navigation items
const navItems = computed(() => [
  {
    path: '/',
    name: 'home',
    icon: Home,
    label: t('nav.home'),
  },
  {
    path: '/config',
    name: 'config',
    icon: Settings,
    label: t('nav.config'),
  },
  {
    path: '/collections',
    name: 'collections',
    icon: Database,
    label: t('nav.collections'),
  },
  {
    path: '/benchmark',
    name: 'benchmark',
    icon: BarChart3,
    label: t('nav.benchmark'),
  },
  {
    path: '/test/rerank-lab',
    name: 'rerank-lab',
    icon: FlaskConical,
    label: t('nav.rerankLab'),
  },
  {
    path: '/settings',
    name: 'settings',
    icon: SlidersHorizontal,
    label: t('nav.settings'),
  },
])

// Check if a nav item is active
function isActive(path: string, name: string): boolean {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path) || route.name === name
}

// Computed sidebar width
const sidebarWidth = computed(() => {
  if (isMobile.value) return SIDEBAR_WIDTH_EXPANDED
  return isCollapsed.value ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED
})
</script>

<template>
  <aside
    class="flex h-full flex-col bg-sidebar border-r border-sidebar-border transition-all duration-300 ease-in-out"
    :style="{ width: `${sidebarWidth}px` }"
  >
    <!-- Logo Header -->
    <div
      class="flex h-14 items-center border-b border-sidebar-border px-4"
      :class="isCollapsed && !isMobile ? 'justify-center' : 'justify-between'"
    >
      <div class="flex items-center gap-2 overflow-hidden">
        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Layers class="h-5 w-5" />
        </div>
        <Transition
          enter-active-class="transition-all duration-200"
          enter-from-class="opacity-0 -translate-x-2"
          enter-to-class="opacity-100 translate-x-0"
          leave-active-class="transition-all duration-200"
          leave-from-class="opacity-100 translate-x-0"
          leave-to-class="opacity-0 -translate-x-2"
        >
          <span
            v-if="!isCollapsed || isMobile"
            class="text-lg font-bold text-sidebar-foreground whitespace-nowrap"
          >
            RagHub
          </span>
        </Transition>
      </div>
      
      <!-- Collapse toggle button (desktop only) -->
      <Button
        v-if="!isMobile"
        variant="ghost"
        size="icon"
        class="h-8 w-8 shrink-0"
        :class="isCollapsed ? 'absolute -right-3 top-3 z-10 rounded-full bg-background border shadow-elevation-1' : ''"
        @click="toggleCollapsed"
      >
        <ChevronLeft v-if="!isCollapsed" class="h-4 w-4" />
        <ChevronRight v-else class="h-4 w-4" />
      </Button>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto scrollbar-thin p-2">
      <TooltipProvider :delay-duration="0">
        <ul class="space-y-1">
          <li v-for="item in navItems" :key="item.path">
            <!-- Collapsed state with tooltip -->
            <Tooltip v-if="isCollapsed && !isMobile">
              <TooltipTrigger as-child>
                <RouterLink
                  :to="item.path"
                  class="nav-item-collapsed"
                  :class="{ active: isActive(item.path, item.name) }"
                >
                  <component :is="item.icon" class="h-5 w-5" />
                </RouterLink>
              </TooltipTrigger>
              <TooltipContent side="right" :side-offset="8">
                {{ item.label }}
              </TooltipContent>
            </Tooltip>
            
            <!-- Expanded state -->
            <RouterLink
              v-else
              :to="item.path"
              class="nav-item"
              :class="{ active: isActive(item.path, item.name) }"
            >
              <component :is="item.icon" class="h-5 w-5 shrink-0" />
              <span class="truncate">{{ item.label }}</span>
            </RouterLink>
          </li>
        </ul>
      </TooltipProvider>
    </nav>

    <!-- Footer -->
    <div class="border-t border-sidebar-border p-2">
      <Transition
        enter-active-class="transition-all duration-200"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-all duration-200"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="!isCollapsed || isMobile"
          class="px-2 py-1 text-xs text-muted-foreground"
        >
          <span>v1.0.0</span>
        </div>
      </Transition>
    </div>
  </aside>
</template>
