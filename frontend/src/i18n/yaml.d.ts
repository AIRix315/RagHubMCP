// Type declarations for YAML modules
declare module '*.yaml' {
  const value: Record<string, unknown>
  export default value
}

declare module '*.yml' {
  const value: Record<string, unknown>
  export default value
}