<template>
  <div class="space-y-6">
    <!-- Header & Breadcrumbs -->
    <div class="flex items-center justify-between border-b border-gray-200 pb-4">
      <div>
        <div class="flex items-center space-x-2 text-xs text-gray-500 mb-1">
          <NuxtLink to="/dashboard" class="hover:underline">Dashboard</NuxtLink>
          <span>/</span>
          <span class="text-gray-900 font-medium">Patients</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 tracking-tight">Patient Directory</h1>
        <p class="text-sm text-gray-500">Universal patient identity lookup across clinical and billing records</p>
      </div>

      <div>
        <NuxtLink
          to="/patients/register"
          class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          + New Patient (Alt+N)
        </NuxtLink>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="bg-white p-4 rounded-lg border border-gray-200 shadow-sm flex items-center space-x-3">
      <div class="flex-1 relative">
        <input
          v-model="searchQuery"
          type="text"
          class="w-full h-10 pl-10 pr-4 rounded-md border border-gray-300 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          placeholder="Search by UHID, Mobile number, Barcode or Patient Name..."
          @keydown.enter="handleSearch"
        />
        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
        </div>
      </div>
      <button
        type="button"
        class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-md"
        @click="handleSearch"
      >
        Search
      </button>
    </div>

    <!-- UI States: Loading, Empty, Permission Denied -->
    <div v-if="uiState === 'loading'" class="p-8 text-center bg-white rounded-lg border border-gray-200">
      <p class="text-sm text-gray-500">Searching records...</p>
    </div>

    <div v-else-if="uiState === 'permission_denied'" class="p-8 text-center bg-white rounded-lg border border-gray-200">
      <p class="text-sm text-gray-500">You do not have permission ('patient.view') to search patient records.</p>
    </div>

    <div v-else-if="uiState === 'empty'" class="p-8 text-center bg-white rounded-lg border border-gray-200">
      <p class="text-sm text-gray-500">No patient records found matching your query.</p>
    </div>

    <!-- Patient Directory Table -->
    <div v-else class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left font-semibold text-gray-700">UHID / Patient #</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-700">Full Name</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-700">Sex</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-700">Mobile</th>
            <th class="px-4 py-3 text-right font-semibold text-gray-700">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white">
          <tr v-for="patient in patients" :key="patient.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-mono font-medium text-blue-600">{{ patient.patient_no }}</td>
            <td class="px-4 py-3 font-medium text-gray-900">{{ patient.first_name }} {{ patient.last_name }}</td>
            <td class="px-4 py-3 text-gray-600 capitalize">{{ patient.sex }}</td>
            <td class="px-4 py-3 font-mono text-gray-600">{{ patient.mobile_normalized }}</td>
            <td class="px-4 py-3 text-right space-x-2">
              <NuxtLink :to="`/patients/${patient.patient_no}`" class="text-blue-600 hover:underline">View Profile</NuxtLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const searchQuery = ref('')
const uiState = ref<'ready' | 'loading' | 'empty' | 'permission_denied'>('ready')

const patients = ref([
  {
    id: '1',
    patient_no: 'UHID-10001',
    first_name: 'Fatima',
    last_name: 'Zahra',
    sex: 'female',
    mobile_normalized: '+923001234567',
  },
  {
    id: '2',
    patient_no: 'UHID-10002',
    first_name: 'Zahid',
    last_name: 'Khan',
    sex: 'male',
    mobile_normalized: '+923219876543',
  },
])

function handleSearch() {
  uiState.value = 'loading'
  setTimeout(() => {
    if (!searchQuery.value) {
      uiState.value = 'ready'
    } else {
      uiState.value = 'ready'
    }
  }, 200)
}
</script>
