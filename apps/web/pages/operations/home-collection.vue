<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '~/components/ui/PageHeader.vue'
import Card from '~/components/ui/Card.vue'
import Button from '~/components/ui/Button.vue'
import Badge from '~/components/ui/Badge.vue'
import Icon from '~/components/ui/Icon.vue'
import Modal from '~/components/ui/Modal.vue'
import Input from '~/components/ui/Input.vue'
import { useToast } from '~/composables/useToast'

const api = useApi()
const { success, error } = useToast()

const bookings = ref<any[]>([])
const loading = ref(false)
const filterStatus = ref<string>('')
const isBookModalOpen = ref(false)
const submitting = ref(false)

const newBooking = ref({
  patient_id: '',
  patient_name: '',
  contact_phone: '',
  appointment_date: new Date().toISOString().split('T')[0] + 'T08:00',
  time_slot: '07:30 AM - 08:30 AM',
  address: '',
  landmark: '',
  pincode: '201301',
  collection_charge: 150,
  notes: '',
})

async function fetchBookings() {
  loading.value = true
  try {
    const url = filterStatus.value ? `/home-collections?status=${filterStatus.value}` : '/home-collections'
    const res: any = await api.get(url)
    bookings.value = Array.isArray(res) ? res : []
  } catch (err: any) {
    error('Failed to load home collection bookings', err.message)
  } finally {
    loading.value = false
  }
}

async function updateStatus(bookingId: string, nextStatus: string) {
  try {
    await api.patch(`/home-collections/${bookingId}/status`, { status: nextStatus })
    success('Status Updated', `Booking moved to ${nextStatus}`)
    fetchBookings()
  } catch (err: any) {
    error('Update Failed', err.message)
  }
}

async function handleCreateBooking() {
  if (!newBooking.value.address || !newBooking.value.contact_phone) return
  submitting.value = true
  try {
    // If patient_id not specified, fetch first patient from directory or mock
    let patId = newBooking.value.patient_id
    if (!patId) {
      const pats: any = await api.get('/patients?limit=1')
      if (Array.isArray(pats) && pats.length > 0) {
        patId = pats[0].id
      }
    }
    await api.post('/home-collections', {
      ...newBooking.value,
      patient_id: patId,
      appointment_date: new Date(newBooking.value.appointment_date).toISOString(),
    })
    success('Home Collection Scheduled', 'Phlebotomist booking successfully logged')
    isBookModalOpen.value = false
    fetchBookings()
  } catch (err: any) {
    error('Booking Failed', err.message)
  } finally {
    submitting.value = false
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'REQUESTED': return 'warning'
    case 'SCHEDULED': return 'info'
    case 'OUT_FOR_COLLECTION': return 'info'
    case 'COLLECTED': return 'success'
    case 'ARRIVED_AT_LAB': return 'success'
    case 'CANCELLED': return 'danger'
    default: return 'neutral'
  }
}

onMounted(() => {
  fetchBookings()
})
</script>

