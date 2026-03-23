<script setup lang="ts">
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { X } from 'lucide-vue-next'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import { useSidebar } from '@/composables/useSidebar'
import { Button } from '@/components/ui/button'

const route = useRoute()
const { isCollapsed, isMobile, isMobileOpen, closeMobile } = useSidebar()

// Close mobile sidebar on route change
watch(
  () => route.path,
  () => {
    if (isMobileOpen.value) {
      closeMobile()
    }
  }
)
</script>

<template>
  <div class="flex min-h-screen bg-background">
    <!-- Desktop Sidebar -->
    <div v-if="!isMobile" class="shrink-0">
      <Sidebar />
    </div>

    <!-- Mobile Sidebar Overlay -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-opacity duration-300"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-opacity duration-300"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="isMobile && isMobileOpen"
          class="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
          @click="closeMobile"
        />
      </Transition>
      
      <Transition
        enter-active-class="transition-transform duration-300 ease-out"
        enter-from-class="-translate-x-full"
        enter-to-class="translate-x-0"
        leave-active-class="transition-transform duration-300 ease-in"
        leave-from-class="translate-x-0"
        leave-to-class="-translate-x-full"
      >
        <div
          v-if="isMobile && isMobileOpen"
          class="fixed inset-y-0 left-0 z-50 w-72 shadow-elevation-4"
        >
          <Sidebar />
          <Button
            variant="ghost"
            size="icon"
            class="absolute right-2 top-2"
            @click="closeMobile"
          >
            <X class="h-5 w-5" />
          </Button>
        </div>
      </Transition>
    </Teleport>

    <!-- Main Content Area -->
    <div class="flex flex-1 flex-col min-w-0">
      <Header />
      
      <main class="flex-1 overflow-auto">
        <div class="container mx-auto p-4 md:p-6">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>
