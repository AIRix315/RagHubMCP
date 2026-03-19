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

// 颜色配置 - 与 shadcn-vue 主题协调
const chartColors = {
  primary: 'rgba(59, 130, 246, 0.8)',
  primaryBorder: 'rgba(59, 130, 246, 1)',
  secondary: 'rgba(139, 92, 246, 0.8)',
  secondaryBorder: 'rgba(139, 92, 246, 1)',
  accent: 'rgba(34, 197, 94, 0.8)',
  accentBorder: 'rgba(34, 197, 94, 1)',
  muted: 'rgba(148, 163, 184, 0.8)',
  mutedBorder: 'rgba(148, 163, 184, 1)',
}

const chartData = computed(() => {
  const labels = props.results.map((r) => r.config_name)
  const latencyData = props.results.map((r) => r.latency_ms)
  const resultCounts = props.results.map((r) => r.results.length)

  // 计算平均分数
  const avgScores = props.results.map((r) => {
    if (r.results.length === 0) return 0
    const sum = r.results.reduce((acc, item) => {
      return acc + (item.rerank_score ?? item.score)
    }, 0)
    return sum / r.results.length
  })

  return {
    labels,
    datasets: [
      {
        label: '延迟 (ms)',
        data: latencyData,
        backgroundColor: chartColors.primary,
        borderColor: chartColors.primaryBorder,
        borderWidth: 1,
        borderRadius: 4,
        yAxisID: 'y',
      },
      {
        label: '平均分数 (×100)',
        data: avgScores.map((s) => s * 100),
        backgroundColor: chartColors.accent,
        borderColor: chartColors.accentBorder,
        borderWidth: 1,
        borderRadius: 4,
        yAxisID: 'y1',
      },
      {
        label: '结果数量',
        data: resultCounts,
        backgroundColor: chartColors.secondary,
        borderColor: chartColors.secondaryBorder,
        borderWidth: 1,
        borderRadius: 4,
        yAxisID: 'y',
      },
    ],
  }
})

const chartOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  plugins: {
    legend: {
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 16,
        font: {
          size: 12,
        },
      },
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
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        font: {
          size: 12,
        },
      },
    },
    y: {
      type: 'linear',
      display: true,
      position: 'left',
      title: {
        display: true,
        text: '延迟 (ms) / 结果数量',
        font: {
          size: 11,
        },
      },
      grid: {
        color: 'rgba(148, 163, 184, 0.2)',
      },
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      title: {
        display: true,
        text: '平均分数 (×100)',
        font: {
          size: 11,
        },
      },
      grid: {
        drawOnChartArea: false,
      },
    },
  },
}
</script>

<template>
  <div class="w-full">
    <div v-if="results.length === 0" class="flex h-64 items-center justify-center text-muted-foreground">
      暂无数据
    </div>
    <div v-else class="h-80">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>