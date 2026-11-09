<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from '~/composables/useToast'

const api = useApi()
const { success, warning, error } = useToast()

const loading = ref(false)
const errorState = ref<string | null>(null)
const permission_denied = ref(false)

interface PermissionItem {
  id: string
  code: string
  module: string
  description: string
  risk_level: 'normal' | 'sensitive' | 'critical'
}

interface RoleItem {
  id: string
  name: string
  description: string
  is_system: boolean
  status: string
  permission_ids: string[]
}

const roles = ref<RoleItem[]>([
  {
    id: 'r-admin',
    name: 'Lab Administrator',
    description: 'Full administrative access to all clinical modules, settings and licenses',
    is_system: true,
    status: 'active',
    permission_ids: [
      'patient.register', 'order.create', 'sample.collect', 'sample.receive',
      'result.enter', 'result.verify', 'result.approve', 'report.release',
      'invoice.create', 'payment.record', 'donor.register', 'blood.issue', 'system.admin'
    ],
  },
  {
    id: 'r-path',
    name: 'Pathologist (MD)',
    description: 'Clinical evaluation, delta check approval and diagnostic sign-off',
    is_system: true,
    status: 'active',
    permission_ids: [
      'patient.register', 'sample.receive', 'result.enter', 'result.verify',
      'result.approve', 'report.release'
    ],
  },
  {
    id: 'r-phleb',
    name: 'Phlebotomist / Collector',
    description: 'Sample collection, barcode accessioning and specimen rejection',
    is_system: true,
    status: 'active',
    permission_ids: [
      'patient.register', 'order.create', 'sample.collect', 'sample.receive'
    ],
  },
  {
    id: 'r-cashier',
    name: 'Cashier & Front Office',
    description: 'Patient intake registration, invoice generation and POS receipts',
    is_system: false,
    status: 'active',
    permission_ids: [
      'patient.register', 'order.create', 'invoice.create', 'payment.record'
    ],
  },
])

const permissions = ref<PermissionItem[]>([
  { id: 'patient.register', code: 'patient.register', module: 'Registration', description: 'Intake new patients and edit demographics', risk_level: 'normal' },
  { id: 'order.create', code: 'order.create', module: 'Registration', description: 'Create lab test orders and requisition profiles', risk_level: 'normal' },
  { id: 'sample.collect', code: 'sample.collect', module: 'Pathology LIS', description: 'Phlebotomy blood draw & sample tube collection', risk_level: 'normal' },
  { id: 'sample.receive', code: 'sample.receive', module: 'Pathology LIS', description: 'Lab receipt and accession barcode scanning', risk_level: 'normal' },
  { id: 'result.enter', code: 'result.enter', module: 'Pathology LIS', description: 'Technician test result numerical entry', risk_level: 'normal' },
  { id: 'result.verify', code: 'result.verify', module: 'Pathology LIS', description: 'Senior technologist delta review and verification', risk_level: 'sensitive' },
  { id: 'result.approve', code: 'result.approve', module: 'Pathology LIS', description: 'Pathologist medical approval and digital signature', risk_level: 'critical' },
  { id: 'report.release', code: 'report.release', module: 'Reporting', description: 'Render, publish and dispatch patient diagnostic reports', risk_level: 'sensitive' },
  { id: 'invoice.create', code: 'invoice.create', module: 'Billing', description: 'Generate diagnostic bills and price discounts', risk_level: 'sensitive' },
  { id: 'payment.record', code: 'payment.record', module: 'Billing', description: 'Receive cash/UPI/card payments and print receipts', risk_level: 'sensitive' },
  { id: 'donor.register', code: 'donor.register', module: 'Blood Bank', description: 'Blood donor intake, health screening & bleeds', risk_level: 'normal' },
  { id: 'blood.issue', code: 'blood.issue', module: 'Blood Bank', description: 'Compatibility cross-match sign-off & unit issue', risk_level: 'critical' },
  { id: 'system.admin', code: 'system.admin', module: 'System Admin', description: 'Manage users, license keys and local backups', risk_level: 'critical' },
])

const selectedRole = ref<RoleItem>(roles.value[1]!)
const enabledPermissionIds = ref<Set<string>>(new Set(selectedRole.value?.permission_ids || []))
const isCreateRoleModalOpen = ref(false)
const newRoleName = ref('')
const newRoleDesc = ref('')

const groupedPermissions = computed(() => {
  const groups: Record<string, PermissionItem[]> = {}
  for (const perm of permissions.value) {
    if (!groups[perm.module]) groups[perm.module] = []
    groups[perm.module]!.push(perm)
  }
  return groups
})

function selectRole(role: RoleItem) {
  selectedRole.value = role
  enabledPermissionIds.value = new Set(role.permission_ids || [])
}

function isPermissionEnabled(id: string) {
  return enabledPermissionIds.value.has(id)
}

function togglePermission(id: string) {
  if (selectedRole.value?.is_system && selectedRole.value.id === 'r-admin') {
    warning('Administrator permissions cannot be modified.')
    return
  }
  if (enabledPermissionIds.value.has(id)) {
    enabledPermissionIds.value.delete(id)
  } else {
    enabledPermissionIds.value.add(id)
  }
}

function savePermissions() {
  if (selectedRole.value) {
    selectedRole.value.permission_ids = Array.from(enabledPermissionIds.value)
    success(`Permissions saved for role "${selectedRole.value.name}"!`)
  }
}

