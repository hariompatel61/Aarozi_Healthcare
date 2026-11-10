<script setup lang="ts">
import { onMounted } from 'vue'
import { usePlatformStore } from '~/composables/usePlatformStore'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const { blogPosts, initStore } = usePlatformStore()

onMounted(() => {
  initStore()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16 text-slate-900 dark:text-slate-100">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#f0f7fe] dark:bg-[#1d273d] text-[#1c5fae] dark:text-[#90ccf9] border border-[#bee1fb] dark:border-[#2576d2]/50">
        <Icon name="book-open" size="xs" />
        <span>Clinical &amp; Operational Knowledge Hub</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Aarozi Healthcare Knowledge Hub
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-300">
        Expert articles, operational guides, and regulatory insights for diagnostic laboratory owners, pathologists, and healthcare technologists.
      </p>
    </div>

    <!-- Articles Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div
        v-for="article in blogPosts.filter(p => p.published)"
        :key="article.id"
        class="rounded-3xl border border-[#ede9f7] dark:border-[#23273e] bg-white dark:bg-[#15182a] p-8 shadow-2xs flex flex-col justify-between hover:shadow-md transition-all space-y-4"
      >
        <div class="space-y-3">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span class="font-bold text-[#1c5fae] dark:text-[#90ccf9] px-2.5 py-0.5 rounded-full bg-[#f0f7fe] dark:bg-[#1d273d] border border-[#bee1fb] dark:border-[#2576d2]/50">
              {{ article.category }}
            </span>
            <span>{{ article.date }} &bull; {{ article.readTime }}</span>
          </div>

          <h3 class="text-lg font-bold text-slate-900 dark:text-white leading-snug">
            {{ article.title }}
          </h3>

          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            {{ article.excerpt }}
          </p>
        </div>

        <div class="pt-4 border-t border-[#ede9f7] dark:border-[#23273e] flex items-center justify-between">
          <NuxtLink :to="`/blog/${article.slug}`" class="text-xs font-bold text-[#2576d2] dark:text-[#90ccf9] hover:underline flex items-center space-x-1">
            <span>Read Full Guide</span>
            <Icon name="arrow-right" size="xs" />
          </NuxtLink>
          <span class="text-[11px] text-slate-400 font-medium">By {{ article.author }}</span>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>
