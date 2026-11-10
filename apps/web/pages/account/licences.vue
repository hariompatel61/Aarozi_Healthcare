<script setup lang="ts">
import { ref } from 'vue'
import { useCustomerAuth } from '~/composables/useCustomerAuth'
import { useToast } from '~/composables/useToast'
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'

definePageMeta({
  layout: 'customer',
})

const { licenses, downloadLicenseFile } = useCustomerAuth()
const { success, error } = useToast()

const showReKeyModal = ref(false)
const selectedLicId = ref('')
const newMachineId = ref('')
const reKeyReason = ref('Replacement Motherboard / Hardware Failure')

function openReKey(licId: string) {
  selectedLicId.value = licId
  showReKeyModal.value = true
}

function handleReKeySubmit() {
  if (!newMachineId.value.trim()) return
  const lic = licenses.value.find(l => l.license_id === selectedLicId.value)
  if (lic) {
    lic.installation_id = newMachineId.value.trim()
    success('Hardware Re-Keyed', `New machine bound: ${newMachineId.value}. Download your updated .lic file.`)
    showReKeyModal.value = false
    newMachineId.value = ''
  }
}
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black text-slate-900 dark:text-white">Software Licences</h1>
        <p class="text-xs text-slate-500">View cryptographic license files and manage Master PC hardware bindings</p>
      </div>

      <NuxtLink to="/pricing">
        <Button variant="primary" size="sm">
          <template #icon-left><Icon name="plus" size="xs" /></template>
          Purchase Additional Machine Licence
        </Button>
      </NuxtLink>
    </div>

    <!-- Licences List -->
    <div class="space-y-4">
      <div
        v-for="lic in licenses"
        :key="lic.license_id"
        class="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-sm space-y-6"
      >
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div class="space-y-1">
            <div class="flex items-center space-x-2">
              <span class="font-mono text-base font-bold text-slate-900 dark:text-white">{{ lic.license_id }}</span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                {{ lic.status }}
              </span>
            </div>
            <p class="text-xs text-slate-500">Order Ref: {{ lic.order_id }} &bull; Issued on {{ lic.issued_at.slice(0, 10) }}</p>
          </div>

          <div class="flex items-center space-x-2">
            <Button variant="secondary" size="xs" @click="openReKey(lic.license_id)">
              <template #icon-left><Icon name="refresh" size="xs" /></template>
              Hardware Transfer (Re-Key)
            </Button>
            <Button variant="primary" size="xs" @click="downloadLicenseFile(lic.license_id)">
              <template #icon-left><Icon name="download" size="xs" /></template>
              Download .lic File
            </Button>
          </div>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div><span class="text-slate-400 block">Plan Tier</span><strong class="text-slate-900 dark:text-white">{{ lic.plan_code }}</strong></div>
          <div><span class="text-slate-400 block">Bound Machine ID</span><strong class="font-mono text-teal-600 dark:text-teal-400">{{ lic.installation_id || 'Unbound' }}</strong></div>
          <div><span class="text-slate-400 block">Valid From</span><span class="text-slate-700 dark:text-slate-300">{{ lic.valid_from.slice(0, 10) }}</span></div>
          <div><span class="text-slate-400 block">Expiry Date</span><span class="text-slate-700 dark:text-slate-300">{{ lic.valid_to.slice(0, 10) }}</span></div>
        </div>

        <!-- Local Activation Steps Hint -->
        <div class="rounded-2xl bg-slate-50 dark:bg-slate-800/40 p-4 border border-slate-200/80 dark:border-slate-800 flex items-start space-x-3 text-xs text-slate-600 dark:text-slate-400">
          <Icon name="info" size="xs" class="text-teal-600 shrink-0 mt-0.5" />
          <p>
            To activate: Save the downloaded <code class="text-teal-600 font-mono font-bold">aarozi_license_{{ lic.license_id }}.lic</code> file on your Master PC. Open Aarozi LIS desktop software, navigate to <strong class="text-slate-800 dark:text-slate-200">Settings > Licensing > Upload Licence File</strong>.
          </p>
        </div>
      </div>
    </div>

    <!-- Re-Key Modal -->
    <div
      v-if="showReKeyModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm"
      @click.self="showReKeyModal = false"
    >
      <div class="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 space-y-4">
        <h3 class="text-base font-bold text-slate-900 dark:text-white">Hardware Re-Keying</h3>
        <p class="text-xs text-slate-500">
          Transfer your license to a replacement Master PC. The previous hardware ID will be decommissioned.
        </p>

        <div class="space-y-3 text-xs">
          <div>
            <label class="font-semibold text-slate-700 dark:text-slate-300 block mb-1">New Master PC Machine ID *</label>
            <input
              v-model="newMachineId"
              type="text"
              placeholder="e.g. HW-90A1-4B22-C890"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 font-mono text-xs focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <div>
            <label class="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Reason for Hardware Move</label>
            <select
              v-model="reKeyReason"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs focus:ring-2 focus:ring-teal-500"
            >
              <option>Replacement Motherboard / Hardware Failure</option>
              <option>Upgraded to High-Performance Desktop</option>
              <option>Relocated Server to New Branch</option>
            </select>
          </div>
        </div>

        <div class="flex justify-end space-x-2 pt-2">
          <Button variant="secondary" size="xs" @click="showReKeyModal = false">Cancel</Button>
          <Button variant="primary" size="xs" @click="handleReKeySubmit">Update Machine & Re-Issue</Button>
        </div>
      </div>
    </div>
  </div>
</template>
