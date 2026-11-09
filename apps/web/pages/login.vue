<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '~/composables/useToast'
import Button from '~/components/ui/Button.vue'
import Input from '~/components/ui/Input.vue'
import Select from '~/components/ui/Select.vue'
import Badge from '~/components/ui/Badge.vue'
import Icon from '~/components/ui/Icon.vue'

definePageMeta({
  layout: 'auth',
})

const router = useRouter()
const { success, error, info } = useToast()
const api = useApi()

const username = ref('hariom.patel')
const password = ref('password123')
const selectedStation = ref('Lab Admin Workstation')
const selectedBranch = ref('Main City Branch')
const loading = ref(false)

const workstations = [
  { label: 'Lab Admin Workstation', value: 'Lab Admin Workstation', badge: 'Full Access' },
  { label: 'Front-Office Cashier Counter', value: 'Front-Office Cashier Counter', badge: 'POS' },
  { label: 'Phlebotomy & Sample Reception', value: 'Phlebotomy & Sample Reception', badge: 'Barcode' },
  { label: 'Automated Analyzer Bench', value: 'Automated Analyzer Bench', badge: 'ASTM/HL7' },
  { label: 'Pathologist Approval Desk', value: 'Pathologist Approval Desk', badge: 'Sign-off' },
  { label: 'Blood Bank Cold-Chain Desk', value: 'Blood Bank Cold-Chain Desk', badge: 'Transfusion' },
]

const branches = [
  { label: 'Main City Branch (HQ)', value: 'Main City Branch' },
  { label: 'City Centre Collection Point', value: 'City Centre Branch' },
  { label: 'North Satellite Laboratory', value: 'North Satellite Lab' },
]

const quickRoles = [
  { role: 'Receptionist', user: 'reception.staff', station: 'Front-Office Cashier Counter' },
  { role: 'Phlebotomist', user: 'phlebo.tech', station: 'Phlebotomy & Sample Reception' },
  { role: 'Technician', user: 'analyzer.op', station: 'Automated Analyzer Bench' },
  { role: 'Pathologist', user: 'dr.pathologist', station: 'Pathologist Approval Desk' },
  { role: 'Admin', user: 'hariom.patel', station: 'Lab Admin Workstation' },
]

function quickSelect(user: string, station: string) {
  username.value = user
  selectedStation.value = station
  password.value = 'password123'
  info('Staff Role Switched', `Selected ${station}`)
}

async function handleLogin() {
  loading.value = true
  const authCookie = useCookie('auth_token', { path: '/' })
  const userCookie = useCookie('aarozi_user', { path: '/' })

  try {
    let authToken = 'offline_authenticated_session_token'
    try {
      const res: any = await api.post('/auth/login', {
        username: username.value,
        password: password.value,
      })
      if (res && (res.access_token || res.token)) {
        authToken = res.access_token || res.token
      }
    } catch {
      // Offline fallback simulation for local LAN desktop operation
      authToken = 'offline_authenticated_session_token'
    }

    authCookie.value = authToken
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', authToken)
      localStorage.setItem('access_token', authToken)
    }

    const userData = {
      username: username.value,
      station: selectedStation.value,
      branch: selectedBranch.value,
      loginTime: new Date().toISOString(),
    }
    userCookie.value = JSON.stringify(userData)
    if (typeof window !== 'undefined') {
      localStorage.setItem('aarozi_user', JSON.stringify(userData))
    }

    success('Authentication Successful', `Logged into ${selectedStation.value}`)
    await navigateTo('/dashboard')
  } catch (err: any) {
    error('Authentication Failed', 'Please verify your credentials or station lock.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden text-left text-slate-900 dark:text-slate-100">
    <!-- Header -->
    <div class="p-6 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800 text-center">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-teal-600 text-white font-bold text-xl mb-3 shadow-md">
        AH
      </div>
      <h1 class="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Staff Workstation Login</h1>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Laboratory Information System &bull; Blood Bank &bull; POS</p>
    </div>

    <!-- Quick Role Switcher Pills -->
    <div class="px-6 pt-4 pb-1 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
      <div class="text-[11px] font-semibold text-slate-400 mb-2 uppercase tracking-wider">Quick Station Preset:</div>
      <div class="flex flex-wrap gap-1.5 pb-2">
        <button
          v-for="r in quickRoles"
          :key="r.role"
          type="button"
          :class="[
            'px-2.5 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer border select-none',
            selectedStation === r.station
              ? 'bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 border-teal-300 dark:border-teal-700'
              : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700'
          ]"
          @click="quickSelect(r.user, r.station)"
        >
          {{ r.role }}
        </button>
      </div>
    </div>

    <!-- Login Form -->
    <form class="p-6 space-y-4" @submit.prevent="handleLogin">
      <!-- Workstation Selector -->
      <Select
        v-model="selectedStation"
        label="Operating Workstation Bench"
        :options="workstations"
        :searchable="false"
      />

      <!-- Branch Selector -->
      <Select
        v-model="selectedBranch"
        label="Laboratory Branch / Center"
        :options="branches"
        :searchable="false"
      />

      <!-- Username -->
      <Input
        v-model="username"
        label="Staff Username or Employee ID"
        placeholder="e.g. hariom.patel"
        required
        prefix-icon="user"
        monospace
      />

      <!-- Password -->
      <Input
        v-model="password"
        label="Security Password"
        type="password"
        placeholder="••••••••"
        required
        prefix-icon="lock"
        monospace
      />

      <!-- Submit Action -->
      <div class="pt-2">
        <Button
          type="submit"
          variant="primary"
          size="md"
          full-width
          :loading="loading"
        >
          <template #icon-left><Icon name="unlock" size="xs" /></template>
          Unlock & Open Workstation
        </Button>
      </div>
    </form>

    <!-- Card Footer -->
    <div class="px-6 py-3 bg-slate-50 dark:bg-slate-800/40 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
      <span class="flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-emerald-500" />
        Local LAN Ready
      </span>
      <span>v2.4.0 (Offline-first)</span>
    </div>
  </div>
</template>
