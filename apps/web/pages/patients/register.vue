<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between border-b border-gray-200 pb-4">
      <div>
        <div class="flex items-center space-x-2 text-xs text-gray-500 mb-1">
          <NuxtLink to="/dashboard" class="hover:underline">Dashboard</NuxtLink>
          <span>/</span>
          <NuxtLink to="/patients" class="hover:underline">Patients</NuxtLink>
          <span>/</span>
          <span class="text-gray-900 font-medium">New Registration</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 tracking-tight">Patient Registration</h1>
        <p class="text-sm text-gray-500">Keyboard-first rapid intake workflow (Alt+S to save, Esc to clear)</p>
      </div>

      <div class="flex items-center space-x-3">
        <span v-if="uiState === 'loading'" class="text-sm text-blue-600">Saving...</span>
        <button
          type="button"
          class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          @click="resetForm"
        >
          Reset (Esc)
        </button>
        <button
          type="button"
          class="px-5 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 shadow-sm"
          :disabled="uiState === 'loading'"
          @click="submitRegistration"
        >
          Save &amp; Continue (Alt+S)
        </button>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="uiState === 'error'" class="p-4 rounded-md bg-red-50 border border-red-200">
      <h3 class="text-sm font-medium text-red-800">Registration Error</h3>
      <p class="mt-1 text-sm text-red-700">{{ errorMessage }}</p>
    </div>

    <!-- Permission Denied State -->
    <div v-if="uiState === 'permission_denied'" class="p-6 text-center bg-white rounded-lg border border-gray-200">
      <p class="text-sm text-gray-500">You do not have permission ('patient.create') to register patients.</p>
    </div>

    <!-- Main Registration Form -->
    <form
      v-else
      class="bg-white rounded-lg border border-gray-200 shadow-sm p-6 space-y-6"
      @keydown.alt.s.prevent="submitRegistration"
      @keydown.esc="resetForm"
      @submit.prevent="submitRegistration"
    >
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1" for="first_name">
            First Name <span class="text-red-500">*</span>
          </label>
          <input
            id="first_name"
            ref="firstNameInput"
            v-model="form.first_name"
            type="text"
            required
            class="w-full h-9 px-3 rounded border border-gray-300 text-sm focus:border-blue-500"
            placeholder="e.g. Fatima"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1" for="last_name">
            Last Name / Father Name
          </label>
          <input
            id="last_name"
            v-model="form.last_name"
            type="text"
            class="w-full h-9 px-3 rounded border border-gray-300 text-sm focus:border-blue-500"
            placeholder="e.g. Zahra"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1" for="sex">
            Biological Sex <span class="text-red-500">*</span>
          </label>
          <select
            id="sex"
            v-model="form.sex"
            required
            class="w-full h-9 px-3 rounded border border-gray-300 text-sm focus:border-blue-500"
          >
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1" for="mobile">
            Mobile Phone <span class="text-red-500">*</span>
          </label>
          <input
            id="mobile"
            v-model="form.mobile"
            type="tel"
            required
            class="w-full h-9 px-3 rounded border border-gray-300 text-sm focus:border-blue-500"
            placeholder="+92 300 1234567"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1" for="id_type">
            Identifier Type
          </label>
          <select
            id="id_type"
            v-model="form.primary_id_type"
            class="w-full h-9 px-3 rounded border border-gray-300 text-sm focus:border-blue-500"
          >
            <option value="CNIC">National ID / CNIC</option>
            <option value="PASSPORT">Passport</option>
            <option value="BARCODE">Barcode Scan</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1" for="id_val">
            Identifier Value / Barcode
          </label>
          <input
            id="id_val"
            v-model="form.primary_id_value"
            type="text"
            class="w-full h-9 px-3 rounded border border-gray-300 text-sm focus:border-blue-500"
            placeholder="Scan or enter ID"
          />
        </div>
      </div>

      <div class="pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
        <div class="flex items-center space-x-4">
          <span><kbd class="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded font-mono">Tab</kbd> Next Field</span>
          <span><kbd class="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded font-mono">Alt+S</kbd> Save</span>
          <span><kbd class="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded font-mono">Esc</kbd> Reset</span>
        </div>
        <span class="text-gray-400">Multi-tenant boundary checked server-side</span>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

const firstNameInput = ref<HTMLInputElement | null>(null)
const uiState = ref<'ready' | 'loading' | 'error' | 'permission_denied'>('ready')
const errorMessage = ref('')

const form = reactive({
  first_name: '',
  last_name: '',
  sex: 'male',
  mobile: '',
  primary_id_type: 'CNIC',
  primary_id_value: '',
})

onMounted(() => {
  firstNameInput.value?.focus()
})

function resetForm() {
  form.first_name = ''
  form.last_name = ''
  form.sex = 'male'
  form.mobile = ''
  form.primary_id_value = ''
  errorMessage.value = ''
  uiState.value = 'ready'
  firstNameInput.value?.focus()
}

async function submitRegistration() {
  if (!form.first_name || !form.mobile) {
    errorMessage.value = 'Please provide First Name and Mobile Phone'
    uiState.value = 'error'
    return
  }

  uiState.value = 'loading'
  errorMessage.value = ''

  try {
    resetForm()
  } catch (err: any) {
    errorMessage.value = err.message || 'Failed to register patient'
    uiState.value = 'error'
  }
}
</script>
