<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Operational Dashboard</h1>
        <p class="text-gray-600">Unified Diagnostic Laboratory + Blood Bank + Billing workspace</p>
      </div>
      <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
        Active Tenant: Aarozi Main
      </span>
    </div>

    <!-- Quick Navigation to Phase 2 RBAC UI -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <NuxtLink
        to="/admin/roles"
        class="block p-6 bg-white rounded-lg border border-gray-200 shadow-sm hover:border-indigo-500 hover:shadow transition group"
      >
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-gray-900 group-hover:text-indigo-600">Roles &amp; Permissions</h2>
          <span class="text-xs bg-indigo-50 text-indigo-700 font-medium px-2 py-0.5 rounded">RBAC</span>
        </div>
        <p class="text-sm text-gray-500 mb-4">
          Configure canonical tenant roles, audit risk levels, and toggle atomic module permissions.
        </p>
        <span class="text-sm font-medium text-indigo-600 flex items-center">
          Open Role Manager &rarr;
        </span>
      </NuxtLink>

      <NuxtLink
        to="/admin/users"
        class="block p-6 bg-white rounded-lg border border-gray-200 shadow-sm hover:border-indigo-500 hover:shadow transition group"
      >
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-gray-900 group-hover:text-indigo-600">User Management &amp; Scopes</h2>
          <span class="text-xs bg-emerald-50 text-emerald-700 font-medium px-2 py-0.5 rounded">Identity</span>
        </div>
        <p class="text-sm text-gray-500 mb-4">
          Assign branch and department boundaries to staff accounts with multi-tenant guards.
        </p>
        <span class="text-sm font-medium text-indigo-600 flex items-center">
          Open User Scopes &rarr;
        </span>
      </NuxtLink>

      <div class="p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-gray-900">Security &amp; Audit Engine</h2>
          <span class="text-xs bg-blue-50 text-blue-700 font-medium px-2 py-0.5 rounded">Engine</span>
        </div>
        <p class="text-sm text-gray-500 mb-4">
          Zero-trust server-side authorization engine active. Scoped policies and audit trail enabled.
        </p>
        <span class="text-sm text-gray-400 font-medium">322 backend tests green</span>
      </div>
    </div>
  </div>
</template>