<template>
  <div class="space-y-4 max-w-7xl mx-auto text-left text-slate-900 dark:text-slate-100 pb-12">
    <!-- Header -->
    <PageHeader
      title="Home Sample Collection & Phlebotomy Routing"
      subtitle="Field dispatch queue, home appointment scheduling, route tracking, and accessioning handover."
      icon="map-pin"
      badge="Module 06"
      badge-variant="info"
    >
      <template #actions>
        <Button variant="secondary" size="sm" icon-left="refresh" :loading="loading" @click="fetchBookings">
          Refresh Queue
        </Button>
        <Button variant="primary" size="sm" icon-left="plus" @click="isBookModalOpen = true">
          Schedule Home Visit
        </Button>
      </template>
    </PageHeader>

    <!-- Filters & Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
      <Card dense>
        <div class="text-xs text-slate-500 font-medium">Total Bookings</div>
        <div class="text-xl font-bold text-slate-900 dark:text-white mt-1">{{ bookings.length }}</div>
      </Card>
      <Card dense>
        <div class="text-xs text-amber-600 dark:text-amber-400 font-medium">Pending Pickup</div>
        <div class="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1">
          {{ bookings.filter(b => ['REQUESTED', 'SCHEDULED', 'OUT_FOR_COLLECTION'].includes(b.status)).length }}
        </div>
      </Card>
      <Card dense>
        <div class="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Samples Collected</div>
        <div class="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
          {{ bookings.filter(b => b.status === 'COLLECTED').length }}
        </div>
      </Card>
      <Card dense>
        <div class="text-xs text-teal-600 dark:text-teal-400 font-medium">Arrived at Lab</div>
        <div class="text-xl font-bold text-teal-600 dark:text-teal-400 mt-1">
          {{ bookings.filter(b => b.status === 'ARRIVED_AT_LAB').length }}
        </div>
      </Card>
    </div>

    <!-- Bookings Table -->
    <Card title="Phlebotomist Field Dispatch Queue" dense>
      <template #header-right>
        <div class="flex items-center space-x-2 text-xs">
          <label class="text-slate-500 font-medium">Filter:</label>
          <select
            v-model="filterStatus"
            class="px-2 py-1 text-xs border rounded-md bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700"
            @change="fetchBookings"
          >
            <option value="">All Statuses</option>
            <option value="REQUESTED">Requested</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="OUT_FOR_COLLECTION">Out for Collection</option>
            <option value="COLLECTED">Collected</option>
            <option value="ARRIVED_AT_LAB">Arrived at Lab</option>
          </select>
        </div>
      </template>

      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-xs">
          <thead class="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 font-bold">
            <tr>
              <th class="px-4 py-3 text-left">Patient & Contact</th>
              <th class="px-4 py-3 text-left">Appointment Slot</th>
              <th class="px-4 py-3 text-left">Address & Landmark</th>
              <th class="px-4 py-3 text-left">Phlebotomist</th>
              <th class="px-4 py-3 text-center">Status</th>
              <th class="px-4 py-3 text-right">Fee</th>
              <th class="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
            <tr v-for="b in bookings" :key="b.id" class="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
              <td class="px-4 py-3">
                <div class="font-bold text-slate-900 dark:text-slate-100">{{ b.patient_name }}</div>
                <div class="text-[11px] text-slate-500 font-mono">📞 {{ b.contact_phone }}</div>
                <div v-if="b.patient_uhid" class="text-[10px] text-teal-600 font-mono">{{ b.patient_uhid }}</div>
              </td>
              <td class="px-4 py-3">
                <div class="font-medium text-slate-800 dark:text-slate-200">{{ new Date(b.appointment_date).toLocaleDateString() }}</div>
                <div class="text-[11px] text-teal-700 dark:text-teal-300 font-semibold">{{ b.time_slot }}</div>
              </td>
              <td class="px-4 py-3 max-w-xs truncate">
                <div class="truncate text-slate-800 dark:text-slate-200">{{ b.address }}</div>
                <div v-if="b.landmark" class="text-[11px] text-slate-500">Near: {{ b.landmark }}</div>
              </td>
              <td class="px-4 py-3">
                <span class="inline-flex items-center gap-1 text-slate-700 dark:text-slate-300 font-medium">
                  <Icon name="user" size="xs" />
                  {{ b.phlebotomist_name }}
                </span>
              </td>
              <td class="px-4 py-3 text-center">
                <Badge :variant="getStatusBadge(b.status)" size="sm">
                  {{ b.status.replace(/_/g, ' ') }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right font-mono font-bold text-slate-900 dark:text-white">
                ₹{{ b.collection_charge }}
              </td>
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end space-x-1.5">
                  <button
                    v-if="b.status === 'REQUESTED'"
                    type="button"
                    class="px-2 py-1 bg-sky-50 dark:bg-sky-950 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800 rounded text-[11px] font-semibold hover:bg-sky-100"
                    @click="updateStatus(b.id, 'SCHEDULED')"
                  >
                    Schedule
                  </button>
                  <button
                    v-if="b.status === 'SCHEDULED'"
                    type="button"
                    class="px-2 py-1 bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 rounded text-[11px] font-semibold hover:bg-amber-100"
                    @click="updateStatus(b.id, 'OUT_FOR_COLLECTION')"
                  >
                    Dispatch
                  </button>
                  <button
                    v-if="b.status === 'OUT_FOR_COLLECTION'"
                    type="button"
                    class="px-2 py-1 bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded text-[11px] font-semibold hover:bg-emerald-100"
                    @click="updateStatus(b.id, 'COLLECTED')"
                  >
                    Mark Collected
                  </button>
                  <button
                    v-if="b.status === 'COLLECTED'"
                    type="button"
                    class="px-2 py-1 bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 rounded text-[11px] font-semibold hover:bg-teal-100"
                    @click="updateStatus(b.id, 'ARRIVED_AT_LAB')"
                  >
                    Receive at Lab
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="bookings.length === 0">
              <td colspan="7" class="py-8 text-center text-slate-400">
                No home collection requests found for this filter.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Schedule Modal -->
    <Modal v-model="isBookModalOpen" title="Schedule Home Sample Collection" @close="isBookModalOpen = false">
      <form class="space-y-4" @submit.prevent="handleCreateBooking">
        <Input v-model="newBooking.contact_phone" label="Patient Mobile Number" placeholder="10-digit mobile" required prefix-icon="phone" />
        <div class="grid grid-cols-2 gap-3">
          <Input v-model="newBooking.appointment_date" label="Appointment Date & Time" type="datetime-local" required />
          <div class="flex flex-col space-y-1">
            <label class="text-xs font-semibold text-slate-700 dark:text-slate-300">Preferred Time Slot</label>
            <select v-model="newBooking.time_slot" class="h-9 px-3 text-sm border rounded-md bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700">
              <option value="06:30 AM - 07:30 AM">06:30 AM - 07:30 AM (Fasting)</option>
              <option value="07:30 AM - 08:30 AM">07:30 AM - 08:30 AM (Fasting)</option>
              <option value="08:30 AM - 09:30 AM">08:30 AM - 09:30 AM</option>
              <option value="10:00 AM - 12:00 PM">10:00 AM - 12:00 PM</option>
              <option value="04:00 PM - 06:00 PM">04:00 PM - 06:00 PM (Evening)</option>
            </select>
          </div>
        </div>
        <Input v-model="newBooking.address" label="Complete Residential Address" placeholder="Flat No, Building, Street, Area" required prefix-icon="map-pin" />
        <div class="grid grid-cols-2 gap-3">
          <Input v-model="newBooking.landmark" label="Landmark" placeholder="e.g. Near Metro Station" />
          <Input v-model="newBooking.pincode" label="Area Pincode" placeholder="e.g. 201301" />
        </div>
        <Input v-model.number="newBooking.collection_charge" label="Home Collection Fee (₹)" type="number" />
        <div class="pt-2 flex justify-end space-x-2">
          <Button variant="secondary" size="md" @click="isBookModalOpen = false">Cancel</Button>
          <Button variant="primary" size="md" type="submit" :loading="submitting">Schedule Booking</Button>
        </div>
      </form>
    </Modal>
  </div>
</template>
