<script setup lang="ts">
import { ref } from 'vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})

const submitted = ref(false)
const form = ref({
  labName: '',
  contactName: '',
  phone: '',
  email: '',
  city: '',
  labType: 'pathology',
  preferredTime: 'morning',
  dailyVolume: '50-150',
})

const handleDemoSubmit = () => {
  if (!form.value.labName || !form.value.phone) return
  submitted.value = true
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
    <!-- Header -->
    <div class="text-center max-w-3xl mx-auto space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="video" size="xs" />
        <span>Live Interactive Guided Walkthrough</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Experience Aarozi LIS in Real-Time
      </h1>
      <p class="text-sm sm:text-base text-slate-600 dark:text-slate-400">
        Schedule a 1-on-1 virtual product demonstration with our healthcare software specialists. We will simulate your actual lab workflow, from sample intake to final verified report.
      </p>
    </div>

    <!-- Booking Form / Success Card -->
    <div class="max-w-3xl mx-auto">
      <div v-if="!submitted" class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 sm:p-10 shadow-lg space-y-6">
        <h3 class="text-lg font-bold text-slate-900 dark:text-white border-b pb-4 border-slate-100 dark:border-slate-800">
          Book Your 20-Minute Live Demo
        </h3>

        <form @submit.prevent="handleDemoSubmit" class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Diagnostic Centre / Lab Name *</label>
              <input
                v-model="form.labName"
                type="text"
                required
                placeholder="e.g. LifeCare Diagnostic Centre"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Doctor / Owner Full Name *</label>
              <input
                v-model="form.contactName"
                type="text"
                required
                placeholder="e.g. Dr. Rajesh Sharma"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Mobile / WhatsApp Number *</label>
              <input
                v-model="form.phone"
                type="tel"
                required
                placeholder="e.g. 9876543210"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Email Address (Optional)</label>
              <input
                v-model="form.email"
                type="email"
                placeholder="e.g. info@lifecarediagnostics.com"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Facility Type</label>
              <select
                v-model="form.labType"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="pathology">Pathology Laboratory</option>
                <option value="diagnostic">Integrated (Pathology + Ultrasound)</option>
                <option value="radiology">Radiology / Imaging Centre</option>
                <option value="blood_bank">Blood Bank & Component Centre</option>
              </select>
            </div>
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Daily Patient Volume</label>
              <select
                v-model="form.dailyVolume"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="1-50">1 - 50 Patients / day</option>
                <option value="50-150">50 - 150 Patients / day</option>
                <option value="150-500">150 - 500 Patients / day</option>
                <option value="500+">500+ Patients / day</option>
              </select>
            </div>
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Preferred Slot</label>
              <select
                v-model="form.preferredTime"
                class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="morning">Morning (10:00 AM - 1:00 PM)</option>
                <option value="afternoon">Afternoon (2:00 PM - 5:00 PM)</option>
                <option value="evening">Evening (5:00 PM - 8:00 PM)</option>
              </select>
            </div>
          </div>

          <div class="pt-4">
            <Button type="submit" variant="primary" class="w-full justify-center py-3 text-sm">
              Confirm Demo Request
            </Button>
          </div>
        </form>
      </div>

      <div v-else class="rounded-3xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40 p-8 sm:p-12 text-center space-y-4">
        <div class="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/60 text-emerald-600 dark:text-emerald-400 mx-auto flex items-center justify-center font-bold text-2xl">
          ✓
        </div>
        <h3 class="text-xl font-bold text-slate-900 dark:text-white">Demo Booking Confirmed!</h3>
        <p class="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-md mx-auto">
          Thank you, {{ form.contactName }}. Our product specialist will call you at <strong class="text-slate-900 dark:text-white">{{ form.phone }}</strong> to confirm your Google Meet or AnyDesk session.
        </p>
        <div class="pt-4 flex justify-center space-x-3">
          <NuxtLink to="/download">
            <Button variant="secondary" size="sm">Or Download Local Installer Now</Button>
          </NuxtLink>
        </div>
      </div>
    </div>

    <CtaBanner />
  </div>
</template>

