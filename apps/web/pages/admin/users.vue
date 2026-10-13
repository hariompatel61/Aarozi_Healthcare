<template>
  <div class="admin-users max-w-7xl mx-auto px-4 py-6" role="region" aria-label="User Management">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">User Management</h1>
      <button type="button" class="px-4 py-2 text-sm rounded bg-indigo-600 text-white" @click="openCreateUserModal">Add User</button>
    </div>

    <!-- UI States -->
    <div v-if="uiState === 'loading'" class="p-6 text-center text-gray-500" aria-live="polite">Loading users...</div>
    <div v-else-if="uiState === 'error'" class="p-4 bg-red-50 text-red-700" aria-live="assertive">{{ errorMessage }}</div>
    <div v-else-if="uiState === 'permission_denied'" class="p-4 bg-yellow-50 text-yellow-800" aria-live="assertive">Access Denied</div>

    <!-- Users Table -->
    <div v-else class="bg-white shadow rounded overflow-hidden border">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assigned Roles</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ user.username }}</td>
            <td class="px-6 py-4 text-sm text-gray-500">{{ user.email }}</td>
            <td class="px-6 py-4 text-sm text-gray-500">
              <span v-for="role in user.roles" :key="role" class="inline-block bg-indigo-100 text-indigo-800 text-xs px-2 py-0.5 rounded mr-1">{{ role }}</span>
            </td>
            <td class="px-6 py-4 text-sm">
              <span :class="['px-2 py-0.5 rounded text-xs', user.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800']">
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="px-6 py-4 text-right text-sm">
              <button type="button" class="text-indigo-600 hover:text-indigo-900 font-medium" @click="editUser(user)">Edit Scopes</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface UserItem {
  id: string
  username: string
  email: string
  is_active: boolean
  roles: string[]
  branch_scope?: string[]
}

const uiState = ref<'loading' | 'ready' | 'error' | 'permission_denied'>('ready')
const errorMessage = ref('')
const users = ref<UserItem[]>([
  { id: 'u1', username: 'dr_jane', email: 'jane@alpha.test', is_active: true, roles: ['Pathologist'] },
  { id: 'u2', username: 'sam_tech', email: 'sam@alpha.test', is_active: true, roles: ['Phlebotomist'] }
])

function openCreateUserModal() {
  // Opens user creation dialog
}

function editUser(user: UserItem) {
  // Opens role & branch scope assignment editor
}
</script>
