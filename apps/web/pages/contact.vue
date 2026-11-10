<script setup lang="ts">
import { ref } from 'vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const sent = ref(false)
const contactForm = ref({
  name: '',
  email: '',
  phone: '',
  subject: 'General Inquiry',
  message: '',
})

const submitContact = () => {
  if (!contactForm.value.name || !contactForm.value.phone) return
  sent.value = true
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="phone" size="xs" />
        <span>We Are Here to Assist</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Connect with the Aarozi Engineering & Support Team
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Have questions about LAN configuration, analyzer interfacing, or license purchasing? Get in touch directly with our support specialists.
      </p>
    </div>

    <!-- Contact Details & Form -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Contact Info Cards -->
      <div class="space-y-4 lg:col-span-1">
        <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 space-y-3">
          <div class="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
            <Icon name="phone" size="sm" />
          </div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white">Direct Phone & WhatsApp</h3>
          <p class="text-xs text-slate-500">Available Monday to Saturday, 9:00 AM – 7:00 PM IST</p>
          <a href="tel:+919876543210" class="text-sm font-bold text-teal-600 dark:text-teal-400 block hover:underline">
            +91 98765 43210
          </a>
        </div>

        <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 space-y-3">
          <div class="w-10 h-10 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
            <Icon name="mail" size="sm" />
          </div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white">Email Inquiries</h3>
          <p class="text-xs text-slate-500">Fast response within 2 hours for licensing & technical queries</p>
          <a href="mailto:support@aarozi.in" class="text-sm font-bold text-sky-600 dark:text-sky-400 block hover:underline">
            support@aarozi.in
          </a>
        </div>

        <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 space-y-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
            <Icon name="help-circle" size="sm" />
          </div>
          <h3 class="text-base font-bold text-slate-900 dark:text-white">Remote Assistance</h3>
          <p class="text-xs text-slate-500">Immediate remote desktop setup via AnyDesk or TeamViewer</p>
          <span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400 block">
            Guaranteed 15-minute response for active diagnostic centres
          </span>
        </div>
      </div>

      <!-- Contact Form -->
      <div class="lg:col-span-2 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 sm:p-10 shadow-sm space-y-6">
        <h3 class="text-lg font-bold text-slate-900 dark:text-white border-b pb-4 border-slate-100 dark:border-slate-800">
          Send Us a Message
        </h3>

        <form v-if="!sent" @submit.prevent="submitContact" class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Your Name *</label>
              <input
                v-model="contactForm.name"
                type="text"
                required
                placeholder="e.g. Dr. Ramesh Kumar"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Mobile Number *</label>
              <input
                v-model="contactForm.phone"
                type="tel"
                required
                placeholder="e.g. 9876543210"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Email Address</label>
              <input
                v-model="contactForm.email"
                type="email"
                placeholder="e.g. ramesh@gmail.com"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Inquiry Department</label>
              <select
                v-model="contactForm.subject"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="General Inquiry">General Product Inquiry</option>
                <option value="Licensing">Licence Purchase & Activation</option>
                <option value="Technical Support">Technical & LAN Hub Setup</option>
                <option value="Customization">Report Template Customization</option>
              </select>
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">How can we help your laboratory? *</label>
            <textarea
              v-model="contactForm.message"
              rows="4"
              required
              placeholder="Tell us about your diagnostic facility, daily test volume, or specific requirements..."
              class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
            ></textarea>
          </div>

          <div class="pt-2">
            <Button type="submit" variant="primary" class="w-full justify-center py-3 text-sm">
              Send Message
            </Button>
          </div>
        </form>

        <div v-else class="rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 p-8 text-center space-y-3">
          <div class="text-2xl text-emerald-600 font-bold">✓ Message Received</div>
          <p class="text-xs text-slate-600 dark:text-slate-400">
            Thank you, {{ contactForm.name }}. We will review your message and reply via WhatsApp or phone within 2 business hours.
          </p>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>
