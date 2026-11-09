<script setup lang="ts">
definePageMeta({ layout: 'public' as any })
useSeoMeta({
  title: 'Aarozi Healthcare | Laboratory Information System',
  description: 'Explore Aarozi Healthcare laboratory information software for diagnostic lab operations, reporting, billing and local network workflows.',
  ogTitle: 'Aarozi Healthcare — Laboratory Information System',
  ogDescription: 'A clearer way to manage diagnostic laboratory workflows.',
})
const highlights = [
  { n: '01', title: 'Patient & sample workflows', body: 'Organise registration, sample collection, processing and report delivery in one operational workflow.' },
  { n: '02', title: 'Reports & laboratory billing', body: 'Bring report preparation, billing and day-to-day front desk work into a consistent system.' },
  { n: '03', title: 'Local network operation', body: 'Designed around a Master PC and LAN workstation model. Final capacity depends on tested deployment configuration.' },
  { n: '04', title: 'Backup & recovery', body: 'Plan customer-controlled backups and recovery procedures for your laboratory data.' },
]
</script>

<template>
  <div>
    <section class="relative overflow-hidden bg-slate-950 text-white">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(13,148,136,.28),transparent_48%)]" />
      <div class="relative mx-auto grid max-w-7xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[1.1fr_.9fr] lg:py-28">
        <div>
          <div class="inline-flex rounded-full border border-teal-400/30 bg-teal-400/10 px-3 py-1 text-xs font-semibold tracking-wide text-teal-200">AAROZI HEALTHCARE · LAB SOFTWARE</div>
          <h1 class="mt-6 max-w-3xl text-4xl font-black leading-tight tracking-tight sm:text-6xl">Your laboratory. <span class="text-teal-300">One connected workflow.</span></h1>
          <p class="mt-6 max-w-xl text-lg leading-8 text-slate-300">A laboratory information system for managing diagnostic operations, patient workflows, reports and billing—with a focus on dependable local operations.</p>
          <div class="mt-9 flex flex-wrap gap-3">
            <NuxtLink to="/business-registration" class="rounded-xl bg-teal-500 px-6 py-3.5 text-sm font-bold text-slate-950 hover:bg-teal-400">Register your lab <span aria-hidden="true">→</span></NuxtLink>
            <NuxtLink to="/product" class="rounded-xl border border-white/20 px-6 py-3.5 text-sm font-semibold text-white hover:bg-white/10">Explore the product</NuxtLink>
          </div>
          <p class="mt-5 text-xs text-slate-400">Product capabilities and availability are subject to the current release and verified deployment configuration.</p>
        </div>
        <div class="rounded-3xl border border-white/10 bg-white/5 p-4 shadow-2xl backdrop-blur">
          <div class="rounded-2xl bg-slate-900 p-5">
            <div class="flex items-center justify-between border-b border-white/10 pb-4"><div><div class="text-xs text-slate-400">LAB OPERATIONS</div><div class="mt-1 text-lg font-bold">Daily workflow overview</div></div><span class="rounded-full bg-teal-400/10 px-3 py-1 text-xs text-teal-200">Illustrative UI</span></div>
            <div class="mt-5 grid grid-cols-2 gap-3">
              <div class="rounded-xl bg-white/5 p-4"><div class="text-xs text-slate-400">Registration</div><div class="mt-2 text-2xl font-bold">Patients</div><div class="mt-1 text-xs text-slate-500">Front desk workflow</div></div>
              <div class="rounded-xl bg-white/5 p-4"><div class="text-xs text-slate-400">Processing</div><div class="mt-2 text-2xl font-bold">Samples</div><div class="mt-1 text-xs text-slate-500">Collection & tracking</div></div>
              <div class="rounded-xl bg-white/5 p-4"><div class="text-xs text-slate-400">Reporting</div><div class="mt-2 text-2xl font-bold">Results</div><div class="mt-1 text-xs text-slate-500">Review & release</div></div>
              <div class="rounded-xl bg-white/5 p-4"><div class="text-xs text-slate-400">Accounts</div><div class="mt-2 text-2xl font-bold">Billing</div><div class="mt-1 text-xs text-slate-500">Invoices & receipts</div></div>
            </div>
            <div class="mt-4 rounded-xl border border-teal-300/20 bg-teal-300/5 p-4 text-sm text-teal-100">A clear view of the work moving through your laboratory.</div>
          </div>
        </div>
      </div>
    </section>
    <section class="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:py-20">
      <div class="max-w-2xl"><p class="text-xs font-bold uppercase tracking-[.2em] text-teal-700">Built around lab operations</p><h2 class="mt-3 text-3xl font-black tracking-tight sm:text-4xl">From the front desk to the final report.</h2><p class="mt-4 leading-7 text-slate-600">Bring the everyday work of a diagnostic laboratory into a structured system. Explore the modules and deployment approach before choosing a plan.</p></div>
      <div class="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <article v-for="item in highlights" :key="item.n" class="rounded-2xl border border-slate-200 p-6"><div class="text-sm font-black text-teal-700">{{ item.n }}</div><h3 class="mt-5 text-lg font-bold">{{ item.title }}</h3><p class="mt-3 text-sm leading-6 text-slate-600">{{ item.body }}</p></article>
      </div>
    </section>
    <section class="bg-slate-50 py-16"><div class="mx-auto grid max-w-7xl gap-8 px-4 sm:px-6 lg:grid-cols-2 lg:items-center"><div><p class="text-xs font-bold uppercase tracking-[.2em] text-teal-700">Getting started</p><h2 class="mt-3 text-3xl font-black">A guided path to your lab setup.</h2><p class="mt-4 leading-7 text-slate-600">Review requirements, register your laboratory, install the software and configure your local workstation environment.</p></div><div class="grid gap-3 sm:grid-cols-2"><NuxtLink to="/business-registration" class="rounded-xl border bg-white p-5 font-semibold hover:border-teal-400">1. Register your lab <span class="block pt-2 text-sm font-normal text-slate-500">Business and contact details</span></NuxtLink><NuxtLink to="/setup" class="rounded-xl border bg-white p-5 font-semibold hover:border-teal-400">2. Read setup guide <span class="block pt-2 text-sm font-normal text-slate-500">Master PC and LAN basics</span></NuxtLink><NuxtLink to="/pricing" class="rounded-xl border bg-white p-5 font-semibold hover:border-teal-400">3. Compare plans <span class="block pt-2 text-sm font-normal text-slate-500">Current published price configuration</span></NuxtLink><NuxtLink to="/download" class="rounded-xl border bg-white p-5 font-semibold hover:border-teal-400">4. Get the installer <span class="block pt-2 text-sm font-normal text-slate-500">Release availability and checks</span></NuxtLink></div></div></section>
    <section class="mx-auto max-w-7xl px-4 py-16 text-center sm:px-6"><h2 class="text-3xl font-black">See whether Aarozi fits your laboratory.</h2><p class="mx-auto mt-4 max-w-xl text-slate-600">Start with product details, deployment requirements and transparent plan information.</p><div class="mt-7 flex flex-wrap justify-center gap-3"><NuxtLink to="/pricing" class="rounded-xl bg-teal-700 px-6 py-3 font-semibold text-white hover:bg-teal-800">View pricing</NuxtLink><NuxtLink to="/support" class="rounded-xl border border-slate-300 px-6 py-3 font-semibold hover:bg-slate-50">Contact support</NuxtLink></div></section>
  </div>
</template>
