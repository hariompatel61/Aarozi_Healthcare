export default defineNuxtRouteMiddleware((to) => {
  // 1. Super Admin Authentication Isolation
  const adminTokenCookie = useCookie('aarozi_admin_token', { path: '/' })
  const adminToken = (!to.query.logged_out && !to.query.force)
    ? (adminTokenCookie.value || (import.meta.client ? localStorage.getItem('aarozi_admin_token') : null))
    : null

  // Admin Login route
  if (to.path === '/admin/login') {
    if (adminToken && !to.query.force && !to.query.logged_out) {
      return navigateTo('/admin/platform')
    }
    return
  }

  // Protected Super Admin Platform screens
  if (to.path === '/admin/platform' || to.path.startsWith('/admin/platform/')) {
    if (!adminToken) {
      return navigateTo(`/admin/login?redirect=${encodeURIComponent(to.fullPath)}`)
    }
    return
  }

  // 2. Public route prefixes that do not require authentication
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
  const customerCookie = useCookie('aarozi_customer_token', { path: '/' })

  if (to.query.logged_out || to.query.force) {
    authCookie.value = null
    customerCookie.value = null
    adminTokenCookie.value = null
    if (import.meta.client) {
      localStorage.removeItem('token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('aarozi_user')
      localStorage.removeItem('aarozi_customer_token')
      localStorage.removeItem('aarozi_customer_email')
      localStorage.removeItem('aarozi_admin_token')
      localStorage.removeItem('aarozi_admin_email')
    }
  }

  if (to.query.auth) {
    authCookie.value = String(to.query.auth)
  }

  const token = (!to.query.logged_out && !to.query.force)
    ? (authCookie.value || customerCookie.value || (import.meta.client ? localStorage.getItem('token') : null))
    : null

  if (isPublicRoute) {
    // If already logged in and visiting lab login or signup, redirect to customer account
    if ((to.path === '/login' || to.path === '/signup') && token && !to.query.force && !to.query.logged_out) {
      return navigateTo('/account')
    }
    return
  }

  // 3. Protected LIS and Customer Account screens
  if (!token) {
    return navigateTo(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  }
})
