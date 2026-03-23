<script setup lang="ts">
import { ref, provide, type Ref } from 'vue'

const open = ref<boolean>(false)

provide<Ref<boolean>>('dropdown-open', open)

function toggle() {
  open.value = !open.value
}

function close() {
  open.value = false
}

provide('dropdown-close', close)
</script>

<template>
  <div class="relative inline-block text-left">
    <div @click="toggle">
      <slot name="trigger" />
    </div>
    <div v-if="open" class="absolute right-0 mt-2 w-56 origin-top-right rounded-md bg-popover shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50" role="menu">
      <slot />
    </div>
  </div>
</template>