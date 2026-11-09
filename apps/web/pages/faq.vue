<script setup lang="ts">
definePageMeta({ layout: 'public' as any as any })
useSeoMeta({ title: 'Frequently asked questions | Aarozi Healthcare', description: 'Answers about Aarozi Healthcare deployment, licensing and data handling.' })
const faqs = [
['Does the LIS require internet for daily work?','The product is designed around local laboratory operations. Exact offline behavior must be confirmed against the installed release and tested workflows.'],
['Can multiple workstations connect to one laboratory server?','The deployment model uses a Master PC and local network workstations. Confirm supported workstation limits and network requirements for the selected plan before purchase.'],
['Can I connect my analyzer?','Compatibility depends on the exact instrument model, communication protocol, interface hardware and validated driver. Ask for written confirmation for your analyzer.'],
['Where is patient data stored?','The intended deployment keeps clinical data in the customer laboratory environment. Confirm the actual configured database path, backup destination and remote-access settings before go-live.'],
['Is Google Drive live database sync supported?','A live SQLite database must not be placed in a file-sync folder. Use an application-created consistent backup archive and verify restore procedures.'],
['How do I obtain the Windows installer?','The public installer link will be published after signing, checksum and clean Windows installation checks have been completed.'],
['Can I create an online customer account?','Hosted portal signup and login are not active yet. Laboratory workstation authentication remains a separate local service.'],
]
</script>
<template><div class="mx-auto max-w-4xl px-4 py-16 sm:px-6"><p class="text-xs font-bold uppercase tracking-[.2em] text-teal-700">Help centre</p><h1 class="mt-3 text-4xl font-black">Frequently asked questions.</h1><div class="mt-10 divide-y divide-slate-200 border-y border-slate-200"><details v-for="item in faqs" :key="item[0]" class="py-5"><summary class="cursor-pointer text-base font-bold">{{ item[0] }}</summary><p class="mt-3 max-w-3xl text-sm leading-7 text-slate-600">{{ item[1] }}</p></details></div><NuxtLink to="/support" class="mt-8 inline-flex rounded-xl bg-teal-700 px-5 py-3 font-semibold text-white">More support information</NuxtLink></div></template>
