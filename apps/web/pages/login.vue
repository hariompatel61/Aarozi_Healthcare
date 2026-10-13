<template>
  <div class="max-w-md mx-auto mt-12 bg-white p-8 rounded-lg shadow border border-gray-200">
    <h1 class="text-xl font-bold text-gray-900 mb-6 text-center">Sign in to Aarozi</h1>
    <form class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Username / Email</label>
        <input type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" placeholder="user@aarozi.local" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
        <input type="password" class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
      </div>
      <button type="submit" class="w-full bg-blue-900 text-white py-2 px-4 rounded-md hover:bg-blue-800 font-medium transition-colors">
        Sign In
      </button>
    </form>
  </div>
</template>