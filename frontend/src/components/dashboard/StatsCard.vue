<script setup lang="ts">
/**
 * StatsCard - Reusable statistics card component
 * 
 * Used to display key metrics on the dashboard with optional
 * trend indicators and icons.
 */
import { computed } from 'vue'
import type { Component } from 'vue'

interface Props {
  title: string
  value: string | number
  description?: string
  icon?: Component
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'destructive'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
})

const variantClasses = computed(() => {
  const variants: Record<string, string> = {
    default: '',
    primary: 'border-primary/50 bg-primary/5',
    success: 'border-green-500/50 bg-green-500/5',
    warning: 'border-yellow-500/50 bg-yellow-500/5',
    destructive: 'border-destructive/50 bg-destructive/5',
  }
  return variants[props.variant]
})

const trendClasses = computed(() => {
  if (!props.trend) return ''
  const trends: Record<string, string> = {
    up: 'text-green-600',
    down: 'text-destructive',
    neutral: 'text-muted-foreground',
  }
  return trends[props.trend]
})
</script>

<template>
  <div
    class="rounded-lg border bg-card p-6 transition-shadow hover:shadow-md"
    :class="variantClasses"
  >
    <div class="flex items-center justify-between">
      <span class="text-sm font-medium text-muted-foreground">{{ title }}</span>
      <component
        :is="icon"
        v-if="icon"
        class="h-4 w-4 text-muted-foreground"
      />
    </div>
    
    <div class="mt-2 flex items-baseline gap-2">
      <span class="text-2xl font-bold">{{ value }}</span>
      <span
        v-if="trendValue"
        class="text-sm font-medium"
        :class="trendClasses"
      >
        {{ trendValue }}
      </span>
    </div>
    
    <p
      v-if="description"
      class="mt-1 text-sm text-muted-foreground"
    >
      {{ description }}
    </p>
    
    <slot />
  </div>
</template>