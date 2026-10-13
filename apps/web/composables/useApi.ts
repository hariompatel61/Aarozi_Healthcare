export function useApi() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  async function get<T>(endpoint: string, options = {}) {
    return await $fetch<T>(`${apiBase}${endpoint}`, {
      method: 'GET',
      ...options
    })
  }

  async function post<T>(endpoint: string, body: any, options = {}) {
    return await $fetch<T>(`${apiBase}${endpoint}`, {
      method: 'POST',
      body,
      ...options
    })
  }

  return {
    get,
    post
  }
}