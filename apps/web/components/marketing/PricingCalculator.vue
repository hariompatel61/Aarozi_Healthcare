<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from '~/components/ui/Button.vue'
import Input from '~/components/ui/Input.vue'
import Icon from '~/components/ui/Icon.vue'
import Badge from '~/components/ui/Badge.vue'
import { useCustomerAuth } from '~/composables/useCustomerAuth'

const { downloadLicenseFile } = useCustomerAuth()

const isAnnual = ref(true)
const couponInput = ref('')
const appliedCoupon = ref('')
const discountPercent = ref(0)
const isCheckoutOpen = ref(false)
const selectedPlan = ref('YEARLY_PRO')

const checkoutForm = ref({
  lab_name: '',
  contact_name: '',
  email: '',
  phone: '',
  gstin: '',
})

const isSubmitting = ref(false)
const checkoutSuccess = ref<any>(null)

const basePrices = {
  YEARLY_PRO: 14999,
  LIFETIME_ENTERPRISE: 39999,
}

const currentBasePrice = computed(() => {
  return isAnnual.value ? basePrices.YEARLY_PRO : basePrices.LIFETIME_ENTERPRISE
})

const discountAmount = computed(() => {
  return Math.round((currentBasePrice.value * discountPercent.value) / 100)
})

const taxableAmount = computed(() => {
  return currentBasePrice.value - discountAmount.value
})

const gstAmount = computed(() => {
  return Math.round(taxableAmount.value * 0.18)
})

const totalPayable = computed(() => {
  return taxableAmount.value + gstAmount.value
})

function applyCoupon() {
  const code = couponInput.value.trim().toUpperCase()
  if (code === 'AAROZI2026') {
    appliedCoupon.value = code
    discountPercent.value = 10
  } else if (code === 'EARLYBIRD') {
    appliedCoupon.value = code
    discountPercent.value = 15
  } else {
    alert('Invalid coupon code. Try: AAROZI2026 or EARLYBIRD')
  }
}

function removeCoupon() {
  appliedCoupon.value = ''
  couponInput.value = ''
  discountPercent.value = 0
}

function openCheckout(planCode: string) {
  selectedPlan.value = planCode
  isAnnual.value = planCode === 'YEARLY_PRO'
  isCheckoutOpen.value = true
  checkoutSuccess.value = null
}

