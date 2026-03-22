<script setup lang="ts">
import { type HTMLAttributes, computed } from 'vue'
import { SelectValue as RadixSelectValue, type SelectValueProps } from 'radix-vue'

const props = defineProps<SelectValueProps & { class?: HTMLAttributes['class'] }>()
</script>

<template>
  <RadixSelectValue v-bind="props" :class="props.class">
    <slot />
  </RadixSelectValue>
</template>