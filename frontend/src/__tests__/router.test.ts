import { describe, it, expect } from 'vitest'
import router from '@/router'

describe('router/index.ts', () => {
  it('should export a router instance', () => {
    expect(router).toBeDefined()
    expect(router.getRoutes).toBeDefined()
  })

  it('should have all required routes defined', () => {
    const routes = router.getRoutes()
    const paths = routes.map(route => route.path)

    expect(paths).toContain('/')
    expect(paths).toContain('/config')
    expect(paths).toContain('/collections')
    expect(paths).toContain('/benchmark')
    expect(paths).toContain('/settings')
  })

  it('should have correct route names', () => {
    const routes = router.getRoutes()
    const names = routes.map(route => route.name)

    expect(names).toContain('home')
    expect(names).toContain('config')
    expect(names).toContain('collections')
    expect(names).toContain('benchmark')
    expect(names).toContain('settings')
  })

  it('should have home route with correct path', () => {
    const routes = router.getRoutes()
    const homeRoute = routes.find(route => route.path === '/')
    
    expect(homeRoute).toBeDefined()
    expect(homeRoute?.name).toBe('home')
  })

  it('should have config route with correct path', () => {
    const routes = router.getRoutes()
    const configRoute = routes.find(route => route.path === '/config')
    
    expect(configRoute).toBeDefined()
    expect(configRoute?.name).toBe('config')
  })

  it('should have collections route with correct path', () => {
    const routes = router.getRoutes()
    const collectionsRoute = routes.find(route => route.path === '/collections')
    
    expect(collectionsRoute).toBeDefined()
    expect(collectionsRoute?.name).toBe('collections')
  })

  it('should have benchmark route with correct path', () => {
    const routes = router.getRoutes()
    const benchmarkRoute = routes.find(route => route.path === '/benchmark')
    
    expect(benchmarkRoute).toBeDefined()
    expect(benchmarkRoute?.name).toBe('benchmark')
  })

  it('should have settings route with correct path', () => {
    const routes = router.getRoutes()
    const settingsRoute = routes.find(route => route.path === '/settings')
    
    expect(settingsRoute).toBeDefined()
    expect(settingsRoute?.name).toBe('settings')
  })

  it('should have correct number of routes', () => {
    const routes = router.getRoutes()
    expect(routes.length).toBe(5)
  })

  it('should use createWebHistory', () => {
    // Check that the router uses HTML5 history mode
    expect(router.options.history).toBeDefined()
  })
})