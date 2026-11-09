<script setup lang="ts">
definePageMeta({ layout: 'public' })
useSeoMeta({ title: 'Installation & setup | Aarozi Healthcare', description: 'Prepare a Windows Master PC and local network for Aarozi Healthcare.' })
const steps = [
['Prepare the Master PC','Use a supported Windows 10/11 computer with administrator access, reliable power and adequate disk capacity. Confirm final hardware requirements with support.'],
['Plan your local network','Use a stable wired LAN where possible. Decide which workstations need access and keep the Master PC on a reserved local IP address.'],
['Install the application','Use only an official, versioned and digitally verified installer. Do not install builds from unofficial file-sharing links.'],
['Configure your laboratory','Set up lab identity, branches, users, roles, test catalogue, report templates and printers.'],
['Verify backup and restore','Choose a customer-controlled backup destination and perform a restore drill before entering live patient data.'],
['Train and go live','Test registration, sample processing, report review, billing, user access and daily close procedures.']
]
</script>
<template><div class="mx-auto max-w-5xl px-4 py-16 sm:px-6"><p class="text-xs font-bold uppercase tracking-[.2em] text-teal-700">Deployment guide</p><h1 class="mt-3 text-4xl font-black">Set up your laboratory environment.</h1><p class="mt-4 max-w-2xl leading-7 text-slate-600">This is a preparation guide, not a substitute for the release-specific installation manual. Confirm compatibility and backup behavior with the exact version you install.</p><ol class="mt-10 space-y-4"><li v-for="(step, i) in steps" :key="step[0]" class="flex gap-5 rounded-2xl border border-slate-200 p-6"><span class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-teal-50 font-black text-teal-800">{{ i + 1 }}</span><div><h2 class="text-lg font-bold">{{ step[0] }}</h2><p class="mt-2 text-sm leading-6 text-slate-600">{{ step[1] }}</p></div></li></ol><div class="mt-9 rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-950"><strong>Before production use:</strong> verify the installer signature, supported Windows version, database location, LAN firewall rules, backup destination and successful restore test.</div><NuxtLink to="/download" class="mt-7 inline-flex rounded-xl bg-teal-700 px-5 py-3 font-semibold text-white">View download status</NuxtLink></div></template>
