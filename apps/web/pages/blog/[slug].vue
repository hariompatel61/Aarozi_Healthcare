<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { usePlatformStore } from '~/composables/usePlatformStore'
import Icon from '~/components/ui/Icon.vue'
import Button from '~/components/ui/Button.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const route = useRoute()
const slug = computed(() => route.params.slug as string)
const { blogPosts, initStore } = usePlatformStore()

onMounted(() => {
  initStore()
})

const post = computed(() => {
  return blogPosts.value.find(p => p.slug === slug.value) || blogPosts.value[0]
})
</script>

<template>
  <div v-if="post" class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-10 text-slate-900 dark:text-slate-100">
    <!-- Back Link -->
    <div>
      <NuxtLink to="/blog" class="text-xs font-bold text-[#2576d2] dark:text-[#90ccf9] hover:underline flex items-center space-x-1">
        <Icon name="arrow-left" size="xs" />
        <span>Back to Knowledge Hub</span>
      </NuxtLink>
    </div>

    <!-- Article Header -->
    <div class="space-y-4">
      <div class="flex items-center space-x-3 text-xs">
        <span class="font-bold text-[#1c5fae] dark:text-[#90ccf9] px-3 py-1 rounded-full bg-[#f0f7fe] dark:bg-[#1d273d] border border-[#bee1fb] dark:border-[#2576d2]/50">
          {{ post.category }}
        </span>
        <span class="text-slate-400">&bull;</span>
        <span class="text-slate-500">{{ post.date }}</span>
        <span class="text-slate-400">&bull;</span>
        <span class="text-slate-500">{{ post.readTime }}</span>
      </div>

      <h1 class="text-3xl sm:text-5xl font-black tracking-tight text-slate-900 dark:text-white leading-tight">
        {{ post.title }}
      </h1>

      <p class="text-base text-slate-600 dark:text-slate-300 leading-relaxed font-medium">
        {{ post.excerpt }}
      </p>

      <div class="pt-4 border-t border-[#ede9f7] dark:border-[#23273e] flex items-center space-x-3 text-xs text-slate-500">
        <div class="w-8 h-8 rounded-full bg-[#2576d2] text-white flex items-center justify-center font-bold text-xs">
          AH
        </div>
        <div>
          <div class="font-bold text-slate-800 dark:text-slate-200">{{ post.author }}</div>
          <div class="text-[11px] text-slate-400">Aarozi Healthcare Clinical Content Board</div>
        </div>
      </div>
    </div>

    <!-- Article Body -->
    <article class="prose prose-slate dark:prose-invert max-w-none text-sm sm:text-base leading-relaxed space-y-6 pt-4 border-t border-[#ede9f7] dark:border-[#23273e]">
      <div class="whitespace-pre-line text-slate-700 dark:text-slate-300 leading-relaxed">
        {{ post.content }}
      </div>
    </article>

    <!-- Bottom Action CTA -->
    <CtaBanner />
  </div>
</template>

