export default defineNuxtRouteMiddleware((to) => {
  // Public route prefixes that do not require authentication
  const isPublicRoute =
    to.path === '/' ||
    to.path === '/login' ||
    to.path === '/signup' ||
    to.path === '/forgot-password' ||
    to.path === '/reset-password' ||
    to.path === '/design-system' ||
    to.path === '/product' ||
    to.path === '/pricing' ||
    to.path === '/report-formats' ||
    to.path === '/download' ||
    to.path === '/support' ||
    to.path === '/about' ||
    to.path === '/contact' ||
    to.path === '/faq' ||
    to.path === '/privacy' ||
    to.path === '/terms' ||
    to.path === '/licence-terms' ||
    to.path.startsWith('/features') ||
    to.path.startsWith('/solutions') ||
    to.path.startsWith('/blog') ||
    to.path.startsWith('/licence/') ||
    to.meta.layout === 'marketing'

  const authCookie = useCookie('auth_token', { path: '/' })
  if (to.query.auth) {
    authCookie.value = String(to.query.auth)
  }

  const token = authCookie.value || (import.meta.client ? localStorage.getItem('token') : null)

  if (isPublicRoute) {
    // If already logged in and visiting login or signup, redirect to customer account
    if ((to.path === '/login' || to.path === '/signup') && token && !to.query.force) {
      return navigateTo('/account')
    }
    return
  }

  // Protected LIS and Customer Account screens
  if (!token) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }
})
