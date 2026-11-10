<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '~/composables/useToast'
import { useAuth } from '~/composables/useAuth'
import Button from '~/components/ui/Button.vue'
import Input from '~/components/ui/Input.vue'

definePageMeta({
  layout: 'auth',
})

const router = useRouter()
const { success, error } = useToast()
const { login } = useAuth()

const form = ref({
  fullName: '',
  labName: '',
  email: '',
  phone: '',
  password: '',
})

const loading = ref(false)

async function handleSignup() {
  if (!form.value.fullName || !form.value.email || !form.value.password) return
  loading.value = true

  try {
    const result = await login(form.value.email, form.value.password)
    success('Account Created', `Welcome to Aarozi Healthcare, ${form.value.fullName}!`)
    await router.push(result.redirectPath || '/account')
  } catch (err: any) {
    error('Signup Failed', err.message || 'Could not complete registration.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-white dark:bg-[#15182a] rounded-2xl shadow-xl border border-[#ede9f7] dark:border-[#23273e] p-8 sm:p-10 space-y-6 transition-colors">
    <!-- Header -->
    <div class="space-y-1.5 text-center sm:text-left">
      <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Create an Account</h1>
      <p class="text-xs text-slate-600 dark:text-slate-300 font-medium">Get started with Aarozi Healthcare</p>
    </div>

    <!-- Registration Form -->
    <form class="space-y-4" @submit.prevent="handleSignup">
      <Input
        v-model="form.fullName"
        label="Full Name"
        placeholder="e.g. Dr. Ramesh Kumar"
        required
        prefix-icon="user"
      />

      <Input
        v-model="form.labName"
        label="Diagnostic Centre / Laboratory Name"
        placeholder="e.g. Apex Diagnostics"
        prefix-icon="heart"
      />

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Input
          v-model="form.email"
          label="Email Address"
          type="email"
          placeholder="e.g. doctor@example.com"
          required
          prefix-icon="mail"
        />

        <Input
          v-model="form.phone"
          label="Phone / Mobile"
          type="tel"
          placeholder="e.g. 9876543210"
          prefix-icon="phone"
        />
      </div>

      <Input
        v-model="form.password"
        label="Create Password"
        type="password"
        placeholder="••••••••"
        required
        prefix-icon="lock"
      />

      <div class="pt-2">
        <Button
          type="submit"
          variant="primary"
          size="md"
          full-width
          :loading="loading"
        >
          Create Account
        </Button>
      </div>
    </form>

    <!-- Footer Links -->
    <div class="pt-4 border-t border-[#ede9f7] dark:border-[#23273e] text-center text-xs text-slate-600 dark:text-slate-300">
      <span>Already have an account? </span>
      <NuxtLink to="/login" class="text-[#2576d2] dark:text-[#90ccf9] font-bold hover:underline">
        Sign in
      </NuxtLink>
    </div>
  </div>
</template>
