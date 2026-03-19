<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  type ChartOptions,
} from 'chart.js'
import type { BenchmarkResult } from '@/types/benchmark'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const props = defineProps<{
  results: BenchmarkResult[]
  title?: string
}>()

// 颜色配置
const getBarColor = (index: number, total: number) => {
  // 根据延迟排序，最快的最绿，最慢的最红
  const sorted = [...props.results].sort((a, b) => a.latency_ms - b.latency_ms)
  const sortedIndex = sorted.findIndex((r) => r.config_name === props.results[index].config_name)
  const ratio = sortedIndex / Math.max(total - 1, 1)

  if (ratio === 0) {
    return {
      bg: 'rgba(34, 197, 94, 0.8)',
      border: 'rgba(34, 197, 94, 1)',
    }
  } else if (ratio < 0.5) {
    return {
      bg: 'rgba(59, 130, 246, 0.8)',
      border: 'rgba(59, 130, 246, 1)',
    }
  } else {
    return {
      bg: 'rgba(249, 115, 22, 0.8)',
      border: 'rgba(249, 115, 22, 1)',
    }
  }
}

const chartData = computed(() => {
  const sorted = [...props.results].sort((a, b) => b.latency_ms - a.latency_ms)
  const labels = sorted.map((r) => r.config_name)
  const data = sorted.map((r) => r.latency_ms)

  return {
    labels,
    datasets: [
      {
        label: '延迟 (ms)',
        data,
        backgroundColor: sorted.map((_, i) => getBarColor(props.results.findIndex((r) => r.config_name === sorted[i].config_name), props.results.length).bg),
        borderColor: sorted.map((_, i) => getBarColor(props.results.findIndex((r) => r.config_name === sorted[i].config_name), props.results.length).border),
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  }
})

const chartOptions: ChartOptions<'bar'> = {
  indexAxis: 'y', // 水平条形图
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    title: {
      display: !!props.title,
      text: props.title || '',
      font: {
        size: 14,
        weight: 'bold',
      },
      padding: {
        bottom: 16,
      },
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      padding: 12,
      titleFont: {
        size: 13,
      },
      bodyFont: {
        size: 12,
      },
      cornerRadius: 8,
      callbacks: {
        label: (context) => {
          const value = context.raw as number
          return `延迟: ${value.toFixed(2)} ms`
        },
      },
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      title: {
        display: true,
        text: '延迟 (ms)',
        font: {
          size: 11,
        },
      },
      grid: {
        color: 'rgba(148, 163, 184, 0.2)',
      },
    },
    y: {
      grid: {
        display: false,
      },
      ticks: {
        font: {
          size: 12,
        },
      },
    },
  },
}
</script>

<template>
  <div class="w-full">
    <div v-if="results.length === 0" class="flex h-48 items-center justify-center text-muted-foreground">
      暂无数据
    </div>
    <div v-else class="h-64">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>