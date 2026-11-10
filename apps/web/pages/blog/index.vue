<script setup lang="ts">
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const articles = [
  {
    slug: 'nabl-compliance-checklist-for-pathology-labs',
    title: 'The Complete NABL Accreditation Checklist for Indian Pathology Laboratories',
    excerpt: 'Step-by-step guidance on reference interval documentation, internal quality control (IQC) charts, and pathologist digital signature standards.',
    category: 'Quality & Compliance',
    readTime: '6 min read',
    date: '04 Nov 2026',
  },
  {
    slug: 'why-offline-first-lis-beats-cloud-for-diagnostic-centers',
    title: 'Why Offline-First Local Hub LIS Outperforms Pure Cloud Software in Diagnostic Centers',
    excerpt: 'An architectural comparison of latency, data privacy, internet outage resilience, and recurring SaaS cost inflation.',
    category: 'Architecture',
    readTime: '8 min read',
    date: '28 Oct 2026',
  },
  {
    slug: 'eliminating-preanalytical-errors-with-barcoding',
    title: 'How Color-Coded Barcode Labeling Slashes Pre-Analytical Sample Errors by 99%',
    excerpt: 'Best practices for tube segregation (EDTA, Fluoride, Serum Clot Activator) and Code 128 thermal accessioning at the phlebotomy desk.',
    category: 'Operations',
    readTime: '5 min read',
    date: '15 Oct 2026',
  },
  {
    slug: 'radiology-structured-reporting-macros',
    title: 'Speeding Up Ultrasound & X-Ray Reports: The Power of Organ-by-Organ Clinical Macros',
    excerpt: 'How Sonologists and Radiologists reduce daily typing fatigue and standardize abnormal findings across multiple reporting rooms.',
    category: 'Radiology',
    readTime: '7 min read',
    date: '02 Oct 2026',
  },
]
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="book-open" size="xs" />
        <span>Clinical & Operational Guides</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Aarozi Healthcare Knowledge Hub
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Expert articles, operational guides, and regulatory insights for diagnostic laboratory owners, pathologists, and healthcare technologists.
      </p>
    </div>

    <!-- Articles Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div
        v-for="article in articles"
        :key="article.slug"
        class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 shadow-sm flex flex-col justify-between hover:shadow-md transition-all space-y-4"
      >
        <div class="space-y-3">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span class="font-bold text-teal-600 dark:text-teal-400 px-2.5 py-0.5 rounded-full bg-teal-50 dark:bg-teal-950/50">
              {{ article.category }}
            </span>
            <span>{{ article.date }} • {{ article.readTime }}</span>
          </div>

          <h3 class="text-lg font-bold text-slate-900 dark:text-white leading-snug">
            {{ article.title }}
          </h3>

          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            {{ article.excerpt }}
          </p>
        </div>

        <div class="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <span class="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline cursor-pointer flex items-center space-x-1">
            <span>Read Full Guide</span>
            <Icon name="arrow-right" size="xs" />
          </span>
          <span class="text-[11px] text-slate-400">Free PDF Guide</span>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

