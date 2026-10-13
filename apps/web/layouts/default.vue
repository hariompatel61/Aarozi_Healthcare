<template>
  <div class="min-h-screen bg-gray-50 flex flex-col font-sans">
    <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="text-xl font-bold text-blue-900 tracking-tight">Aarozi Healthcare</span>
        <span class="text-xs bg-blue-100 text-blue-800 font-medium px-2.5 py-0.5 rounded">Modular Monolith</span>
      </div>
      <nav class="flex items-center space-x-4 text-sm font-medium text-gray-600">
        <NuxtLink to="/" class="hover:text-blue-900">Home</NuxtLink>
        <NuxtLink to="/dashboard" class="hover:text-blue-900">Dashboard</NuxtLink>
        <NuxtLink to="/admin/roles" class="hover:text-blue-900">Roles &amp; Permissions</NuxtLink>
        <NuxtLink to="/admin/users" class="hover:text-blue-900">User Scopes</NuxtLink>
        <NuxtLink to="/patients" class="hover:text-blue-900">Patients</NuxtLink>
        <NuxtLink to="/patients/register" class="hover:text-blue-900 font-semibold text-blue-700">+ Register Patient</NuxtLink>
        <NuxtLink to="/login" class="hover:text-blue-900">Login</NuxtLink>
      </nav>
    </header>
    <main class="flex-1 max-w-7xl w-full mx-auto p-6">
      <slot />
    </main>
    <footer class="bg-white border-t border-gray-200 px-6 py-3 text-center text-xs text-gray-500">
      Aarozi Healthcare SaaS &copy; 2026 &mdash; Offline First &amp; Local Multi-PC Ready
    </footer>
  </div>
</template>