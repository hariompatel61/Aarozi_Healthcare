<script setup lang="ts">
definePageMeta({ layout: 'public' })
useSeoMeta({ title: 'Customer portal login | Aarozi Healthcare', description: 'Sign in to the Aarozi Healthcare customer portal.' })
const form = reactive({ tenant: '', username: '', password: '' })
const errorMessage = ref('')
const busy = ref(false)
const api = useApi()
async function login() {
  errorMessage.value = ''
  busy.value = true
  try {
    const result = await api.post<any>('/auth/login', { tenant_id_or_code: form.tenant, username: form.username, password: form.password })
    if (!result?.access_token) throw new Error('The server did not return a valid session.')
    if (import.meta.client) localStorage.setItem('token', result.access_token)
    await navigateTo('/customer/dashboard')
  } catch {
    errorMessage.value = 'Sign-in failed. Check your laboratory code and credentials, or contact your administrator.'
  } finally { busy.value = false }
}
</script>
<template><div class="mx-auto max-w-xl px-4 py-20 sm:px-6"><form class="rounded-3xl border border-slate-200 p-8 shadow-sm" @submit.prevent="login"><p class="text-xs font-bold uppercase tracking-[.2em] text-teal-700">Customer portal</p><h1 class="mt-3 text-3xl font-black">Welcome back.</h1><p class="mt-3 text-sm leading-6 text-slate-600">Sign in with the laboratory code and user credentials issued by your administrator.</p><label class="mt-7 grid gap-2 text-sm font-semibold">Laboratory code<input v-model="form.tenant" required autocomplete="organization" class="rounded-lg border border-slate-300 px-3 py-3 font-normal" /></label><label class="mt-4 grid gap-2 text-sm font-semibold">Username or email<input v-model="form.username" required autocomplete="username" class="rounded-lg border border-slate-300 px-3 py-3 font-normal" /></label><label class="mt-4 grid gap-2 text-sm font-semibold">Password<input v-model="form.password" required type="password" autocomplete="current-password" class="rounded-lg border border-slate-300 px-3 py-3 font-normal" /></label><p v-if="errorMessage" role="alert" class="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{{ errorMessage }}</p><button :disabled="busy" class="mt-6 w-full rounded-xl bg-teal-700 px-5 py-3 font-bold text-white disabled:opacity-50">{{ busy ? 'Signing in…' : 'Sign in securely' }}</button><p class="mt-5 text-xs leading-5 text-slate-500">This login uses the configured API. There is no offline demo-token bypass on this page.</p></form></div></template>
