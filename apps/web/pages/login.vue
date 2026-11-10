<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '~/composables/useToast'
import { useAuth } from '~/composables/useAuth'
import Button from '~/components/ui/Button.vue'
import Input from '~/components/ui/Input.vue'
import Icon from '~/components/ui/Icon.vue'

definePageMeta({
  layout: 'auth',
})

const route = useRoute()
const router = useRouter()
const { success, error } = useToast()
const { login } = useAuth()

const email = ref('')
const password = ref('')
const rememberMe = ref(true)
const loading = ref(false)

async function handleLogin() {
  const userEmail = email.value.trim()
  if (!userEmail || !password.value) return
  loading.value = true

  try {
    const result = await login(userEmail, password.value)
    success('Login Successful', `Welcome back to Aarozi Healthcare`)

    const redirectPath = (route.query.redirect as string) || result.redirectPath
    await router.push(redirectPath)
  } catch (err: any) {
    error('Login Failed', err.message || 'Invalid email or password. Please try again.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-white dark:bg-[#15182a] rounded-2xl shadow-xl border border-[#ede9f7] dark:border-[#23273e] p-8 sm:p-10 space-y-6 transition-colors">
    <!-- Header -->
    <div class="space-y-1.5 text-center sm:text-left">
      <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Sign In</h1>
      <p class="text-xs text-slate-600 dark:text-slate-300 font-medium">Enter your email and password to access your account</p>
    </div>

    <!-- Login Form -->
    <form class="space-y-4" @submit.prevent="handleLogin">
      <Input
        v-model="email"
        label="Email Address"
        type="email"
        placeholder="e.g. doctor@example.com"
        required
        prefix-icon="mail"
      />

      <div class="space-y-1">
        <Input
          v-model="password"
          label="Password"
          type="password"
          placeholder="••••••••"
          required
          prefix-icon="lock"
        />
        <div class="flex items-center justify-between text-xs pt-1">
          <label class="flex items-center space-x-2 text-slate-700 dark:text-slate-300 cursor-pointer select-none">
            <input
              v-model="rememberMe"
              type="checkbox"
              class="w-3.5 h-3.5 rounded text-[#2576d2] focus:ring-[#3b93ee] border-slate-300 dark:border-slate-700 dark:bg-slate-800"
            />
            <span>Remember me</span>
          </label>
          <NuxtLink to="/forgot-password" class="text-[#2576d2] dark:text-[#90ccf9] hover:underline font-semibold">
            Forgot password?
          </NuxtLink>
        </div>
      </div>

      <div class="pt-2">
        <Button
          type="submit"
          variant="primary"
          size="md"
          full-width
          :loading="loading"
        >
          Sign In
        </Button>
      </div>
    </form>

    <!-- Footer Links -->
    <div class="pt-4 border-t border-[#ede9f7] dark:border-[#23273e] text-center text-xs text-slate-600 dark:text-slate-300">
      <span>Don't have an account? </span>
      <NuxtLink to="/signup" class="text-[#2576d2] dark:text-[#90ccf9] font-bold hover:underline">
        Sign up
      </NuxtLink>
    </div>
  </div>
</template>
