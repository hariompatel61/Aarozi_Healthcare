<template>
  <!-- Each page selects its own layout through definePageMeta.
       Public marketing routes use layouts/public.vue; LIS routes retain
       layouts/default.vue; the local workstation login uses layout: false.
       Changes under apps/web are built by GitHub CI and deployed by Cloudflare Pages. -->
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
