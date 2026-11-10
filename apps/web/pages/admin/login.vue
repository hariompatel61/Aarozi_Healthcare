<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '~/composables/useToast'
import { useAdminAuth } from '~/composables/useAdminAuth'
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'
import Input from '~/components/ui/Input.vue'

definePageMeta({
  layout: false, // Self-contained standalone layout
})

const router = useRouter()
const route = useRoute()
const { success, error } = useToast()
const { login, isAuthenticated } = useAdminAuth()

const email = ref('')
const password = ref('')
const loading = ref(false)

async function handleAdminLogin() {
  if (!email.value.trim() || !password.value) return
  loading.value = true

  try {
    await login(email.value, password.value)
    success('Authentication Successful', 'Welcome to Aarozi Platform Administration Console.')
    const redirect = (route.query.redirect as string) || '/admin/platform'
    await router.push(redirect)
  } catch (err: any) {
    error('Authentication Failed', err.message || 'Invalid Super Admin credentials.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen w-full bg-[#0a0d18] text-slate-100 flex flex-col justify-between items-center p-4 sm:p-6 selection:bg-[#2576d2] selection:text-white relative overflow-hidden">
    <!-- Background Ambient Glow -->
    <div class="absolute -top-40 -left-40 w-96 h-96 bg-[#2576d2]/15 rounded-full blur-3xl pointer-events-none" />
    <div class="absolute -bottom-40 -right-40 w-96 h-96 bg-[#fb8f68]/10 rounded-full blur-3xl pointer-events-none" />

    <!-- Top Branding Header -->
    <header class="w-full max-w-4xl py-4 flex items-center justify-between z-10 shrink-0">
      <NuxtLink to="/" class="flex items-center space-x-2.5 group">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-[#2576d2] to-[#5eaef5] text-white flex items-center justify-center font-black text-sm shadow-md">
          AH
        </div>
        <div>
          <span class="font-bold text-base tracking-tight text-white block leading-tight">
            Aarozi Healthcare
          </span>
          <span class="text-[10px] text-slate-400 font-mono tracking-wider uppercase block">
            Platform Vendor Console
          </span>
        </div>
      </NuxtLink>

      <NuxtLink
        to="/"
        class="text-xs font-semibold text-slate-400 hover:text-white transition-colors flex items-center space-x-1"
      >
        <span>&larr; Back to Public Portal</span>
      </NuxtLink>
    </header>

    <!-- Centered High-Security Authentication Box -->
    <main class="w-full max-w-md my-auto py-8 z-10">
      <div class="bg-[#121629] rounded-2xl shadow-2xl border border-slate-800 p-8 sm:p-10 space-y-6 relative overflow-hidden">
        <!-- Top Accent Bar -->
        <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#2576d2] via-[#5eaef5] to-[#fb8f68]" />

        <!-- Security Header -->
        <div class="space-y-2 text-center">
          <div class="w-12 h-12 rounded-2xl bg-[#1b223c] border border-slate-700 mx-auto flex items-center justify-center text-[#5eaef5] shadow-inner mb-3">
            <Icon name="shield-check" size="md" />
          </div>
          <h1 class="text-2xl font-bold tracking-tight text-white">Super Admin Access</h1>
          <p class="text-xs text-slate-400 font-medium">
            Restricted console for multi-tenant plans, license issuance, and platform operations.
          </p>
        </div>

        <!-- Credentials Form -->
        <form class="space-y-4" @submit.prevent="handleAdminLogin">
          <div>
            <label class="block text-xs font-bold text-slate-300 mb-1">Super Admin Email</label>
            <div class="relative">
              <input
                v-model="email"
                type="email"
                required
                autocomplete="email"
                placeholder="superadmin@aarozi.in"
                class="w-full px-3.5 py-2.5 rounded-lg text-xs bg-[#0b0e1b] text-white border border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#2576d2] focus:border-transparent transition-all placeholder:text-slate-600"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-300 mb-1">Master Password</label>
            <div class="relative">
              <input
                v-model="password"
                type="password"
                required
                autocomplete="current-password"
                placeholder="••••••••••••"
                class="w-full px-3.5 py-2.5 rounded-lg text-xs bg-[#0b0e1b] text-white border border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#2576d2] focus:border-transparent transition-all placeholder:text-slate-600 font-mono"
              />
            </div>
          </div>

          <!-- Security Notice -->
          <div class="p-3 rounded-lg bg-[#0b0e1b]/80 border border-slate-800 text-[11px] text-slate-400 space-y-1">
            <div class="flex items-center space-x-1.5 text-slate-300 font-semibold">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Restricted Session Protocol</span>
            </div>
            <p class="text-[10px] text-slate-500 leading-relaxed">
              Every login attempt is cryptographically audited. Unauthenticated sessions expire automatically after 12 hours.
            </p>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 px-4 rounded-lg bg-gradient-to-r from-[#2576d2] to-[#1c5fae] hover:from-[#1c5fae] hover:to-[#174e8f] text-white font-bold text-xs shadow-lg shadow-[#2576d2]/25 focus:outline-none focus:ring-2 focus:ring-[#5eaef5] transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center space-x-2"
          >
            <Icon v-if="loading" name="refresh" size="xs" class="animate-spin" />
            <Icon v-else name="lock" size="xs" />
            <span>{{ loading ? 'Verifying Credentials...' : 'Authenticate & Enter Console' }}</span>
          </button>
        </form>

        <!-- Lab Owner Redirect -->
        <div class="pt-4 border-t border-slate-800/80 text-center text-xs text-slate-500">
          <span>Are you a Pathology Lab Owner? </span>
          <NuxtLink to="/login" class="text-[#5eaef5] hover:underline font-semibold">
            Lab Staff &amp; Customer Login &rarr;
          </NuxtLink>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="w-full max-w-4xl py-4 flex items-center justify-between text-xs text-slate-500 border-t border-slate-900 z-10 shrink-0">
      <span>&copy; 2026 Aarozi Healthcare Platform Architecture. All rights reserved.</span>
      <span class="font-mono text-[11px] text-slate-600">v2.4.0-cloud</span>
    </footer>
  </div>
</template>
