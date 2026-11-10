<script setup lang="ts">
import { ref } from 'vue'
import Button from '~/components/ui/Button.vue'
import Input from '~/components/ui/Input.vue'
import Icon from '~/components/ui/Icon.vue'
import { useCustomerAuth } from '~/composables/useCustomerAuth'
import { useToast } from '~/composables/useToast'

definePageMeta({
  layout: 'auth',
})

const customerAuth = useCustomerAuth()
const { success, error } = useToast()

const form = ref({
  labName: '',
  doctorName: '',
  email: '',
  phone: '',
  city: '',
  gstin: '',
})

const loading = ref(false)

async function handleRegister() {
  if (!form.value.labName || !form.value.email || !form.value.phone) return
  loading.value = true
  try {
    await customerAuth.sendOtp(form.value.email)
    success('Account Registered', 'Verification OTP sent to your email.')
    await navigateTo('/login')
  } catch (err: any) {
    error('Registration Failed', err.message || 'Could not register account')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden text-left text-slate-900 dark:text-slate-100">
    <div class="p-6 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800 text-center">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-teal-600 text-white font-bold text-xl mb-3 shadow-md">
        AH
      </div>
      <h1 class="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Register Your Laboratory</h1>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Create an account to purchase licences, manage downloads & invoices</p>
    </div>

    <form class="p-6 space-y-4" @submit.prevent="handleRegister">
      <Input
        v-model="form.labName"
        label="Laboratory / Diagnostic Facility Name *"
        placeholder="e.g. Metro Diagnostic Centre"
        required
      />

      <Input
        v-model="form.doctorName"
        label="Pathologist / Medical Director Name *"
        placeholder="e.g. Dr. K. S. Murthy"
        required
      />

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Input
          v-model="form.email"
          label="Email Address *"
          type="email"
          placeholder="e.g. info@metrodiagnostics.in"
          required
        />
        <Input
          v-model="form.phone"
          label="Mobile / WhatsApp Number *"
          type="tel"
          placeholder="e.g. 9876543210"
          required
        />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Input
          v-model="form.city"
          label="City / State"
          placeholder="e.g. Pune, Maharashtra"
        />
        <Input
          v-model="form.gstin"
          label="GSTIN (Optional)"
          placeholder="e.g. 27ABCDE1234F1Z5"
          monospace
        />
      </div>

      <div class="pt-2 space-y-2">
        <Button
          type="submit"
          variant="primary"
          size="md"
          full-width
          :loading="loading"
        >
          Create Customer Account & Continue
        </Button>

        <p class="text-center text-xs text-slate-500 pt-2">
          Already have an account?
          <NuxtLink to="/login" class="text-teal-600 font-bold hover:underline">
            Sign in here
          </NuxtLink>
        </p>
      </div>
    </form>

    <div class="px-6 py-3 bg-slate-50 dark:bg-slate-800/40 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
      <span class="flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-teal-500" />
        Data Safety Guarantee
      </span>
      <span>100% Offline Clinical Records</span>
    </div>
  </div>
</template>
