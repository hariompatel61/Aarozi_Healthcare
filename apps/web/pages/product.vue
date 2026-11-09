<script setup lang="ts">
definePageMeta({ layout: 'public' })
useSeoMeta({ title: 'Product information | Aarozi Healthcare', description: 'Explore Aarozi Healthcare LIS modules and laboratory workflows.' })
const modules = [
['Patient registration','Capture patient and referring details as part of the laboratory intake process.'],
['Sample collection & tracking','Organise sample identifiers, collection status and processing hand-offs.'],
['Pathology & biochemistry','Manage test catalogues and result-entry workflows configured for your lab.'],
['Reports','Prepare laboratory reports for review and release according to assigned roles.'],
['Billing','Support front-desk billing and invoice workflows.'],
['Blood bank','Explore blood-bank workflows where enabled in your licensed deployment.'],
['Analyzer connectivity','Confirm instrument model, protocol and interface compatibility before purchase.'],
['Backup & recovery','Configure and periodically test backups to customer-controlled destinations.'],
]
</script>
<template><div class="mx-auto max-w-6xl px-4 py-16 sm:px-6"><p class="text-xs font-bold uppercase tracking-[.2em] text-teal-700">Product information</p><h1 class="mt-3 max-w-3xl text-4xl font-black">A practical software foundation for diagnostic lab workflows.</h1><p class="mt-5 max-w-2xl leading-7 text-slate-600">Aarozi Healthcare brings key laboratory activities into one application. Module availability depends on the software release, license and configuration at your site.</p><div class="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"><article v-for="m in modules" :key="m[0]" class="rounded-2xl border border-slate-200 p-6"><div class="text-xs font-bold text-teal-700">MODULE</div><h2 class="mt-3 text-lg font-bold">{{ m[0] }}</h2><p class="mt-2 text-sm leading-6 text-slate-600">{{ m[1] }}</p></article></div><div class="mt-10 rounded-2xl bg-slate-950 p-8 text-white"><h2 class="text-2xl font-bold">Need to check a specific analyzer or workflow?</h2><p class="mt-2 text-slate-300">Confirm compatibility and availability with the product team before purchasing.</p><NuxtLink to="/support" class="mt-5 inline-flex rounded-lg bg-teal-400 px-5 py-3 font-bold text-slate-950">Ask a product question</NuxtLink></div></div></template>
