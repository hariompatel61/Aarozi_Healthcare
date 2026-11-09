<script setup lang="ts">
const links = [
  { label: 'Product', to: '/product' },
  { label: 'Pricing', to: '/pricing' },
  { label: 'Setup guide', to: '/setup' },
  { label: 'Downloads', to: '/download' },
]
</script>

<template>
  <div class="min-h-screen bg-white text-slate-900">
    <header class="sticky top-0 z-40 border-b border-slate-200/80 bg-white/95 backdrop-blur">
      <div class="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <NuxtLink to="/" class="flex items-center gap-3" aria-label="Aarozi Healthcare home">
          <span class="grid h-10 w-10 place-items-center rounded-xl bg-teal-700 text-lg font-black text-white">A</span>
          <span><strong class="block text-base leading-tight">Aarozi Healthcare</strong><small class="text-xs text-slate-500">Laboratory Information System</small></span>
        </NuxtLink>
        <nav class="hidden items-center gap-6 text-sm font-medium text-slate-600 md:flex">
          <NuxtLink v-for="link in links" :key="link.to" :to="link.to" class="hover:text-teal-700">{{ link.label }}</NuxtLink>
        </nav>
        <div class="flex items-center gap-2">
          <NuxtLink to="/portal/login" class="hidden rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 sm:inline-flex">Login</NuxtLink>
          <NuxtLink to="/business-registration" class="rounded-lg bg-teal-700 px-3 py-2 text-sm font-semibold text-white hover:bg-teal-800">Register your lab</NuxtLink>
        </div>
      </div>
    </header>
    <main><slot /></main>
    <footer class="border-t border-slate-200 bg-slate-950 text-slate-300">
      <div class="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
        <div class="sm:col-span-2"><div class="font-bold text-white">Aarozi Healthcare</div><p class="mt-3 max-w-md text-sm leading-6 text-slate-400">Laboratory software designed around local operations, clear workflows and customer-controlled data.</p></div>
        <div><div class="font-semibold text-white">Explore</div><div class="mt-3 grid gap-2 text-sm"><NuxtLink to="/product">Product information</NuxtLink><NuxtLink to="/pricing">Plans & pricing</NuxtLink><NuxtLink to="/setup">Installation guide</NuxtLink><NuxtLink to="/download">Software downloads</NuxtLink></div></div>
        <div><div class="font-semibold text-white">Account & help</div><div class="mt-3 grid gap-2 text-sm"><NuxtLink to="/signup">Create account</NuxtLink><NuxtLink to="/portal/login">Customer login</NuxtLink><NuxtLink to="/business-registration">Lab registration</NuxtLink><NuxtLink to="/support">Support</NuxtLink><NuxtLink to="/privacy">Privacy information</NuxtLink></div></div>
      </div>
      <div class="border-t border-slate-800 px-4 py-4 text-center text-xs text-slate-500">© {{ new Date().getFullYear() }} Aarozi Healthcare. Product website: labs.aarozi.in</div>
    </footer>
  </div>
</template>
