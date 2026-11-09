<script setup lang="ts">
import { ref } from 'vue'
import { useToast } from '~/composables/useToast'

definePageMeta({ layout: false })

const { success, error } = useToast()
const api = useApi()
const tenantCode = ref('')
const username = ref('')
const password = ref('')
const selectedStation = ref('Lab Admin Workstation')
const loading = ref(false)

const workstations = [
  'Lab Admin Workstation',
  'Phlebotomy & Sample Reception',
  'Automated Analyzer Bench',
  'Pathologist Approval Desk',
  'Front-Office Cashier Counter',
  'Blood Bank Cold-Chain Desk',
]

async function handleLogin() {
  loading.value = true
  try {
    const res: any = await api.post('/auth/login', {
      tenant_id_or_code: tenantCode.value.trim(),
      username: username.value.trim(),
      password: password.value,
    })
    if (!res?.access_token) {
      throw new Error('Authentication service did not return a session token.')
    }

    localStorage.setItem('token', res.access_token)
    localStorage.setItem('aarozi_user', JSON.stringify({
      username: res.username || username.value,
      tenant_id: res.tenant_id,
      station: selectedStation.value,
    }))

    success('Authentication successful.')
    await navigateTo('/dashboard')
  } catch {
    error('Sign-in failed. Check your laboratory code and credentials, and confirm the local server is available.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-[#0c1322] flex flex-col justify-center items-center p-4 selection:bg-blue-600 selection:text-white font-sans text-slate-200">
    <div class="mb-6 rounded-full border border-slate-800 bg-slate-900/80 px-4 py-2 text-xs text-slate-300">
      Aarozi Healthcare · Local Laboratory Workstation
    </div>
    <div class="w-full max-w-md overflow-hidden rounded-2xl border border-slate-100 bg-white text-slate-900 shadow-2xl">
      <div class="border-b border-slate-100 bg-slate-50 p-6 text-center">
        <div class="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-teal-700 text-xl font-black text-white">A</div>
        <h1 class="text-xl font-bold tracking-tight">Aarozi Healthcare</h1>
        <p class="mt-1 text-xs text-slate-500">Laboratory Information System · Workstation sign-in</p>
      </div>
      <form class="space-y-4 p-6" @submit.prevent="handleLogin">
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-700">Laboratory code</label>
          <input v-model="tenantCode" type="text" required autocomplete="organization" class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm focus:border-teal-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-600/20" placeholder="Enter your laboratory code" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-700">Assigned workstation</label>
          <select v-model="selectedStation" class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-600/20">
            <option v-for="station in workstations" :key="station" :value="station">{{ station }}</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-700">Staff username / email</label>
          <input v-model="username" type="text" required autocomplete="username" class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm focus:border-teal-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-600/20" placeholder="Your assigned username" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-slate-700">Password</label>
          <input v-model="password" type="password" required autocomplete="current-password" class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm focus:border-teal-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-600/20" placeholder="Enter your password" />
        </div>
        <button type="submit" :disabled="loading" class="flex w-full items-center justify-center rounded-lg bg-teal-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50">
          {{ loading ? 'Authenticating…' : 'Authenticate & open workstation' }}
        </button>
        <p class="text-center text-xs leading-5 text-slate-500">Sign-in requires a reachable local Aarozi API and valid laboratory credentials. Demo credentials are not prefilled and no simulated session is created.</p>
      </form>
    </div>
    <p class="mt-6 text-center text-xs text-slate-500">© {{ new Date().getFullYear() }} Aarozi Healthcare</p>
  </div>
</template>
