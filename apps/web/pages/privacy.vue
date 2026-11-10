<script setup lang="ts">
import Icon from '~/components/ui/Icon.vue'
import CtaBanner from '~/components/marketing/CtaBanner.vue'

definePageMeta({
  layout: 'marketing',
})
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
    <!-- Header -->
    <div class="text-center space-y-4">
      <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
        <Icon name="shield-check" size="xs" />
        <span>Privacy & Data Sovereignty Charter</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        Aarozi Healthcare Privacy Policy
      </h1>
      <p class="text-xs sm:text-sm text-slate-500">Last updated: 10 November 2026</p>
    </div>

    <!-- Core Declaration Box -->
    <div class="p-8 rounded-3xl bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 space-y-3">
      <h3 class="text-base font-bold text-teal-900 dark:text-teal-200">Our Fundamental Promise: Zero Patient Data on Cloud</h3>
      <p class="text-xs sm:text-sm text-teal-800 dark:text-teal-300 leading-relaxed">
        Aarozi Healthcare operates on an offline-first architecture. When your diagnostic laboratory uses the Aarozi LIS desktop software, <strong>100% of patient demographics, clinical results, medical histories, invoices, and diagnostic images remain stored locally on your physical Master PC.</strong> Aarozi Healthcare’s public servers do not, and can not, receive or inspect patient data.
      </p>
    </div>

    <!-- Policy Articles -->
    <div class="space-y-8 text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">1. Information Collected on the Marketing & Portal Website</h2>
        <p>When you register as a laboratory owner on https://www.labs.aarozi.in/ or purchase a license, we collect only the commercial account information required to administer your order:</p>
        <ul class="list-disc pl-5 space-y-1.5">
          <li>Laboratory / Medical Facility Name</li>
          <li>Authorized Contact Person Name</li>
          <li>Mobile Number and Email Address (for OTP login and license delivery)</li>
          <li>State, City, and optional GSTIN (for tax compliance and billing invoices)</li>
          <li>Unique Machine ID (hardware hash for cryptographic license key generation)</li>
        </ul>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">2. Medical Records and Diagnostic Privacy</h2>
        <p>The Aarozi LIS software installed on your computer does not transmit clinical data over the internet. All database read and write operations take place exclusively on your local area network (LAN). We do not implement telemetry trackers, keystroke monitors, or cloud patient synchronization in the core LIS.</p>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">3. Cryptographic Verification & QR Codes</h2>
        <p>QR codes printed on patient reports contain an Ed25519 cryptographic signature generated locally by your Master PC. When scanned, the signature verifies test integrity mathematically without pinging a central cloud database.</p>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">4. Payment Processing Security</h2>
        <p>Online payments for software licenses are processed through certified, RBI-authorized Indian payment gateways (Razorpay / Cashfree) over TLS 1.3 encryption. Aarozi never stores debit/credit card numbers or UPI MPINs on its servers.</p>
      </section>

      <section class="space-y-3">
        <h2 class="text-base font-bold text-slate-900 dark:text-white">5. Contact Our Data Protection Officer</h2>
        <p>For any inquiries regarding your commercial account data or privacy rights, please contact our team at <a href="mailto:privacy@aarozi.in" class="text-teal-600 font-bold hover:underline">privacy@aarozi.in</a>.</p>
      </section>
    </div>

    <CtaBanner />
  </div>
</template>

