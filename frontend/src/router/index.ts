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
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/Settings.vue'),
    },
  ],
})

export default router