function createCustomRole() {
  if (!newRoleName.value.trim()) return
  const r: RoleItem = {
    id: `r-${Date.now()}`,
    name: newRoleName.value.trim(),
    description: newRoleDesc.value.trim() || 'Custom operational laboratory role',
    is_system: false,
    status: 'active',
    permission_ids: [],
  }
  roles.value.push(r)
  selectRole(r)
  success(`Role "${r.name}" created! Configure permissions below.`)
  isCreateRoleModalOpen.value = false
  newRoleName.value = ''
  newRoleDesc.value = ''
}
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
      <div>
        <h1 class="text-xl font-bold text-slate-900 tracking-tight">Role-Based Access Control (RBAC)</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Clinical authorization policies, segregation of duties and privilege boundaries
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <NuxtLink
          to="/admin/users"
          class="inline-flex items-center space-x-1 px-3 py-2 border border-slate-300 text-slate-700 bg-white hover:bg-slate-50 text-xs font-medium rounded-md shadow-2xs"
        >
          <span>Staff Directory</span>
        </NuxtLink>
        <button
          type="button"
          class="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded-md shadow-xs transition cursor-pointer"
          @click="isCreateRoleModalOpen = true"
        >
          <span>+ Create Custom Role</span>
        </button>
      </div>
    </div>

    <!-- Main Grid: Left Roles list, Right Permissions Matrix -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Roles Column -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-2xs p-4">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Roles Defined ({{ roles.length }})</h2>
        <div class="space-y-1.5">
          <div
            v-for="r in roles"
            :key="r.id"
            :class="[
              'p-3 rounded-lg border cursor-pointer transition text-xs',
              selectedRole.id === r.id
                ? 'bg-blue-50/70 border-blue-400 shadow-2xs'
                : 'border-slate-200 hover:bg-slate-50'
            ]"
            @click="selectRole(r)"
          >
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-900" :class="selectedRole.id === r.id ? 'text-blue-900' : ''">
                {{ r.name }}
              </span>
              <span
                v-if="r.is_system"
                class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-100 text-slate-600 uppercase"
              >
                System
              </span>
            </div>
            <p class="text-[11px] text-slate-500 mt-1 line-clamp-2">
              {{ r.description }}
            </p>
          </div>
        </div>
      </div>

      <!-- Permissions Column -->
      <div class="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-2xs p-5 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-2">
          <div>
            <span class="text-xs uppercase font-bold tracking-wider text-slate-400">Editing Permissions For</span>
            <h2 class="text-base font-bold text-slate-900 mt-0.5">{{ selectedRole.name }}</h2>
          </div>
          <button
            type="button"
            class="px-4 py-1.5 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded text-xs shadow-xs cursor-pointer"
            @click="savePermissions"
          >
            Save Policy Changes
          </button>
        </div>

        <!-- Modules Grouping -->
        <div class="space-y-4">
          <div
            v-for="(perms, moduleName) in groupedPermissions"
            :key="moduleName"
            class="border border-slate-200 rounded-lg p-3.5 space-y-2 bg-slate-50/30"
          >
            <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center justify-between">
              <span>{{ moduleName }} Module</span>
              <span class="text-[10px] text-slate-400 font-mono font-normal">{{ perms.length }} permissions</span>
            </h3>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div
                v-for="p in perms"
                :key="p.id"
                class="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-md"
              >
                <div class="pr-2">
                  <div class="font-semibold text-slate-900 text-xs">{{ p.code }}</div>
                  <div class="text-[10px] text-slate-500">{{ p.description }}</div>
                  <span
                    :class="[
                      'inline-block mt-1 text-[9px] font-bold uppercase px-1.5 py-0.2 rounded',
                      p.risk_level === 'critical' ? 'bg-red-100 text-red-800' : (p.risk_level === 'sensitive' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600')
                    ]"
                  >
                    {{ p.risk_level }}
                  </span>
                </div>

                <!-- Custom Switch -->
                <button
                  type="button"
                  role="switch"
                  tabindex="0"
                  :aria-checked="isPermissionEnabled(p.id)"
                  :class="[
                    'w-9 h-5 rounded-full transition-colors relative shrink-0 cursor-pointer p-0.5',
                    isPermissionEnabled(p.id) ? 'bg-sky-600' : 'bg-slate-300'
                  ]"
                  @click="togglePermission(p.id)"
                  @keydown.enter.prevent="togglePermission(p.id)"
                >
                  <span
                    :class="[
                      'block w-4 h-4 bg-white rounded-full shadow-xs transition-transform',
                      isPermissionEnabled(p.id) ? 'translate-x-4' : 'translate-x-0'
                    ]"
                  />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Custom Role Modal -->
    <div
      v-if="isCreateRoleModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden text-left">
        <div class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-sm font-bold text-slate-900">Create Custom Clinical Role</h3>
          <button type="button" class="text-slate-400 hover:text-slate-600" @click="isCreateRoleModalOpen = false">&times;</button>
        </div>

        <form class="p-5 space-y-3 text-xs" @submit.prevent="createCustomRole">
          <div>
            <label class="block font-medium text-slate-700 mb-1">Role Display Name</label>
            <input v-model="newRoleName" required class="w-full px-2.5 py-1.5 border border-slate-300 rounded" placeholder="e.g. Quality Assurance Auditor" />
          </div>

          <div>
            <label class="block font-medium text-slate-700 mb-1">Functional Description</label>
            <textarea v-model="newRoleDesc" rows="3" class="w-full px-2.5 py-1.5 border border-slate-300 rounded" placeholder="Scope of duties..." />
          </div>

          <div class="flex justify-end space-x-2 pt-3">
            <button type="button" class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded hover:bg-slate-50" @click="isCreateRoleModalOpen = false">
              Cancel
            </button>
            <button type="submit" class="px-4 py-1.5 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded shadow-xs">
              Create Role
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
