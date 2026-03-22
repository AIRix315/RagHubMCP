import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
    },
    {
      path: '/config',
      name: 'config',
      component: () => import('@/views/Config.vue'),
    },
    {
      path: '/config/providers/rerank',
      name: 'rerank-providers',
      component: () => import('@/views/Config/Providers/Rerank.vue'),
    },
    {
      path: '/config/pipeline',
      name: 'pipeline',
      component: () => import('@/views/Config/Pipeline.vue'),
    },
    {
      path: '/collections',
      name: 'collections',
      component: () => import('@/views/Collections.vue'),
    },
    {
      path: '/benchmark',
      name: 'benchmark',
      component: () => import('@/views/Benchmark.vue'),
    },
    {
      path: '/test/rerank-lab',
      name: 'rerank-lab',
      component: () => import('@/views/Test/RerankLab.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/Settings.vue'),
    },
  ],
})

export default router