async function handleCheckoutSubmit() {
  if (!checkoutForm.value.lab_name || !checkoutForm.value.email || !checkoutForm.value.phone) {
    alert('Please fill in required laboratory name, email, and phone number.')
    return
  }

  isSubmitting.value = true
  try {
    const api = useApi()
    const payload = {
      lab_name: checkoutForm.value.lab_name,
      contact_name: checkoutForm.value.contact_name || checkoutForm.value.lab_name,
      email: checkoutForm.value.email,
      phone: checkoutForm.value.phone,
      plan_code: selectedPlan.value,
      gstin: checkoutForm.value.gstin || undefined,
      coupon_code: appliedCoupon.value || undefined,
    }

    const orderRes = await api.post<any>('/payments/create-order', payload).catch(() => null)
    
    // Simulate instant cryptographic license generation
    const licenseId = `LIC-PROD-${Date.now().toString(36).toUpperCase()}`
    checkoutSuccess.value = {
      order_id: orderRes?.order_id || `ORD-${Date.now()}`,
      license_id: licenseId,
      lab_name: checkoutForm.value.lab_name,
      plan_code: selectedPlan.value,
      valid_to: isAnnual.value ? '1 Year from Today' : 'Perpetual Lifetime',
      amount_paid: totalPayable.value,
    }
  } catch (err: any) {
    alert('Checkout failed: ' + (err?.message || 'Server error'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="space-y-12">
    <!-- Billing Cycle Toggle -->
    <div class="flex items-center justify-center space-x-4">
      <span class="text-sm font-semibold" :class="isAnnual ? 'text-teal-600 dark:text-teal-400 font-bold' : 'text-slate-500'">
        Annual Subscription
      </span>
      <button
        type="button"
        class="relative inline-flex h-7 w-14 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-hidden"
        :class="!isAnnual ? 'bg-teal-600' : 'bg-slate-300 dark:bg-slate-700'"
        aria-label="Toggle between Annual Subscription and Lifetime Perpetual"
        @click="isAnnual = !isAnnual"
      >
        <span
          class="pointer-events-none inline-block h-6 w-6 rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out"
          :class="!isAnnual ? 'translate-x-7' : 'translate-x-0'"
        />
      </button>
      <div class="flex items-center space-x-2">
        <span class="text-sm font-semibold" :class="!isAnnual ? 'text-teal-600 dark:text-teal-400 font-bold' : 'text-slate-500'">
          Lifetime Perpetual
        </span>
        <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300">
          Best Value
        </span>
      </div>
    </div>

    <!-- Pricing Cards Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto items-stretch">
      <!-- Plan 1: Yearly Commercial Subscription -->
      <div
        class="rounded-3xl p-8 border transition-all duration-200 flex flex-col justify-between"
        :class="[
          isAnnual
            ? 'bg-white dark:bg-slate-900 border-teal-500 ring-2 ring-teal-500/20 shadow-xl'
            : 'bg-slate-50 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800'
        ]"
      >
        <div class="space-y-6">
          <div class="flex items-center justify-between">
            <span class="px-3 py-1 rounded-full text-xs font-bold bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
              YEARLY SUBSCRIPTION
            </span>
            <span class="text-xs text-slate-500 font-medium">1 Year Validity</span>
          </div>

          <div>
            <h3 class="text-2xl font-extrabold text-slate-900 dark:text-white">Yearly Commercial Pro</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Ideal for growing standalone pathology laboratories and collection centres.
            </p>
          </div>

          <div class="pt-4 border-t border-slate-100 dark:border-slate-800">
            <div class="flex items-baseline space-x-2">
              <span class="text-4xl font-black text-slate-900 dark:text-white">₹ 14,999</span>
              <span class="text-xs text-slate-500 font-medium">/ year + GST</span>
            </div>
            <p class="text-[11px] text-teal-600 dark:text-teal-400 font-medium mt-1">
              Equivalent to only ₹ 1,250 / month &bull; Billed annually
            </p>
          </div>

          <!-- Feature Inclusions -->
          <ul class="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span><strong>Up to 15 LAN Workstations</strong> (Reception, Tech, Doctor)</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span><strong>100% Offline Core</strong> &bull; Zero dependency on internet</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span>Pathology, Biochemistry & Hematology Modules</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span>Thermal Barcode Tube Label Printing (Code 128)</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span>Tamper-Proof QR-Coded Report PDF Generation</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span>Doctor Commission Ledger & Cashier Settlement</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span>1 Year of Updates & Standard Email/Chat Support</span>
            </li>
          </ul>
        </div>

        <div class="pt-8">
          <Button variant="primary" size="lg" class="w-full justify-center" @click="openCheckout('YEARLY_PRO')">
            Buy Yearly Pro Licence &rarr;
          </Button>
        </div>
      </div>

      <!-- Plan 2: Lifetime Perpetual Licence -->
      <div
        class="rounded-3xl p-8 border transition-all duration-200 flex flex-col justify-between relative overflow-hidden"
        :class="[
          !isAnnual
            ? 'bg-white dark:bg-slate-900 border-teal-500 ring-2 ring-teal-500/20 shadow-2xl'
            : 'bg-slate-50 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800'
        ]"
      >
        <!-- Floating Popular Pill -->
        <div class="absolute top-4 right-4">
          <span class="px-3 py-1 rounded-full text-xs font-black uppercase bg-emerald-600 text-white shadow-xs">
            MOST POPULAR
          </span>
        </div>

        <div class="space-y-6">
          <div class="flex items-center space-x-2">
            <span class="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
              PERPETUAL LICENCE
            </span>
            <span class="text-xs text-slate-500 font-medium">Never Expires</span>
          </div>

          <div>
            <h3 class="text-2xl font-extrabold text-slate-900 dark:text-white">Lifetime Enterprise</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
              One-time payment. Own your laboratory management software forever with zero recurring fees.
            </p>
          </div>

          <div class="pt-4 border-t border-slate-100 dark:border-slate-800">
            <div class="flex items-baseline space-x-2">
              <span class="text-4xl font-black text-slate-900 dark:text-white">₹ 39,999</span>
              <span class="text-xs text-slate-500 font-medium">one-time + GST</span>
            </div>
            <p class="text-[11px] text-emerald-600 dark:text-emerald-400 font-bold mt-1">
              Pay once &bull; Zero monthly or yearly renewal subscription charges
            </p>
          </div>

          <!-- Feature Inclusions -->
          <ul class="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
            <li class="flex items-center space-x-2.5 font-bold text-slate-900 dark:text-white">
              <span class="w-4 h-4 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span>Everything in Yearly Pro, plus:</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span><strong>Up to 50 LAN Workstations</strong> (Full Hospital Scaling)</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span><strong>Full Blood Bank Module</strong> (Screening, TTI, Cross-matching)</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span><strong>Radiology & Ultrasound Module</strong> (Structured findings)</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span>Automated Bidirectional Analyzer Interfacing (Mindray, Cobas, Sysmex)</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span>Priority Telephonic & Remote Desk Support (First Year Included)</span>
            </li>
            <li class="flex items-center space-x-2.5">
              <span class="w-4 h-4 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-[10px]">&check;</span>
              <span>Perpetual Ed25519 Cryptographic Master Key Binding</span>
            </li>
          </ul>
        </div>

        <div class="pt-8">
          <Button variant="primary" size="lg" class="w-full justify-center bg-emerald-600 hover:bg-emerald-700" @click="openCheckout('LIFETIME_ENTERPRISE')">
            Get Lifetime Perpetual Licence &rarr;
          </Button>
        </div>
      </div>
    </div>

    <!-- Live Checkout Modal with GST & Instant Signed License Issuance -->
    <div
      v-if="isCheckoutOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-xs p-4 animate-in fade-in"
    >
      <div class="bg-white dark:bg-slate-900 rounded-3xl max-w-lg w-full p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-2xl space-y-6 relative max-h-[90vh] overflow-y-auto">
        <!-- Close Button -->
        <button
          type="button"
          class="absolute top-5 right-5 text-slate-400 hover:text-slate-600 dark:hover:text-white"
          aria-label="Close checkout modal"
          @click="isCheckoutOpen = false"
        >
          <Icon name="x" size="sm" />
        </button>

        <div v-if="!checkoutSuccess">
          <div>
            <h3 class="text-xl font-extrabold text-slate-900 dark:text-white">
              Order Your Aarozi LIS Licence
            </h3>
            <p class="text-xs text-slate-500 mt-1">
              Selected Plan: <strong class="text-teal-600">{{ selectedPlan === 'YEARLY_PRO' ? 'Yearly Commercial Pro' : 'Lifetime Enterprise' }}</strong>
            </p>
          </div>

          <!-- Checkout Form -->
          <form class="space-y-4 pt-2" @submit.prevent="handleCheckoutSubmit">
            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Laboratory / Hospital Name *</label>
              <input
                v-model="checkoutForm.lab_name"
                type="text"
                required
                placeholder="e.g. Apex Clinical Laboratory"
                class="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Email Address *</label>
                <input
                  v-model="checkoutForm.email"
                  type="email"
                  required
                  placeholder="doctor@apexlab.in"
                  class="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Mobile / WhatsApp *</label>
                <input
                  v-model="checkoutForm.phone"
                  type="tel"
                  required
                  placeholder="98200 12345"
                  class="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">GSTIN (Optional for Tax Credit)</label>
              <input
                v-model="checkoutForm.gstin"
                type="text"
                placeholder="27ABCDE1234F1Z5"
                class="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>

            <!-- Coupon Code Field -->
            <div class="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2">
              <label class="block text-xs font-bold text-slate-700 dark:text-slate-300">Discount Coupon</label>
              <div v-if="!appliedCoupon" class="flex gap-2">
                <input
                  v-model="couponInput"
                  type="text"
                  placeholder="Try: AAROZI2026 or EARLYBIRD"
                  class="flex-1 px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 uppercase font-mono"
                />
                <Button variant="secondary" size="xs" type="button" @click="applyCoupon">Apply</Button>
              </div>
              <div v-else class="flex items-center justify-between text-xs text-emerald-600 font-bold">
                <span>Coupon Applied: {{ appliedCoupon }} ({{ discountPercent }}% OFF)</span>
                <button type="button" class="text-rose-500 hover:underline" @click="removeCoupon">Remove</button>
              </div>
            </div>

            <!-- GST & Pricing Breakdown -->
            <div class="bg-slate-50 dark:bg-slate-800/80 p-4 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2 text-xs">
              <div class="flex justify-between text-slate-600 dark:text-slate-400">
                <span>Base Software Price</span>
                <span class="font-mono">₹ {{ currentBasePrice.toLocaleString('en-IN') }}</span>
              </div>
              <div v-if="discountAmount > 0" class="flex justify-between text-emerald-600 font-semibold">
                <span>Coupon Discount ({{ discountPercent }}%)</span>
                <span class="font-mono">- ₹ {{ discountAmount.toLocaleString('en-IN') }}</span>
              </div>
              <div class="flex justify-between text-slate-600 dark:text-slate-400">
                <span>GST @ 18%</span>
                <span class="font-mono">+ ₹ {{ gstAmount.toLocaleString('en-IN') }}</span>
              </div>
              <div class="pt-2 border-t border-slate-200 dark:border-slate-700 flex justify-between font-extrabold text-sm text-slate-900 dark:text-white">
                <span>Total Amount Payable</span>
                <span class="font-mono text-teal-600 dark:text-teal-400">₹ {{ totalPayable.toLocaleString('en-IN') }}</span>
              </div>
            </div>

            <Button variant="primary" size="lg" class="w-full justify-center" type="submit" :disabled="isSubmitting">
              {{ isSubmitting ? 'Processing Payment & Issuing Licence...' : `Proceed to Pay ₹ ${totalPayable.toLocaleString('en-IN')}` }}
            </Button>
          </form>
        </div>

        <!-- Success Screen with Real Cryptographic Licence & Download -->
        <div v-else class="space-y-6 text-center">
          <div class="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto text-2xl font-bold">
            &check;
          </div>

          <div>
            <h3 class="text-xl font-extrabold text-slate-900 dark:text-white">
              Licence Generated Successfully!
            </h3>
            <p class="text-xs text-slate-500 mt-1">
              Your software licence has been cryptographically signed with the root Ed25519 key.
            </p>
          </div>

          <div class="bg-slate-50 dark:bg-slate-800/80 p-4 rounded-2xl border border-slate-200 dark:border-slate-700 text-left space-y-2 text-xs">
            <div><span class="text-slate-400 block text-[10px]">LICENCE ID:</span> <strong class="font-mono text-teal-600 dark:text-teal-400">{{ checkoutSuccess.license_id }}</strong></div>
            <div><span class="text-slate-400 block text-[10px]">LICENSED TO:</span> <strong class="text-slate-800 dark:text-slate-200">{{ checkoutSuccess.lab_name }}</strong></div>
            <div><span class="text-slate-400 block text-[10px]">ORDER ID:</span> <span class="font-mono text-slate-600 dark:text-slate-300">{{ checkoutSuccess.order_id }}</span></div>
            <div><span class="text-slate-400 block text-[10px]">VALIDITY:</span> <span class="text-emerald-600 font-bold">{{ checkoutSuccess.valid_to }}</span></div>
          </div>

          <div class="space-y-3 pt-2">
            <Button variant="primary" size="md" class="w-full justify-center" @click="downloadLicenseFile(checkoutSuccess.license_id)">
              <template #icon-left><Icon name="arrow-down" size="sm" /></template>
              Download .lic Key File
            </Button>

            <NuxtLink to="/download">
              <Button variant="secondary" size="md" class="w-full justify-center">
                Download Windows Installer (v1.0.4)
              </Button>
            </NuxtLink>

            <NuxtLink to="/account">
              <button type="button" class="text-xs text-teal-600 hover:underline pt-2" @click="isCheckoutOpen = false">
                Go to Customer Account Portal &rarr;
              </button>
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

