<script setup lang="ts">
import { ref, computed } from 'vue'

definePageMeta({
  layout: 'marketing',
})

const isAnnual = ref(true)
const couponInput = ref('')
const appliedCoupon = ref('')
const discountPercent = ref(0)
const isCheckoutOpen = ref(false)
const selectedPlan = ref('YEARLY_PRO')

// Checkout Form State
const checkoutForm = ref({
  lab_name: '',
  contact_name: '',
  email: '',
  phone: '',
  gstin: '',
})

const isSubmitting = ref(false)
const checkoutSuccess = ref<any>(null)

const activeTab = ref('pathology')

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
    alert('Invalid coupon code. Try AAROZI2026 or EARLYBIRD')
  }
}

function openCheckout(planCode: string) {
  selectedPlan.value = planCode
  isAnnual.value = planCode === 'YEARLY_PRO'
  isCheckoutOpen.value = true
}

async function handleCheckoutSubmit() {
  if (!checkoutForm.value.lab_name || !checkoutForm.value.email || !checkoutForm.value.phone) {
    alert('Please enter your Laboratory Name, Email, and Phone Number.')
    return
  }

  isSubmitting.value = true
  try {
    const res = await fetch('/payments/create-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lab_name: checkoutForm.value.lab_name,
        contact_name: checkoutForm.value.contact_name || checkoutForm.value.lab_name,
        email: checkoutForm.value.email,
        phone: checkoutForm.value.phone,
        gstin: checkoutForm.value.gstin || null,
        plan_code: selectedPlan.value,
        coupon_code: appliedCoupon.value || null,
      }),
    })
    const orderData = await res.json()

    // Simulate instant test checkout completion for demonstration
    const simRes = await fetch('/payments/webhook/razorpay', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event: 'payment.captured',
        event_id: `evt_${Date.now()}`,
        order_id: orderData.order_id,
        payload: {
          payment: {
            entity: {
              id: `pay_${Date.now()}`,
              order_id: orderData.order_id,
              method: 'upi',
            },
          },
        },
      }),
    })

    const updatedOrderRes = await fetch(`/payments/order/${orderData.order_id}`)
    checkoutSuccess.value = await updatedOrderRes.json()
  } catch (err) {
    alert('Checkout failed. Please ensure the backend server is running.')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-white text-slate-900 font-sans antialiased selection:bg-teal-500 selection:text-white">

    <!-- Hero Section -->
    <section class="relative pt-20 pb-16 overflow-hidden bg-gradient-to-b from-slate-50/70 to-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        <div class="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold mb-6">
          <span class="w-2 h-2 rounded-full bg-indigo-600 animate-pulse"></span>
          <span>100% Offline-First LIS &bull; Engineered for 10,000+ Indian Diagnostic Centers</span>
        </div>

        <h1 class="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-[1.15]">
          The Next-Generation Diagnostic Laboratory <span class="bg-gradient-to-r from-indigo-600 to-indigo-700 bg-clip-text text-transparent">Operating System</span>.
        </h1>

        <p class="mt-6 text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          From high-speed patient registration and Mindray/Cobas analyzer interfacing to 1-click doctor sign-offs, thermal barcoding, and WhatsApp reports. Operates <strong>100% offline</strong> over your clinic's local LAN.
        </p>

        <!-- CTA Buttons -->
        <div class="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          <a
            href="#pricing"
            class="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-md shadow-indigo-200 transition"
          >
            <span>Get Commercial License</span>
            <span>&rarr;</span>
          </a>
          <NuxtLink
            to="/dashboard"
            class="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold border border-slate-200 shadow-xs transition"
          >
            <span>Explore Live Lab Workstation</span>
          </NuxtLink>
        </div>

        <!-- Trust Features Bar -->
        <div class="mt-12 pt-8 border-t border-slate-200/60 max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-medium text-slate-500">
          <div class="flex items-center justify-center space-x-2">
            <span class="text-emerald-500 font-bold text-base">&check;</span>
            <span>100% Offline Local Server</span>
          </div>
          <div class="flex items-center justify-center space-x-2">
            <span class="text-emerald-500 font-bold text-base">&check;</span>
            <span>50+ Analyzers Supported</span>
          </div>
          <div class="flex items-center justify-center space-x-2">
            <span class="text-emerald-500 font-bold text-base">&check;</span>
            <span>Ed25519 Cryptographic Security</span>
          </div>
          <div class="flex items-center justify-center space-x-2">
            <span class="text-emerald-500 font-bold text-base">&check;</span>
            <span>India DPDP Act Compliant</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Interactive Workstation Showcase -->
    <section class="py-16 bg-white border-y border-slate-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-3xl mx-auto mb-10">
          <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Designed for Speed at the Phlebotomy &amp; Doctor Desk
          </h2>
          <p class="text-sm text-slate-500 mt-2">
            No lag, no buffering, and no internet spinning wheels. Built with FAANG keyboard shortcuts for rapid patient turnover.
          </p>
        </div>

        <!-- Interactive Tabs -->
        <div class="flex justify-center border-b border-slate-200 mb-8 space-x-2 overflow-x-auto pb-2">
          <button
            type="button"
            class="px-4 py-2 text-xs font-semibold rounded-lg transition"
            :class="activeTab === 'pathology' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'"
            @click="activeTab = 'pathology'"
          >
            Pathology &amp; Quick Workstation
          </button>
          <button
            type="button"
            class="px-4 py-2 text-xs font-semibold rounded-lg transition"
            :class="activeTab === 'analyzers' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'"
            @click="activeTab = 'analyzers'"
          >
            Analyzer Interfacing (ASTM/HL7)
          </button>
          <button
            type="button"
            class="px-4 py-2 text-xs font-semibold rounded-lg transition"
            :class="activeTab === 'bloodbank' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'"
            @click="activeTab = 'bloodbank'"
          >
            Blood Bank &amp; Cross-Match
          </button>
          <button
            type="button"
            class="px-4 py-2 text-xs font-semibold rounded-lg transition"
            :class="activeTab === 'billing' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'"
            @click="activeTab = 'billing'"
          >
            Cashier Billing &amp; Invoicing
          </button>
        </div>

        <!-- Tab Content Display -->
        <div class="bg-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl shadow-slate-200 border border-slate-800">
          <div v-if="activeTab === 'pathology'" class="space-y-4">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span class="text-xs uppercase font-bold text-indigo-400">Pathology Result Desk</span>
                <h3 class="text-lg font-bold text-slate-100">Keyboard-Accelerated Result Entry &amp; Automatic Panic Range Highlighting</h3>
              </div>
              <NuxtLink to="/pathology/results" class="text-xs text-indigo-400 hover:text-indigo-300 font-semibold">&rarr; Open Workstation</NuxtLink>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
                <span class="text-slate-400">Sample Barcode</span>
                <p class="font-mono text-emerald-400 font-bold mt-1 text-sm">SMP-2026-BIO-0914</p>
                <span class="inline-block mt-2 px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 text-[10px]">Plasma EDTA</span>
              </div>
              <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
                <span class="text-slate-400">Doctor Verification</span>
                <p class="font-semibold text-slate-200 mt-1">Dr. S. Mehta, MD (Pathology)</p>
                <span class="inline-block mt-2 px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 text-[10px]">Digital Signature Embedded</span>
              </div>
              <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
                <span class="text-slate-400">Clinical Audit Trail</span>
                <p class="font-mono text-slate-300 mt-1 text-[11px]">Event #4810 &bull; Timestamp Verified</p>
                <span class="inline-block mt-2 px-2 py-0.5 rounded bg-slate-700 text-slate-200 text-[10px]">Immutable History</span>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'analyzers'" class="space-y-4">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span class="text-xs uppercase font-bold text-emerald-400">Analyzer Connector Service</span>
                <h3 class="text-lg font-bold text-slate-100">Direct Serial (RS-232 COM) &amp; Ethernet TCP/IP ASTM Driver</h3>
              </div>
              <NuxtLink to="/pathology/instruments" class="text-xs text-emerald-400 hover:text-emerald-300 font-semibold">&rarr; Instruments Catalog</NuxtLink>
            </div>
            <p class="text-xs text-slate-400 leading-relaxed">
              Connect your Mindray BC-5000, Erba Chem-7, Roche Cobas, and Sysmex analyzers. Test results are fetched directly into patient sample records without manual technician transcription error.
            </p>
          </div>

          <div v-if="activeTab === 'bloodbank'" class="space-y-4">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span class="text-xs uppercase font-bold text-rose-400">Blood Bank &amp; Transfusion Safety</span>
                <h3 class="text-lg font-bold text-slate-100">Donor Registration, Serology Screening &amp; Cross-Match Issue</h3>
              </div>
              <NuxtLink to="/blood_bank/inventory" class="text-xs text-rose-400 hover:text-rose-300 font-semibold">&rarr; Blood Inventory</NuxtLink>
            </div>
            <p class="text-xs text-slate-400 leading-relaxed">
              Full cold-chain tracking for PRBC, FFP, and Platelet Concentrates. Strict TTI (Transfusion-Transmissible Infection) clearance before release.
            </p>
          </div>

          <div v-if="activeTab === 'billing'" class="space-y-4">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span class="text-xs uppercase font-bold text-amber-400">Cashier Billing &amp; Taxation</span>
                <h3 class="text-lg font-bold text-slate-100">Instant GST Invoicing, Referral Partner Cut &amp; Dual Print Desk</h3>
              </div>
              <NuxtLink to="/billing/invoices" class="text-xs text-amber-400 hover:text-amber-300 font-semibold">&rarr; Invoice Manager</NuxtLink>
            </div>
            <p class="text-xs text-slate-400 leading-relaxed">
              Complete accounts ledger with automatic B2B/B2C GST tax calculation, split cash/UPI tracking, and referral doctor incentive ledgers.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Pricing Section -->
    <section id="pricing" class="py-20 bg-slate-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-3xl mx-auto mb-12">
          <span class="text-xs font-bold uppercase tracking-wider text-indigo-600">Transparent Indian Pricing</span>
          <h2 class="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mt-1">
            Choose Your Laboratory License
          </h2>
          <p class="text-sm text-slate-600 mt-2">
            One License = One Laboratory Organization / Local Master Server. Connect unlimited workstations on your clinic LAN.
          </p>

          <!-- Toggle -->
          <div class="mt-8 flex items-center justify-center space-x-3">
            <span class="text-xs font-semibold" :class="isAnnual ? 'text-indigo-600 font-bold' : 'text-slate-500'">Yearly Plan</span>
            <button
              type="button"
              class="w-12 h-6 rounded-full p-1 transition bg-indigo-600 relative cursor-pointer"
              @click="isAnnual = !isAnnual"
            >
              <div
                class="w-4 h-4 rounded-full bg-white transition-transform"
                :class="isAnnual ? 'translate-x-0' : 'translate-x-6'"
              ></div>
            </button>
            <span class="text-xs font-semibold" :class="!isAnnual ? 'text-indigo-600 font-bold' : 'text-slate-500'">
              Lifetime License <span class="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-bold ml-1">POPULAR</span>
            </span>
          </div>
        </div>

        <!-- Pricing Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <!-- Card 1: Yearly Subscription -->
          <div class="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm hover:shadow-md transition relative flex flex-col justify-between">
            <div>
              <div class="flex justify-between items-start">
                <div>
                  <h3 class="text-lg font-bold text-slate-900">Yearly Subscription</h3>
                  <p class="text-xs text-slate-500 mt-0.5">Annual subscription with continuous software updates</p>
                </div>
                <span class="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                  Annual OPEX
                </span>
              </div>

              <div class="mt-6 flex items-baseline">
                <span class="text-4xl font-extrabold text-slate-900">₹14,999</span>
                <span class="text-xs text-slate-500 ml-2">/ year (+ 18% GST)</span>
              </div>
              <p class="text-[11px] text-emerald-600 font-medium mt-1">Approx. ₹1,250 / month &bull; Billed annually</p>

              <ul class="mt-8 space-y-3 text-xs text-slate-600">
                <li class="flex items-center space-x-2"><span class="text-indigo-600 font-bold">&check;</span><span>All 9 Clinical Modules Included</span></li>
                <li class="flex items-center space-x-2"><span class="text-indigo-600 font-bold">&check;</span><span>Unlimited LAN Workstations (Same Lab)</span></li>
                <li class="flex items-center space-x-2"><span class="text-indigo-600 font-bold">&check;</span><span>Automated Mindray / Cobas Interfacing</span></li>
                <li class="flex items-center space-x-2"><span class="text-indigo-600 font-bold">&check;</span><span>30-Day Soft Renewal Grace Period</span></li>
                <li class="flex items-center space-x-2"><span class="text-indigo-600 font-bold">&check;</span><span>Free Version Updates during Subscription</span></li>
                <li class="flex items-center space-x-2"><span class="text-indigo-600 font-bold">&check;</span><span>Local Encrypted Database Backups</span></li>
              </ul>
            </div>

            <button
              type="button"
              class="mt-8 w-full py-3 px-4 rounded-xl text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 transition border border-indigo-200 cursor-pointer"
              @click="openCheckout('YEARLY_PRO')"
            >
              Select Yearly License
            </button>
          </div>

          <!-- Card 2: Lifetime License -->
          <div class="bg-white rounded-2xl p-8 border-2 border-indigo-600 shadow-md relative flex flex-col justify-between">
            <div class="absolute -top-3 right-6 bg-indigo-600 text-white text-[10px] font-bold uppercase tracking-wider px-3 py-0.5 rounded-full shadow-xs">
              Best Long-Term Value
            </div>

            <div>
              <div class="flex justify-between items-start">
                <div>
                  <h3 class="text-lg font-bold text-slate-900">Lifetime License</h3>
                  <p class="text-xs text-slate-500 mt-0.5">One-time payment for permanent offline use</p>
                </div>
              </div>

              <div class="mt-6 flex items-baseline">
                <span class="text-4xl font-extrabold text-slate-900">₹39,999</span>
                <span class="text-xs text-slate-500 ml-2">one-time (+ 18% GST)</span>
              </div>
              <p class="text-[11px] text-indigo-600 font-medium mt-1">Zero recurring license fees &bull; Own your LIS forever</p>

              <ul class="mt-8 space-y-3 text-xs text-slate-600">
                <li class="flex items-center space-x-2"><span class="text-emerald-600 font-bold">&check;</span><span>Perpetual Offline License (Never Expires)</span></li>
                <li class="flex items-center space-x-2"><span class="text-emerald-600 font-bold">&check;</span><span>Zero Recurring Monthly or Yearly Software Rent</span></li>
                <li class="flex items-center space-x-2"><span class="text-emerald-600 font-bold">&check;</span><span>All Clinical Modules (Pathology, Blood Bank, Billing)</span></li>
                <li class="flex items-center space-x-2"><span class="text-emerald-600 font-bold">&check;</span><span>Unlimited LAN Workstations on Lab Network</span></li>
                <li class="flex items-center space-x-2"><span class="text-emerald-600 font-bold">&check;</span><span>1 Year of Included Software Updates (v1.x)</span></li>
                <li class="flex items-center space-x-2"><span class="text-emerald-600 font-bold">&check;</span><span>Priority Telephonic &amp; Remote Desk Support</span></li>
              </ul>
            </div>

            <button
              type="button"
              class="mt-8 w-full py-3 px-4 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition shadow-indigo-200 cursor-pointer"
              @click="openCheckout('LIFETIME_ENTERPRISE')"
            >
              Buy Lifetime License
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- FAQ Section -->
    <section id="faq" class="py-16 bg-white border-t border-slate-100">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-2xl font-extrabold text-slate-900 text-center tracking-tight mb-8">
          Frequently Asked Questions by Laboratory Owners
        </h2>

        <div class="space-y-4 text-xs">
          <div class="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h4 class="font-bold text-slate-900">Does Aarozi Healthcare work without an internet connection?</h4>
            <p class="mt-1 text-slate-600 leading-relaxed">
              Yes. Aarozi is built offline-first. Patient registration, billing, barcode printing, analyzer data ingestion, and report verification all run on your local master PC. An internet connection is only needed during initial license download or optional cloud backup.
            </p>
          </div>

          <div class="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h4 class="font-bold text-slate-900">How do multiple computers connect in my lab?</h4>
            <p class="mt-1 text-slate-600 leading-relaxed">
              Your main computer runs the Aarozi server. All other computers (reception, doctor desk, phlebotomy) simply open Chrome or Edge and enter the server's local IP address (e.g. <code>http://192.168.1.50:8000</code>). You do NOT need to buy separate licenses for each workstation.
            </p>
          </div>

          <div class="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h4 class="font-bold text-slate-900">What happens to our patient data if our subscription expires?</h4>
            <p class="mt-1 text-slate-600 leading-relaxed">
              Your patient records and financial data are <strong>never deleted or locked</strong>. If a yearly subscription expires past its 30-day grace period, the system enters a read-only mode where you can view, print, search, and export all historical records indefinitely until you choose to renew.
            </p>
          </div>

          <div class="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h4 class="font-bold text-slate-900">What if my server computer's hard drive crashes?</h4>
            <p class="mt-1 text-slate-600 leading-relaxed">
              You can restore your database instantly from your daily external USB backup. You can transfer your commercial license to a new PC up to twice per year directly from your online Customer Portal.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Checkout Modal -->
    <div v-if="isCheckoutOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="font-bold text-slate-900 text-sm">
            {{ isAnnual ? 'Yearly Commercial Subscription' : 'Lifetime Commercial License' }} Checkout
          </h3>
          <button type="button" class="text-slate-400 hover:text-slate-600 text-lg cursor-pointer" @click="isCheckoutOpen = false">&times;</button>
        </div>

        <div v-if="!checkoutSuccess" class="mt-4 space-y-4">
          <!-- Pricing Summary Box -->
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1.5">
            <div class="flex justify-between text-slate-600">
              <span>Base License Fee:</span>
              <span class="font-semibold text-slate-900">₹{{ currentBasePrice.toLocaleString('en-IN') }}</span>
            </div>
            <div v-if="discountAmount > 0" class="flex justify-between text-emerald-600 font-medium">
              <span>Discount ({{ appliedCoupon }} - {{ discountPercent }}%):</span>
              <span>-₹{{ discountAmount.toLocaleString('en-IN') }}</span>
            </div>
            <div class="flex justify-between text-slate-600">
              <span>GST (18%):</span>
              <span>₹{{ gstAmount.toLocaleString('en-IN') }}</span>
            </div>
            <div class="flex justify-between text-slate-900 font-bold border-t border-slate-200 pt-1.5 text-sm">
              <span>Total Payable:</span>
              <span class="text-indigo-600">₹{{ totalPayable.toLocaleString('en-IN') }}</span>
            </div>
          </div>

          <!-- Coupon Input -->
          <div class="flex space-x-2">
            <input
              v-model="couponInput"
              type="text"
              placeholder="Coupon Code (e.g. AAROZI2026)"
              class="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-xs uppercase focus:ring-1 focus:ring-indigo-500 focus:outline-hidden"
            />
            <button
              type="button"
              class="px-3 py-2 bg-slate-800 text-white text-xs font-semibold rounded-lg hover:bg-slate-900 transition cursor-pointer"
              @click="applyCoupon"
            >
              Apply
            </button>
          </div>

          <!-- Laboratory Registration Form -->
          <div class="space-y-3 text-xs">
            <div>
              <label class="block font-medium text-slate-700 mb-1">Diagnostic Laboratory Name *</label>
              <input
                v-model="checkoutForm.lab_name"
                type="text"
                required
                placeholder="e.g. Apex Clinical Pathology & Diagnostic Center"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-hidden"
              />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block font-medium text-slate-700 mb-1">Doctor / Owner Name</label>
                <input
                  v-model="checkoutForm.contact_name"
                  type="text"
                  placeholder="Dr. R. Sharma"
                  class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>
              <div>
                <label class="block font-medium text-slate-700 mb-1">Mobile / WhatsApp *</label>
                <input
                  v-model="checkoutForm.phone"
                  type="tel"
                  required
                  placeholder="9876543210"
                  class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>
            </div>

            <div>
              <label class="block font-medium text-slate-700 mb-1">Official Email Address *</label>
              <input
                v-model="checkoutForm.email"
                type="email"
                required
                placeholder="contact@apexdiagnostics.com"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 focus:outline-hidden"
              />
            </div>

            <div>
              <label class="block font-medium text-slate-700 mb-1">GSTIN Number (Optional for Tax Invoice)</label>
              <input
                v-model="checkoutForm.gstin"
                type="text"
                placeholder="27ABCDE1234F1Z5"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg uppercase focus:ring-1 focus:ring-indigo-500 focus:outline-hidden"
              />
            </div>
          </div>

          <button
            type="button"
            :disabled="isSubmitting"
            class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-xs shadow-md shadow-indigo-100 transition cursor-pointer"
            @click="handleCheckoutSubmit"
          >
            <span v-if="!isSubmitting">Pay ₹{{ totalPayable.toLocaleString('en-IN') }} via UPI / Cards / NetBanking</span>
            <span v-else>Processing Order &amp; Issuing License...</span>
          </button>
        </div>

        <!-- Success & Instant License Issuance Screen -->
        <div v-else class="mt-4 text-center space-y-4">
          <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto text-xl font-bold">
            &check;
          </div>
          <div>
            <h4 class="font-bold text-slate-900 text-base">Payment Confirmed &amp; License Issued!</h4>
            <p class="text-xs text-slate-500 mt-1">Invoice: {{ checkoutSuccess.invoice_number }} &bull; Order: {{ checkoutSuccess.order_id }}</p>
          </div>

          <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-left text-xs font-mono space-y-1">
            <p><span class="text-slate-400">Lab:</span> {{ checkoutSuccess.lab_name }}</p>
            <p><span class="text-slate-400">License ID:</span> {{ checkoutSuccess.issued_license_id }}</p>
            <p><span class="text-slate-400">Plan:</span> {{ checkoutSuccess.totals.plan_name }}</p>
            <p><span class="text-slate-400">Status:</span> <span class="text-emerald-600 font-bold uppercase">Active Commercial</span></p>
          </div>

          <div class="space-y-2 pt-2">
            <a
              :href="`/payments/order/${checkoutSuccess.order_id}/download-license`"
              class="w-full block py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-xs transition"
              download
            >
              Download License (.lic) File
            </a>
            <NuxtLink
              to="/customer/dashboard"
              class="w-full block py-2 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
            >
              Go to Customer Portal &rarr;
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="bg-slate-900 text-slate-400 py-12 text-xs border-t border-slate-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center space-x-2">
          <span class="font-bold text-white">Aarozi Healthcare Systems</span>
          <span>&mdash; Modern Diagnostic Laboratory &amp; Blood Bank LIS</span>
        </div>
        <div class="flex items-center space-x-6 text-[11px]">
          <NuxtLink to="/customer/dashboard" class="hover:text-white transition">Customer Portal</NuxtLink>
          <NuxtLink to="/admin/commercial" class="hover:text-white transition">Vendor Admin</NuxtLink>
          <a href="#pricing" class="hover:text-white transition">Pricing</a>
          <a href="#faq" class="hover:text-white transition">Support</a>
        </div>
      </div>
    </footer>
  </div>
</template>
