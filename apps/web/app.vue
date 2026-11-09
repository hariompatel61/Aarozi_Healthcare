<template>
  <!-- Each page selects its own layout through definePageMeta.
       Public marketing routes use layouts/public.vue; LIS routes retain
       layouts/default.vue; the local workstation login uses layout: false. -->
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
