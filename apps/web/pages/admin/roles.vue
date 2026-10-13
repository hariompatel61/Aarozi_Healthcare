<template>
  <div class="admin-roles max-w-7xl mx-auto px-4 py-6" role="region" aria-label="Role and Permission Management">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Role Management</h1>
      <button type="button" class="px-4 py-2 text-sm rounded bg-indigo-600 text-white" @click="openNewRoleForm">Create Role</button>
    </div>

    <div v-if="uiState === 'loading'" class="p-6 text-center text-gray-500" aria-live="polite">Loading roles...</div>
    <div v-else-if="uiState === 'error'" class="p-4 bg-red-50 text-red-700" aria-live="assertive">{{ errorMessage }}</div>
    <div v-else-if="uiState === 'permission_denied'" class="p-4 bg-yellow-50 text-yellow-800" aria-live="assertive">Access Denied</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white shadow rounded p-4 border">
        <h2 class="text-lg font-medium mb-3">Roles ({{ roles.length }})</h2>
        <ul class="divide-y" role="list">
          <li
            v-for="role in roles"
            :key="role.id"
            :class="['p-3 rounded cursor-pointer', selectedRole?.id === role.id ? 'bg-indigo-50 font-bold' : 'hover:bg-gray-50']"
            tabindex="0"
            @keydown.enter="selectRole(role)"
            @click="selectRole(role)"
          >
            <div class="flex justify-between">
              <span>{{ role.name }}</span>
              <span v-if="role.is_system" class="text-xs bg-gray-100 px-2 py-0.5 rounded">System</span>
            </div>
          </li>
        </ul>
      </div>

      <div class="md:col-span-2 bg-white shadow rounded p-6 border">
        <div v-if="!selectedRole" class="text-center py-12 text-gray-500">Select a role to manage its permissions.</div>
        <div v-else>
          <h2 class="text-lg font-bold mb-4">Editing: {{ selectedRole.name }}</h2>
          <div class="space-y-4">
            <div v-for="(perms, moduleName) in groupedPermissions" :key="moduleName" class="border rounded p-3">
              <h3 class="text-sm font-semibold uppercase mb-2">{{ moduleName }} Module</h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div v-for="perm in perms" :key="perm.code" class="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <span class="text-xs block font-medium">{{ perm.code }}</span>
                    <span class="text-[10px] uppercase font-bold text-gray-500">{{ perm.risk_level }}</span>
                  </div>
                  <button
                    type="button"
                    :disabled="selectedRole.is_system"
                    :aria-checked="isPermissionEnabled(perm.id)"
                    role="switch"
                    :class="['h-6 w-11 rounded-full transition-colors', isPermissionEnabled(perm.id) ? 'bg-indigo-600' : 'bg-gray-300']"
                    @click="togglePermission(perm.id)"
                  >
                    <span :class="['block h-5 w-5 bg-white rounded-full transition-transform', isPermissionEnabled(perm.id) ? 'translate-x-5' : 'translate-x-1']" />
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="mt-4 flex justify-end">
            <button v-if="!selectedRole.is_system" type="button" class="px-4 py-2 bg-indigo-600 text-white rounded text-sm" @click="saveRolePermissions">Save Permissions</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface PermissionItem { id: string; code: string; module: string; resource: string; action: string; risk_level: string }
interface RoleItem { id: string; name: string; is_system: boolean; status: string; permission_ids?: string[] }

const uiState = ref<'loading' | 'ready' | 'error' | 'permission_denied'>('ready')
const errorMessage = ref('')
const roles = ref<RoleItem[]>([
  { id: '1', name: 'Tenant Administrator', is_system: true, status: 'active', permission_ids: ['p1', 'p2'] },
  { id: '2', name: 'Pathologist', is_system: false, status: 'active', permission_ids: ['p1'] }
])
const permissions = ref<PermissionItem[]>([
  { id: 'p1', code: 'sample.collect', module: 'pathology', resource: 'sample', action: 'collect', risk_level: 'normal' },
  { id: 'p2', code: 'result.approve', module: 'pathology', resource: 'result', action: 'approve', risk_level: 'critical' }
])
const selectedRole = ref<RoleItem | null>(roles.value[1] ?? null)
const enabledPermissionIds = ref<Set<string>>(new Set(selectedRole.value?.permission_ids || []))

const groupedPermissions = computed(() => {
  const groups: Record<string, PermissionItem[]> = {}
  for (const perm of permissions.value) {
    if (!groups[perm.module]) groups[perm.module] = []
    groups[perm.module]!.push(perm)
  }
  return groups
})

function selectRole(role: RoleItem) { selectedRole.value = role; enabledPermissionIds.value = new Set(role.permission_ids || []) }
function isPermissionEnabled(id: string) { return enabledPermissionIds.value.has(id) }
function togglePermission(id: string) {
  if (selectedRole.value?.is_system) return
  if (enabledPermissionIds.value.has(id)) enabledPermissionIds.value.delete(id)
  else enabledPermissionIds.value.add(id)
}
function openNewRoleForm() {
  const newRole: RoleItem = { id: `r-${Date.now()}`, name: 'New Custom Role', is_system: false, status: 'active', permission_ids: [] }
  roles.value.push(newRole)
  selectRole(newRole)
}
function saveRolePermissions() {
  if (selectedRole.value) selectedRole.value.permission_ids = Array.from(enabledPermissionIds.value)
}
</script>
