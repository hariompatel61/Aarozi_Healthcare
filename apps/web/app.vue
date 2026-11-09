<script setup lang="ts">
const route = useRoute()

// Keep the marketing and customer-acquisition pages completely separate from
// the authenticated LIS workspace shell. Operational routes continue to use
// the default dashboard layout.
const publicRoutes = new Set([
  '/',
  '/product',
  '/faq',
  '/pricing',
  '/business-registration',
  '/signup',
  '/portal/login',
  '/setup',
  '/download',
  '/contact',
  '/support',
  '/privacy',
  '/terms',
])

const layoutName = computed(() => {
  const path = route.path.replace(/\/+$/, '') || '/'
  return publicRoutes.has(path) ? 'public' : 'default'
})
</script>

<template>
  <NuxtLayout :name="layoutName">
    <NuxtPage />
  </NuxtLayout>
</template>
