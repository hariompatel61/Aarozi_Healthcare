export function useApi() {
  const config = useRuntimeConfig()
  const apiBase = (config.public.apiBase as string) || 'http://localhost:8000'

  function getHeaders(customHeaders: Record<string, string> = {}) {
    const headers: Record<string, string> = { ...customHeaders }
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token') || localStorage.getItem('access_token')
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
    }
    return headers
  }

  async function get<T>(endpoint: string, options: any = {}) {
    return await $fetch<T>(`${apiBase}${endpoint}`, {
      method: 'GET',
      ...options,
      headers: getHeaders(options.headers || {})
    })
  }

  async function post<T>(endpoint: string, body: any = {}, options: any = {}) {
    return await $fetch<T>(`${apiBase}${endpoint}`, {
      method: 'POST',
      body,
      ...options,
      headers: getHeaders(options.headers || {})
    })
  }

  async function put<T>(endpoint: string, body: any = {}, options: any = {}) {
    return await $fetch<T>(`${apiBase}${endpoint}`, {
      method: 'PUT',
      body,
      ...options,
      headers: getHeaders(options.headers || {})
    })
  }

  async function patch<T>(endpoint: string, body: any = {}, options: any = {}) {
    return await $fetch<T>(`${apiBase}${endpoint}`, {
      method: 'PATCH',
      body,
      ...options,
      headers: getHeaders(options.headers || {})
    })
  }

  async function del<T>(endpoint: string, options: any = {}) {
    return await $fetch<T>(`${apiBase}${endpoint}`, {
      method: 'DELETE',
      ...options,
      headers: getHeaders(options.headers || {})
    })
  }

  return {
    get,
    post,
    put,
    patch,
    delete: del,
  }
}