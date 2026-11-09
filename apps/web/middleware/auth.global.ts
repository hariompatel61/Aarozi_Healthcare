export default defineNuxtRouteMiddleware((to) => {
  // Public routes that do not require authentication
  const publicRoutes = ['/', '/login', '/design-system', '/forgot-password', '/reset-password']

  const authCookie = useCookie('auth_token', { path: '/' })
  if (to.query.auth) {
    authCookie.value = String(to.query.auth)
  }

  const token = authCookie.value || (import.meta.client ? localStorage.getItem('token') : null)

  if (publicRoutes.includes(to.path)) {
    // If already logged in and visiting login, redirect to dashboard
    if (to.path === '/login' && token && !to.query.force) {
      return navigateTo('/dashboard')
    }
    return
  }

  // Protected LIS screens
  if (!token) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }
})
