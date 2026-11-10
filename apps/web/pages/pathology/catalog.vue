<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from '~/composables/useToast'
import * as XLSX from 'xlsx'
import PageHeader from '~/components/ui/PageHeader.vue'
import Card from '~/components/ui/Card.vue'
import Badge from '~/components/ui/Badge.vue'
import Button from '~/components/ui/Button.vue'
import Icon from '~/components/ui/Icon.vue'
import Kbd from '~/components/ui/Kbd.vue'

const api = useApi()
const { success, warning, error: toastError } = useToast()

interface ReferenceRangeDetail {
  id?: string
  sex: string
  low_value: number | null
  high_value: number | null
  critical_low?: number | null
  critical_high?: number | null
  text_range: string | null
  notes?: string | null
  needs_review?: boolean
}

interface ParameterDetail {
  id?: string
  code: string
  name: string
  unit: string | null
  result_type: string
  sort_order: number
  is_active: boolean
  validation_rules?: string | null
  reference_ranges?: ReferenceRangeDetail[]
}

interface TestCatalogItem {
  id: string
  code: string
  name: string
  default_code?: string
  default_name?: string
  department: string
  specimen: string
  tube_color: string
  unit: string
  tat_hours: number
  default_tat_hours?: number
  price: number
  default_price?: number
  is_active: boolean
  is_system_default: boolean
  is_overridden: boolean
  badge: 'System Default' | 'Customized Default' | 'Tenant Custom'
  sync_status: 'synced' | 'pending' | 'failed'
  parameters_summary?: string
  parameters_count?: number
  parameters?: ParameterDetail[]
  reference_ranges?: ReferenceRangeDetail[]
}

interface NewTestForm {
  code: string
  name: string
  department: string
  specimen: string
  tube_color: string
  unit: string
  tat_hours: number
  price: number
  parameters: ParameterDetail[]
}

const loading = ref(true)
const tests = ref<TestCatalogItem[]>([])
const searchQuery = ref('')
const selectedDepartment = ref('All')
const selectedStatus = ref<'all' | 'active' | 'inactive' | 'overridden'>('all')
const selectedLayer = ref<'all' | 'system' | 'customized' | 'tenant'>('all')

const departments = [
  'All',
  'Hematology',
  'Biochemistry',
  'Hormones & Immunoassay',
  'Serology & Immunology',
  'Microbiology & Culture',
  'Clinical Pathology',
  'Coagulation',
]

// Selection & Bulk actions
const selectedTestIds = ref<string[]>([])
const isBulkModalOpen = ref(false)
const bulkActionType = ref<'fixed' | 'increase_pct' | 'decrease_pct' | 'tat' | 'activate' | 'deactivate'>('fixed')
const bulkPriceValue = ref<number>(300)
const bulkTatValue = ref<number>(4)
const bulkSaving = ref(false)

// Drawer / Detail Editor
const isDetailDrawerOpen = ref(false)
const activeTest = ref<TestCatalogItem | null>(null)
const drawerSaving = ref(false)

// Create Test Modal & Parameter Builder
const isCreateModalOpen = ref(false)
const newTest = ref<NewTestForm>({
  code: '',
  name: '',
  department: 'Biochemistry',
  specimen: 'Serum',
  tube_color: 'Red (Plain / Gel)',
  unit: 'mg/dL',
  tat_hours: 4,
  price: 250,
  parameters: []
})

// Mass Importer
const isImportModalOpen = ref(false)
const importMode = ref<'insert_only' | 'update_existing' | 'upsert'>('upsert')
const importStep = ref<'upload' | 'preview' | 'importing'>('upload')
const importFileName = ref('')
const parsedImportTests = ref<any[]>([])
const importPreview = ref<{
  new_count: number
  updated_count: number
  skipped_count: number
  invalid_count: number
  new_tests: any[]
  updated_tests: any[]
  skipped_tests: any[]
  invalid_rows: any[]
  price_changes: any[]
}>({
  new_count: 0,
  updated_count: 0,
  skipped_count: 0,
  invalid_count: 0,
  new_tests: [],
  updated_tests: [],
  skipped_tests: [],
  invalid_rows: [],
  price_changes: [],
})
const activePreviewTab = ref<'new' | 'updates' | 'skipped' | 'invalid'>('new')

// Offline sync state
const pendingSyncCount = computed(() => tests.value.filter(t => t.sync_status === 'pending').length)
const totalMultiParamCount = computed(() => tests.value.filter(t => (t.parameters?.length || t.parameters_count || 0) > 1).length)
const customizedCount = computed(() => tests.value.filter(t => t.is_overridden).length)
const tenantCustomCount = computed(() => tests.value.filter(t => !t.is_system_default).length)
const inactiveCount = computed(() => tests.value.filter(t => !t.is_active).length)

// Load catalog
async function loadCatalog() {
  loading.value = true
  try {
    const data: any = await api.get('/pathology/tests?limit=500')
    if (Array.isArray(data) && data.length > 0) {
      tests.value = data.map((t: any) => ({
        id: t.id,
        code: t.code,
        name: t.name,
        default_code: t.default_code,
        default_name: t.default_name,
        department: t.department || 'Biochemistry',
        specimen: t.specimen || 'Serum',
        tube_color: t.tube_color || 'Red (Plain / Gel)',
        unit: t.unit || 'Var',
        tat_hours: t.tat_hours || 4,
        default_tat_hours: t.default_tat_hours || 4,
        price: Number(t.price || 0),
        default_price: Number(t.default_price || 0),
        is_active: t.is_active !== false,
        is_system_default: Boolean(t.is_system_default),
        is_overridden: Boolean(t.is_overridden),
        badge: t.badge || (t.is_system_default ? (t.is_overridden ? 'Customized Default' : 'System Default') : 'Tenant Custom'),
        sync_status: t.sync_status || 'synced',
        parameters_summary: t.parameters_summary || '',
        parameters_count: t.parameters_count || (t.parameters ? t.parameters.length : 0),
        parameters: t.parameters || [],
        reference_ranges: t.reference_ranges || [],
      }))
      try {
        localStorage.setItem('aarozi_cached_catalog', JSON.stringify(tests.value))
      } catch (_) {}
    } else {
      loadCachedOrFallbackCatalog()
    }
  } catch (err) {
    console.warn('API error, switching to offline local catalog cache:', err)
    loadCachedOrFallbackCatalog()
  } finally {
    loading.value = false
  }
}

function loadCachedOrFallbackCatalog() {
  try {
    const cached = localStorage.getItem('aarozi_cached_catalog')
    if (cached) {
      tests.value = JSON.parse(cached)
      return
    }
  } catch (_) {}
}

onMounted(() => {
  loadCatalog()
})

// Filtered tests computation
const filteredTests = computed(() => {
  let list = tests.value

  if (selectedDepartment.value !== 'All') {
    list = list.filter(t => t.department.toLowerCase() === selectedDepartment.value.toLowerCase())
  }

  if (selectedStatus.value === 'active') {
    list = list.filter(t => t.is_active)
  } else if (selectedStatus.value === 'inactive') {
    list = list.filter(t => !t.is_active)
  } else if (selectedStatus.value === 'overridden') {
    list = list.filter(t => t.is_overridden)
  }

  if (selectedLayer.value === 'system') {
    list = list.filter(t => t.is_system_default && !t.is_overridden)
  } else if (selectedLayer.value === 'customized') {
    list = list.filter(t => t.is_system_default && t.is_overridden)
  } else if (selectedLayer.value === 'tenant') {
    list = list.filter(t => !t.is_system_default)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter(t =>
      t.code.toLowerCase().includes(q) ||
      t.name.toLowerCase().includes(q) ||
      t.specimen.toLowerCase().includes(q) ||
      (t.parameters_summary && t.parameters_summary.toLowerCase().includes(q))
    )
  }

  return list
})

const { currentPage, pageSize, paginatedItems: paginatedTests, resetPage } = usePagination(filteredTests, 15)

watch([searchQuery, selectedDepartment, selectedStatus, selectedLayer], () => {
  resetPage()
})

// Selection
const isAllSelected = computed(() => {
  return filteredTests.value.length > 0 && selectedTestIds.value.length === filteredTests.value.length
})

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedTestIds.value = []
  } else {
    selectedTestIds.value = filteredTests.value.map(t => t.id)
  }
}

function toggleSelectTest(id: string) {
  const index = selectedTestIds.value.indexOf(id)
  if (index > -1) {
    selectedTestIds.value.splice(index, 1)
  } else {
    selectedTestIds.value.push(id)
  }
}

// Drawer & Parameter Management
async function openDetailDrawer(test: TestCatalogItem) {
  activeTest.value = JSON.parse(JSON.stringify(test))
  isDetailDrawerOpen.value = true

  // Fetch complete details if parameters are not populated
  if (!activeTest.value?.parameters || activeTest.value.parameters.length === 0) {
    try {
      const fullDetail: any = await api.get(`/pathology/tests/${test.id}`)
      if (fullDetail && activeTest.value) {
        activeTest.value.parameters = fullDetail.parameters || []
        activeTest.value.reference_ranges = fullDetail.reference_ranges || []
      }
    } catch (_) {}
  }
}

function addParameterToActiveTest() {
  if (!activeTest.value) return
  if (!activeTest.value.parameters) activeTest.value.parameters = []
  const count = activeTest.value.parameters.length + 1
  activeTest.value.parameters.push({
    id: `param-${Date.now()}-${count}`,
    code: `${activeTest.value.code}_P${count}`,
    name: '',
    unit: activeTest.value.unit || 'mg/dL',
    result_type: 'numeric',
    sort_order: count,
    is_active: true,
    reference_ranges: [
      { sex: 'all', low_value: null, high_value: null, text_range: 'Normal' }
    ]
  })
}

function removeParameterFromActiveTest(index: number) {
  if (!activeTest.value?.parameters) return
  activeTest.value.parameters.splice(index, 1)
}

function addReferenceRangeToParam(param: ParameterDetail) {
  if (!param.reference_ranges) param.reference_ranges = []
  param.reference_ranges.push({
    sex: 'all',
    low_value: null,
    high_value: null,
    text_range: 'Normal'
  })
}

function removeReferenceRangeFromParam(param: ParameterDetail, rIdx: number) {
  if (!param.reference_ranges) return
  param.reference_ranges.splice(rIdx, 1)
}

async function saveTestDrawerOverride() {
  if (!activeTest.value) return
  drawerSaving.value = true
  const t = activeTest.value

  const payload = {
    test_id: t.id,
    price: Number(t.price),
    tat_hours: Number(t.tat_hours),
    custom_name: t.name,
    is_active: t.is_active,
    specimen_type: t.specimen,
    container_type: t.tube_color,
    parameters: (t.parameters || []).map((p, idx) => ({
      id: p.id && !p.id.startsWith('param-') ? p.id : undefined,
      code: p.code || `${t.code}_P${idx+1}`,
      name: p.name || p.code,
      unit: p.unit,
      result_type: p.result_type || 'numeric',
      sort_order: idx + 1,
      is_active: p.is_active !== false,
      reference_ranges: p.reference_ranges || []
    }))
  }

  try {
    const updated: any = await api.post('/pathology/tests/override', payload)

    const targetIdx = tests.value.findIndex(item => item.id === t.id)
    if (targetIdx > -1) {
      const target = tests.value[targetIdx]
      if (target) {
        target.price = Number(t.price)
        target.tat_hours = Number(t.tat_hours)
        target.name = t.name
        target.is_active = t.is_active
        target.is_overridden = true
        target.badge = t.is_system_default ? 'Customized Default' : 'Tenant Custom'
        target.sync_status = 'pending'
        target.parameters = updated?.parameters || t.parameters
        target.parameters_count = target.parameters?.length || 0
        target.parameters_summary = target.parameters?.map((p: any) => p.name).filter(Boolean).join(', ')
      }
    }

    success(`Saved local customization for ${t.code} (${t.name})`)
    isDetailDrawerOpen.value = false
  } catch (err: any) {
    const targetIdx = tests.value.findIndex(item => item.id === t.id)
    if (targetIdx > -1) {
      const target = tests.value[targetIdx]
      if (target) {
        target.price = Number(t.price)
        target.tat_hours = Number(t.tat_hours)
        target.name = t.name
        target.is_active = t.is_active
        target.is_overridden = true
        target.badge = t.is_system_default ? 'Customized Default' : 'Tenant Custom'
        target.sync_status = 'pending'
        target.parameters = t.parameters ? [...t.parameters] : []
        target.parameters_count = target.parameters.length
        target.parameters_summary = target.parameters.map(p => p.name).filter(Boolean).join(', ')
      }
    }
    localStorage.setItem('aarozi_cached_catalog', JSON.stringify(tests.value))
    warning(`Saved locally (Offline Mode)`, `Changes for ${t.code} will sync when connection returns.`)
    isDetailDrawerOpen.value = false
  } finally {
    drawerSaving.value = false
  }
}

async function resetCurrentTestOverride() {
  if (!activeTest.value) return
  const t = activeTest.value
  drawerSaving.value = true

  try {
    await api.post('/pathology/tests/reset-override', { test_id: t.id })
    const targetIdx = tests.value.findIndex(item => item.id === t.id)
    if (targetIdx > -1) {
      const target = tests.value[targetIdx]
      if (target) {
        target.price = target.default_price || target.price
        target.tat_hours = target.default_tat_hours || 4
        target.name = target.default_name || target.name
        target.is_overridden = false
        target.badge = 'System Default'
        target.sync_status = 'synced'
      }
    }
    success(`Reset to System Default`, `${t.code} reverted to official baseline settings.`)
    isDetailDrawerOpen.value = false
  } catch (err) {
    const targetIdx = tests.value.findIndex(item => item.id === t.id)
    if (targetIdx > -1) {
      const target = tests.value[targetIdx]
      if (target) {
        target.price = target.default_price || target.price
        target.tat_hours = target.default_tat_hours || 4
        target.is_overridden = false
        target.badge = 'System Default'
        target.sync_status = 'synced'
      }
    }
    success(`Reset to System Default (Local)`, `${t.code} reverted.`)
    isDetailDrawerOpen.value = false
  } finally {
    drawerSaving.value = false
  }
}

// Quick toggle active
async function toggleActiveStatus(test: TestCatalogItem) {
  const newActive = !test.is_active
  test.is_active = newActive
  test.sync_status = 'pending'

  try {
    await api.post('/pathology/tests/override', {
      test_id: test.id,
      is_active: newActive,
    })
    test.is_overridden = test.is_system_default ? true : test.is_overridden
    test.badge = test.is_system_default ? 'Customized Default' : 'Tenant Custom'
  } catch (err) {
    localStorage.setItem('aarozi_cached_catalog', JSON.stringify(tests.value))
  }
}

// Bulk Actions
async function applyBulkUpdate() {
  if (selectedTestIds.value.length === 0) return
  bulkSaving.value = true

  const payload: any = {
    test_ids: selectedTestIds.value,
  }

  if (bulkActionType.value === 'fixed') {
    payload.price_action = 'set_fixed'
    payload.price_value = Number(bulkPriceValue.value)
  } else if (bulkActionType.value === 'increase_pct') {
    payload.price_action = 'increase_pct'
    payload.price_value = Number(bulkPriceValue.value)
  } else if (bulkActionType.value === 'decrease_pct') {
    payload.price_action = 'decrease_pct'
    payload.price_value = Number(bulkPriceValue.value)
  } else if (bulkActionType.value === 'tat') {
    payload.tat_hours = Number(bulkTatValue.value)
  } else if (bulkActionType.value === 'activate') {
    payload.is_active = true
  } else if (bulkActionType.value === 'deactivate') {
    payload.is_active = false
  }

  try {
    await api.post('/pathology/tests/bulk-update', payload)

    for (const id of selectedTestIds.value) {
      const target = tests.value.find(t => t.id === id)
      if (target) {
        if (payload.price_action === 'set_fixed') {
          target.price = Number(bulkPriceValue.value)
        } else if (payload.price_action === 'increase_pct') {
          target.price = Math.round(target.price * (1 + bulkPriceValue.value / 100))
        } else if (payload.price_action === 'decrease_pct') {
          target.price = Math.max(0, Math.round(target.price * (1 - bulkPriceValue.value / 100)))
        }
        if (payload.tat_hours) target.tat_hours = Number(payload.tat_hours)
        if (payload.is_active !== undefined) target.is_active = payload.is_active

        target.is_overridden = target.is_system_default ? true : target.is_overridden
        target.badge = target.is_system_default ? 'Customized Default' : 'Tenant Custom'
        target.sync_status = 'pending'
      }
    }

    success(`Bulk Action Complete`, `Successfully updated ${selectedTestIds.value.length} investigations.`)
    isBulkModalOpen.value = false
    selectedTestIds.value = []
  } catch (err) {
    for (const id of selectedTestIds.value) {
      const target = tests.value.find(t => t.id === id)
      if (target) {
        if (payload.price_action === 'set_fixed') target.price = Number(bulkPriceValue.value)
        if (payload.tat_hours) target.tat_hours = Number(payload.tat_hours)
        if (payload.is_active !== undefined) target.is_active = payload.is_active
        target.sync_status = 'pending'
      }
    }
    localStorage.setItem('aarozi_cached_catalog', JSON.stringify(tests.value))
    warning(`Applied Locally (Offline)`, `Updated ${selectedTestIds.value.length} investigations.`)
    isBulkModalOpen.value = false
    selectedTestIds.value = []
  } finally {
    bulkSaving.value = false
  }
}

// Add Custom Investigation with Parameter Builder
function openCreateModal() {
  newTest.value = {
    code: '',
    name: '',
    department: 'Biochemistry',
    specimen: 'Serum',
    tube_color: 'Red (Plain / Gel)',
    unit: 'mg/dL',
    tat_hours: 4,
    price: 250,
    parameters: [
      {
        id: `param-temp-${Date.now()}-1`,
        code: '',
        name: '',
        unit: 'mg/dL',
        result_type: 'numeric',
        sort_order: 1,
        is_active: true,
        reference_ranges: [
          { sex: 'all', low_value: null, high_value: null, text_range: 'Normal' }
        ]
      }
    ]
  }
  isCreateModalOpen.value = true
}

function addParameterToNewTest() {
  const pCount = newTest.value.parameters.length + 1
  newTest.value.parameters.push({
    id: `param-temp-${Date.now()}-${pCount}`,
    code: newTest.value.code ? `${newTest.value.code}_P${pCount}` : `PARAM_${pCount}`,
    name: '',
    unit: newTest.value.unit || 'mg/dL',
    result_type: 'numeric',
    sort_order: pCount,
    is_active: true,
    reference_ranges: [
      { sex: 'all', low_value: null, high_value: null, text_range: 'Normal' }
    ]
  })
}

function removeParameterFromNewTest(idx: number) {
  newTest.value.parameters.splice(idx, 1)
}

async function createTest() {
  if (!newTest.value.code || !newTest.value.name) {
    toastError('Validation Error', 'Test Code and Investigation Name are required.')
    return
  }

  // Pre-fill parameter code/name if single parameter was left blank
  const firstParam = newTest.value.parameters[0]
  if (firstParam && !firstParam.name) {
    firstParam.name = newTest.value.name.trim()
    firstParam.code = newTest.value.code.toUpperCase().trim()
  }

  const cleanParams = (newTest.value.parameters || []).map((p, idx) => ({
    code: (p.code || `${newTest.value.code}_P${idx+1}`).toUpperCase().trim(),
    name: (p.name || newTest.value.name).trim(),
    unit: p.unit || newTest.value.unit,
    result_type: p.result_type || 'numeric',
    sort_order: idx + 1,
    is_active: p.is_active !== false,
    reference_ranges: p.reference_ranges || []
  }))

  const item: TestCatalogItem = {
    id: `custom-${Date.now()}`,
    code: newTest.value.code.toUpperCase().trim(),
    name: newTest.value.name.trim(),
    department: newTest.value.department,
    specimen: newTest.value.specimen,
    tube_color: newTest.value.tube_color,
    unit: newTest.value.unit,
    tat_hours: newTest.value.tat_hours,
    price: newTest.value.price,
    is_active: true,
    is_system_default: false,
    is_overridden: false,
    badge: 'Tenant Custom',
    sync_status: 'pending',
    parameters: cleanParams,
    parameters_count: cleanParams.length,
    parameters_summary: cleanParams.map(p => p.name).join(', ')
  }

  tests.value.unshift(item)
  localStorage.setItem('aarozi_cached_catalog', JSON.stringify(tests.value))

  try {
    await api.post('/pathology/tests/create', {
      code: item.code,
      name: item.name,
      department_id: null,
      

      
    })
    item.sync_status = 'synced'
  } catch (_) {
    // Stored locally
  }

  success(`Investigation Registered`, `"${item.code} — ${item.name}" registered with ${cleanParams.length} reportable parameters!`)
  isCreateModalOpen.value = false
}

// Mass Importer Handler
function handleFileUpload(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  const file = target.files[0]
  if (!file) return
  importFileName.value = file.name

  const reader = new FileReader()
  reader.onload = (loadEvent) => {
    try {
      const data = new Uint8Array(loadEvent.target?.result as ArrayBuffer)
      const workbook = XLSX.read(data, { type: 'array' })

      const sheetNames = workbook.SheetNames
      let rawRows: any[] = []

      const targetSheetName = sheetNames.includes('Investigations') ? 'Investigations' : (sheetNames[0] || '')
      const targetWorksheet = targetSheetName ? workbook.Sheets[targetSheetName] : undefined

      if (targetWorksheet) {
        rawRows = XLSX.utils.sheet_to_json(targetWorksheet, { header: 1 })
      }

      if (rawRows.length < 2) {
        toastError('Import Error', 'Spreadsheet contains no data rows.')
        return
      }

      const headers = (rawRows[0] || []).map((h: any) => String(h || '').trim().toLowerCase())
      const parsedItems: any[] = []

      const codeIdx = headers.findIndex((h: string) => h.includes('code'))
      const nameIdx = headers.findIndex((h: string) => h.includes('name') || h.includes('investigation'))
      const deptIdx = headers.findIndex((h: string) => h.includes('department') || h.includes('discipline'))
      const priceIdx = headers.findIndex((h: string) => h.includes('price') || h.includes('rate') || h.includes('inr'))
      const tatIdx = headers.findIndex((h: string) => h.includes('tat') || h.includes('turnaround'))
      const sampleIdx = headers.findIndex((h: string) => h.includes('sample') || h.includes('specimen'))
      const paramsIdx = headers.findIndex((h: string) => h.includes('parameter') && !h.includes('details'))

      for (let r = 1; r < rawRows.length; r++) {
        const row = rawRows[r]
        if (!row || row.length === 0) continue

        const code = String(row[codeIdx >= 0 ? codeIdx : 0] || '').trim().toUpperCase()
        const name = String(row[nameIdx >= 0 ? nameIdx : 1] || '').trim()
        if (!name) continue

        const dept = deptIdx >= 0 ? String(row[deptIdx] || 'Biochemistry').trim() : 'Biochemistry'
        const price = priceIdx >= 0 ? Number(String(row[priceIdx]).replace(/[^\d.]/g, '') || 0) : 250
        const tat = tatIdx >= 0 ? Number(String(row[tatIdx]).replace(/[^\d.]/g, '') || 4) : 4
        const sample = sampleIdx >= 0 ? String(row[sampleIdx] || 'Serum').trim() : 'Serum'
        const paramsSummary = paramsIdx >= 0 ? String(row[paramsIdx] || '').trim() : ''

        parsedItems.push({
          code: code || `IMP_${r}`,
          name,
          department: dept,
          price,
          tat_hours: tat || 4,
          sample_type: sample,
          parameters_summary: paramsSummary,
        })
      }

      parsedImportTests.value = parsedItems

      // Generate preview
      const existingMap = new Map(tests.value.map(t => [t.code.toUpperCase(), t]))
      const newItems: any[] = []
      const updatedItems: any[] = []
      const skippedItems: any[] = []
      const priceDiffs: any[] = []

      for (const item of parsedItems) {
        const matched = existingMap.get(item.code)
        if (matched) {
          if (importMode.value === 'insert_only') {
            skippedItems.push({ ...item, reason: 'Already exists in catalog' })
          } else {
            updatedItems.push(item)
            if (matched.price !== item.price) {
              priceDiffs.push({
                code: item.code,
                name: item.name,
                old_price: matched.price,
                new_price: item.price,
              })
            }
          }
        } else {
          if (importMode.value === 'update_existing') {
            skippedItems.push({ ...item, reason: 'Investigation not found in catalog' })
          } else {
            newItems.push(item)
          }
        }
      }

      importPreview.value = {
        new_count: newItems.length,
        updated_count: updatedItems.length,
        skipped_count: skippedItems.length,
        invalid_count: 0,
        new_tests: newItems,
        updated_tests: updatedItems,
        skipped_tests: skippedItems,
        invalid_rows: [],
        price_changes: priceDiffs,
      }

      importStep.value = 'preview'
    } catch (err: any) {
      toastError('Parser Error', `Failed to parse spreadsheet: ${err.message}`)
    }
  }
  reader.readAsArrayBuffer(file)
}

async function confirmMassImport() {
  importStep.value = 'importing'
  try {
    await api.post('/pathology/tests/import', {
      tests: parsedImportTests.value,
      mode: importMode.value,
    })
    success(`Import Complete`, `Catalog updated with ${parsedImportTests.value.length} records.`)
    isImportModalOpen.value = false
    importStep.value = 'upload'
    loadCatalog()
  } catch (err: any) {
    // Offline local apply
    for (const item of parsedImportTests.value) {
      const idx = tests.value.findIndex(t => t.code.toUpperCase() === item.code.toUpperCase())
      if (idx > -1) {
        if (importMode.value !== 'insert_only') {
          const t = tests.value[idx]
          if (t) {
            t.price = item.price
            t.tat_hours = item.tat_hours
            t.is_overridden = true
            t.badge = t.is_system_default ? 'Customized Default' : 'Tenant Custom'
            t.sync_status = 'pending'
          }
        }
      } else {
        if (importMode.value !== 'update_existing') {
          tests.value.unshift({
            id: `custom-imp-${Date.now()}-${Math.random()}`,
            code: item.code,
            name: item.name,
            department: item.department || 'Biochemistry',
            specimen: item.sample_type || 'Serum',
            tube_color: 'Red (Plain / Gel)',
            unit: 'Var',
            tat_hours: item.tat_hours || 4,
            price: item.price || 0,
            is_active: true,
            is_system_default: false,
            is_overridden: false,
            badge: 'Tenant Custom',
            sync_status: 'pending',
            parameters_summary: item.parameters_summary,
            parameters_count: 1,
            parameters: [{
              code: item.code,
              name: item.name,
              unit: 'Var',
              result_type: 'numeric',
              sort_order: 1,
              is_active: true
            }]
          })
        }
      }
    }
    localStorage.setItem('aarozi_cached_catalog', JSON.stringify(tests.value))
    warning(`Applied Locally (Offline)`, `Imported ${parsedImportTests.value.length} items to local storage.`)
    isImportModalOpen.value = false
    importStep.value = 'upload'
  }
}

function downloadTemplate() {
  const config = useRuntimeConfig()
  const apiBase = (config.public.apiBase as string) || 'http://localhost:8000'
  window.open(`${apiBase}/pathology/tests/template/download`, '_blank')
}
</script>

<template>
  <div class="space-y-4">
    <!-- Top Action & Architecture Header -->
    <PageHeader
      title="Master Pathology Test Catalog"
      description="Laboratory investigations, clinical parameters, sex-specific reference intervals, and tenant rate structures."
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <Button
            variant="secondary"
            size="md"
            title="Download Excel test catalog template"
            @click="downloadTemplate"
          >
            <Icon name="download" class="w-4 h-4" />
            <span class="hidden sm:inline">Template</span>
          </Button>

          <Button
            variant="secondary"
            size="md"
            title="Import investigations from Excel / CSV"
            @click="isImportModalOpen = true; importStep = 'upload'"
          >
            <Icon name="file-text" class="w-4 h-4" />
            <span class="hidden sm:inline">Mass Import</span>
          </Button>

          <Button
            variant="primary"
            size="md"
            title="Define custom laboratory test or panel"
            @click="openCreateModal"
          >
            <Icon name="plus" class="w-4 h-4" />
            <span>Add Investigation</span>
          </Button>
        </div>
      </template>
    </PageHeader>

    <!-- 5 Live Catalog Stats Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
      <Card class="p-3.5 bg-white">
        <div class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Tests</div>
        <div class="text-xl font-bold font-mono text-slate-900 mt-1">{{ tests.length }}</div>
        <div class="text-xs text-emerald-700 mt-1 font-medium flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          <span>{{ tests.length - inactiveCount }} Active in Catalog</span>
        </div>
      </Card>

      <Card class="p-3.5 bg-white">
        <div class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Multi-Param Panels</div>
        <div class="text-xl font-bold font-mono text-teal-700 mt-1">{{ totalMultiParamCount }}</div>
        <div class="text-xs text-teal-700 mt-1 font-medium truncate">CBC, LFT, KFT, Lipid...</div>
      </Card>

      <Card class="p-3.5 bg-white">
        <div class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Customized Defaults</div>
        <div class="text-xl font-bold font-mono text-amber-700 mt-1">{{ customizedCount }}</div>
        <div class="text-xs text-amber-700 mt-1 font-medium">Lab Overrides Active</div>
      </Card>

      <Card class="p-3.5 bg-white">
        <div class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tenant Custom</div>
        <div class="text-xl font-bold font-mono text-purple-700 mt-1">{{ tenantCustomCount }}</div>
        <div class="text-xs text-purple-700 mt-1 font-medium">Lab-Created Assays</div>
      </Card>

      <Card class="p-3.5 bg-white col-span-2 lg:col-span-1">
        <div class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Offline Sync</div>
        <div v-if="pendingSyncCount > 0" class="text-xl font-bold font-mono text-amber-600 mt-1 flex items-center gap-1.5">
          <Icon name="refresh" class="w-4 h-4 animate-spin text-amber-600" />
          <span>{{ pendingSyncCount }} Pending</span>
        </div>
        <div v-else class="text-xl font-bold font-mono text-emerald-600 mt-1 flex items-center gap-1.5">
          <Icon name="shield-check" class="w-4 h-4 text-emerald-600" />
          <span>Synced</span>
        </div>
        <div class="text-xs text-slate-400 mt-1 font-medium">Local SQLite Truth</div>
      </Card>
    </div>

    <!-- Filters, Search & Bulk Toolbar -->
    <div class="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs space-y-3 text-xs">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <!-- Search -->
        <div class="relative flex-1 min-w-[280px]">
          <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400 pointer-events-none">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search test name, code, specimen, parameters (e.g. CBC, ESR, LFT)..."
            class="input-faang w-full pl-9 pr-7 py-1.5 text-xs"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="absolute inset-y-0 right-0 flex items-center pr-2 text-slate-400 hover:text-slate-600 cursor-pointer"
            title="Clear search"
            @click="searchQuery = ''"
          >
            <span class="text-sm leading-none">&times;</span>
          </button>
        </div>

        <!-- Discipline Filter -->
        <div class="flex items-center space-x-1.5">
          <label class="text-slate-500 font-medium">Discipline:</label>
          <select
            v-model="selectedDepartment"
            class="select-faang input-faang text-xs text-slate-700 cursor-pointer"
          >
            <option v-for="dept in departments" :key="dept" :value="dept">
              {{ dept === 'All' ? 'All Disciplines' : dept }}
            </option>
          </select>
        </div>

        <!-- Layer Filter -->
        <div class="flex items-center space-x-1.5">
          <label class="text-slate-500 font-medium">Catalog Layer:</label>
          <select
            v-model="selectedLayer"
            class="select-faang input-faang text-xs text-slate-700 cursor-pointer"
          >
            <option value="all">All Layers</option>
            <option value="system">System Default</option>
            <option value="customized">Customized Default</option>
            <option value="tenant">Tenant Custom</option>
          </select>
        </div>

        <!-- Status Filter -->
        <div class="flex items-center space-x-1.5">
          <label class="text-slate-500 font-medium">Status:</label>
          <select
            v-model="selectedStatus"
            class="select-faang input-faang text-xs text-slate-700 cursor-pointer"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
            <option value="overridden">Customized Only</option>
          </select>
        </div>

        <button
          type="button"
          class="btn-secondary"
          title="Reset all filters"
          @click="searchQuery = ''; selectedDepartment = 'All'; selectedStatus = 'all'; selectedLayer = 'all'"
        >
          Reset
        </button>
      </div>

      <!-- Bulk Actions Bar (Appears when tests are selected) -->
      <div
        v-if="selectedTestIds.length > 0"
        class="bg-sky-50 border border-sky-200 rounded-lg p-2.5 flex items-center justify-between text-xs text-sky-900 animate-fadeIn"
      >
        <div class="flex items-center space-x-2">
          <span class="font-bold text-sm text-sky-700">{{ selectedTestIds.length }}</span>
          <span>investigations selected</span>
        </div>

        <div class="flex items-center space-x-2">
          <button
            type="button"
            class="px-2.5 py-1 bg-white hover:bg-sky-100 border border-sky-300 text-sky-800 rounded font-semibold transition"
            @click="bulkActionType = 'fixed'; isBulkModalOpen = true"
          >
            Set Fixed Price
          </button>
          <button
            type="button"
            class="px-2.5 py-1 bg-white hover:bg-sky-100 border border-sky-300 text-sky-800 rounded font-semibold transition"
            @click="bulkActionType = 'increase_pct'; isBulkModalOpen = true"
          >
            Increase %
          </button>
          <button
            type="button"
            class="px-2.5 py-1 bg-white hover:bg-sky-100 border border-sky-300 text-sky-800 rounded font-semibold transition"
            @click="bulkActionType = 'tat'; isBulkModalOpen = true"
          >
            Update TAT
          </button>
          <button
            type="button"
            class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-semibold transition"
            @click="bulkActionType = 'activate'; isBulkModalOpen = true"
          >
            Activate All
          </button>
          <button
            type="button"
            class="px-2.5 py-1 bg-red-600 hover:bg-red-700 text-white rounded font-semibold transition"
            @click="bulkActionType = 'deactivate'; isBulkModalOpen = true"
          >
            Deactivate All
          </button>
          <button
            type="button"
            class="px-2 py-1 text-slate-500 hover:text-slate-700 underline text-xs"
            @click="selectedTestIds = []"
          >
            Clear Selection
          </button>
        </div>
      </div>
    </div>

    <!-- Master Catalog Table -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-xs">
          <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
            <tr>
              <th class="px-3 py-2.5 text-center w-8">
                <input
                  type="checkbox"
                  :checked="isAllSelected"
                  class="rounded border-slate-300 text-sky-600 focus:ring-sky-500 cursor-pointer"
                  @change="toggleSelectAll"
                />
              </th>
              <th class="w-12 px-3 py-2.5 text-center">#</th>
              <th class="px-4 py-2.5 text-left">Test Code</th>
              <th class="px-4 py-2.5 text-left">Investigation &amp; Parameters</th>
              <th class="px-3 py-2.5 text-left">Catalog Layer</th>
              <th class="px-3 py-2.5 text-left">Specimen / Tube</th>
              <th class="px-3 py-2.5 text-center">TAT</th>
              <th class="px-4 py-2.5 text-right">Standard Rate (₹)</th>
              <th class="px-3 py-2.5 text-center">Status</th>
              <th class="px-3 py-2.5 text-center">Sync</th>
              <th class="px-3 py-2.5 text-center">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-if="loading">
              <td colspan="11" class="text-center py-12 text-slate-400">
                <div class="flex flex-col items-center justify-center space-y-2">
                  <svg class="h-6 w-6 animate-spin text-sky-600" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                  </svg>
                  <span>Loading clinical test catalog from local database...</span>
                </div>
              </td>
            </tr>
            <tr v-else-if="filteredTests.length === 0">
              <td colspan="11" class="text-center py-12 text-slate-400">
                No investigations matching your criteria. Try adjusting the search query or discipline filter.
              </td>
            </tr>
            <tr
              v-for="(t, idx) in paginatedTests"
              v-else
              :key="t.id"
              class="hover:bg-slate-50/70 transition-colors"
            >
              <!-- Checkbox -->
              <td class="px-3 py-2.5 text-center">
                <input
                  type="checkbox"
                  :checked="selectedTestIds.includes(t.id)"
                  class="rounded border-slate-300 text-sky-600 focus:ring-sky-500 cursor-pointer"
                  @change="toggleSelectTest(t.id)"
                />
              </td>

              <!-- Index -->
              <td class="px-3 py-2.5 text-center font-mono font-bold text-slate-400">
                {{ (currentPage - 1) * pageSize + idx + 1 }}
              </td>

              <!-- Test Code -->
              <td class="px-4 py-2.5 font-mono font-bold text-sky-800 whitespace-nowrap">
                {{ t.code }}
              </td>

              <!-- Investigation Name & Parameter Summary -->
              <td class="px-4 py-2.5">
                <div class="font-semibold text-slate-900 flex items-center space-x-1.5">
                  <span>{{ t.name }}</span>
                  <span
                    v-if="(t.parameters?.length || t.parameters_count || 0) > 1"
                    class="inline-flex items-center px-1.5 py-0.2 rounded text-xs font-bold bg-sky-100 text-sky-800"
                  >
                    {{ t.parameters?.length || t.parameters_count }} params
                  </span>
                </div>
                <div v-if="t.parameters_summary" class="text-xs text-slate-500 mt-0.5 line-clamp-1">
                  {{ t.parameters_summary }}
                </div>
              </td>

              <!-- Badge / Architecture Layer -->
              <td class="px-3 py-2.5 whitespace-nowrap">
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border',
                    t.badge === 'System Default' ? 'bg-slate-50 text-slate-700 border-slate-300' :
                    (t.badge === 'Customized Default' ? 'bg-amber-50 text-amber-800 border-amber-300' :
                    'bg-purple-50 text-purple-800 border-purple-300')
                  ]"
                >
                  {{ t.badge }}
                </span>
              </td>

              <!-- Specimen / Container -->
              <td class="px-3 py-2.5 whitespace-nowrap">
                <div class="text-slate-800 font-medium">{{ t.specimen }}</div>
                <div class="text-xs text-slate-500 flex items-center mt-0.5">
                  <span
                    :class="[
                      'w-2 h-2 rounded-full mr-1 shrink-0',
                      t.tube_color.includes('Purple') ? 'bg-purple-600' :
                      (t.tube_color.includes('Red') ? 'bg-red-500' :
                      (t.tube_color.includes('Blue') ? 'bg-blue-500' :
                      (t.tube_color.includes('Grey') ? 'bg-slate-400' : 'bg-amber-400')))
                    ]"
                  />
                  {{ t.tube_color }}
                </div>
              </td>

              <!-- TAT -->
              <td class="px-3 py-2.5 text-center font-mono text-slate-600 whitespace-nowrap">
                {{ t.tat_hours }} hrs
              </td>

              <!-- Price -->
              <td class="px-4 py-2.5 text-right font-mono font-bold whitespace-nowrap">
                <span v-if="t.is_overridden && t.default_price && t.default_price !== t.price" class="text-xs text-slate-400 line-through mr-1.5 font-normal">
                  ₹{{ t.default_price }}
                </span>
                <span :class="t.is_overridden ? 'text-amber-800 font-extrabold' : 'text-slate-900'">
                  ₹{{ t.price }}
                </span>
              </td>

              <!-- Active Status -->
              <td class="px-3 py-2.5 text-center whitespace-nowrap">
                <button
                  type="button"
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border cursor-pointer transition',
                    t.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100' :
                    'bg-slate-100 text-slate-500 border-slate-300 hover:bg-slate-200'
                  ]"
                  @click="toggleActiveStatus(t)"
                >
                  {{ t.is_active ? 'Active' : 'Inactive' }}
                </button>
              </td>

              <!-- Sync State -->
              <td class="px-3 py-2.5 text-center whitespace-nowrap">
                <span
                  v-if="t.sync_status === 'pending'"
                  class="text-amber-600 flex items-center justify-center"
                  title="Local save committed; pending cloud synchronization"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </span>
                <span
                  v-else
                  class="text-emerald-600 flex items-center justify-center"
                  title="Synchronized with authenticated tenant"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </span>
              </td>

              <!-- Actions -->
              <td class="px-3 py-2.5 text-center whitespace-nowrap">
                <div class="flex items-center justify-center space-x-1.5">
                  <button
                    type="button"
                    class="px-2 py-1 bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 rounded text-xs font-semibold transition cursor-pointer"
                    @click="openDetailDrawer(t)"
                  >
                    Customize &amp; Parameters
                  </button>

                  <button
                    v-if="t.is_overridden"
                    type="button"
                    class="px-1.5 py-1 text-slate-400 hover:text-red-600 text-xs transition"
                    title="Reset to official system defaults"
                    @click="activeTest = t; resetCurrentTestOverride()"
                  >
                    Reset
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Component -->
      <PaginationBar
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total-items="filteredTests.length"
        :page-size-options="[15, 25, 50, 100]"
      />
    </div>

    <!-- Slide-over Drawer: Investigation & Granular Parameter Management -->
    <div
      v-if="isDetailDrawerOpen && activeTest"
      class="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-xs flex justify-end"
    >
      <div class="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col justify-between text-xs animate-slideLeft">
        <!-- Drawer Header -->
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div>
            <div class="flex items-center space-x-2">
              <span class="font-mono font-bold text-sky-800 text-sm">{{ activeTest.code }}</span>
              <span
                :class="[
                  'px-2 py-0.5 rounded-full text-xs font-semibold border',
                  activeTest.badge === 'System Default' ? 'bg-slate-100 text-slate-700 border-slate-300' :
                  (activeTest.badge === 'Customized Default' ? 'bg-amber-50 text-amber-800 border-amber-300' :
                  'bg-purple-50 text-purple-800 border-purple-300')
                ]"
              >
                {{ activeTest.badge }}
              </span>
            </div>
            <h2 class="text-base font-bold text-slate-900 mt-0.5">{{ activeTest.name }}</h2>
          </div>
          <button
            type="button"
            class="text-slate-400 hover:text-slate-600 text-lg font-bold p-1 cursor-pointer"
            @click="isDetailDrawerOpen = false"
          >
            &times;
          </button>
        </div>

        <!-- Drawer Body -->
        <div class="p-6 overflow-y-auto space-y-6 flex-1">
          <!-- Rate, TAT & Specimen Configurations -->
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <h3 class="font-bold text-slate-900 text-xs uppercase tracking-wider">
              Investigation Settings (Layer B Override)
            </h3>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block font-medium text-slate-700 mb-1">Standard Rate (₹)</label>
                <input
                  v-model.number="activeTest.price"
                  type="number"
                  min="0"
                  class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg font-mono font-bold text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
                />
                <span v-if="activeTest.default_price" class="text-xs text-slate-400 mt-0.5 block">
                  Default: ₹{{ activeTest.default_price }}
                </span>
              </div>

              <div>
                <label class="block font-medium text-slate-700 mb-1">Target TAT (Hours)</label>
                <input
                  v-model.number="activeTest.tat_hours"
                  type="number"
                  min="1"
                  class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg font-mono text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
                />
                <span v-if="activeTest.default_tat_hours" class="text-xs text-slate-400 mt-0.5 block">
                  Default: {{ activeTest.default_tat_hours }} hrs
                </span>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3 pt-1">
              <div>
                <label class="block font-medium text-slate-700 mb-1">Specimen Matrix</label>
                <input
                  v-model="activeTest.specimen"
                  class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900"
                />
              </div>
              <div>
                <label class="block font-medium text-slate-700 mb-1">Collection Tube</label>
                <input
                  v-model="activeTest.tube_color"
                  class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900"
                />
              </div>
            </div>

            <div class="pt-2 flex items-center justify-between border-t border-slate-200">
              <span class="font-medium text-slate-700">Available for Intake / Order Booking:</span>
              <button
                type="button"
                :class="[
                  'px-3 py-1 rounded text-xs font-bold transition cursor-pointer',
                  activeTest.is_active ? 'bg-emerald-600 text-white' : 'bg-slate-300 text-slate-700'
                ]"
                @click="activeTest.is_active = !activeTest.is_active"
              >
                {{ activeTest.is_active ? 'Active' : 'Inactive' }}
              </button>
            </div>
          </div>

          <!-- Reportable Parameters & Reference Ranges -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-bold text-slate-900 text-xs uppercase tracking-wider">
                  Reportable Parameters ({{ activeTest.parameters ? activeTest.parameters.length : 0 }})
                </h3>
                <p class="text-xs text-slate-500">Configure parameters, test units, and clinical reference intervals.</p>
              </div>

              <button
                type="button"
                class="inline-flex items-center space-x-1 px-2.5 py-1 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded text-xs shadow-2xs cursor-pointer"
                @click="addParameterToActiveTest"
              >
                <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                <span>Add Parameter</span>
              </button>
            </div>

            <div v-if="!activeTest.parameters || activeTest.parameters.length === 0" class="p-6 bg-slate-50 border border-slate-200 rounded-xl text-center text-slate-400">
              No sub-parameters configured. Click "Add Parameter" above to attach reportable analytes.
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="(param, pIdx) in activeTest.parameters"
                :key="pIdx"
                class="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs space-y-3 hover:border-slate-300 transition"
              >
                <!-- Parameter Header & Controls -->
                <div class="flex items-center justify-between gap-2">
                  <div class="flex items-center space-x-2 flex-1">
                    <span class="w-5 h-5 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-xs font-bold">
                      {{ pIdx + 1 }}
                    </span>
                    <input
                      v-model="param.name"
                      placeholder="Parameter Name (e.g. Hemoglobin)"
                      class="px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs font-semibold text-slate-900 flex-1 focus:bg-white focus:outline-none focus:ring-1 focus:ring-sky-500"
                    />
                    <input
                      v-model="param.code"
                      placeholder="Code (e.g. HB)"
                      class="w-24 px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs font-mono font-bold text-sky-800 uppercase focus:bg-white focus:outline-none focus:ring-1 focus:ring-sky-500"
                    />
                  </div>

                  <button
                    type="button"
                    class="text-slate-400 hover:text-red-600 p-1 cursor-pointer transition text-sm"
                    title="Remove parameter"
                    @click="removeParameterFromActiveTest(pIdx)"
                  >
                    &times;
                  </button>
                </div>

                <!-- Parameter Meta: Unit & Result Type -->
                <div class="grid grid-cols-3 gap-2">
                  <div>
                    <label class="block text-xs text-slate-500 mb-0.5">Unit of Measure</label>
                    <input
                      v-model="param.unit"
                      placeholder="e.g. g/dL, mg/dL, /cumm"
                      class="w-full px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs text-slate-800 font-mono"
                    />
                  </div>
                  <div>
                    <label class="block text-xs text-slate-500 mb-0.5">Result Type</label>
                    <select
                      v-model="param.result_type"
                      class="w-full px-2 py-1 bg-slate-50 border border-slate-200 rounded text-xs text-slate-800"
                    >
                      <option value="numeric">Numeric Value</option>
                      <option value="text">Descriptive Text</option>
                      <option value="qualitative">Qualitative (+/-)</option>
                      <option value="dropdown">Predefined Dropdown</option>
                      <option value="calculated">Calculated Formula</option>
                    </select>
                  </div>
                  <div class="flex items-end">
                    <label class="flex items-center space-x-1.5 cursor-pointer py-1">
                      <input
                        type="checkbox"
                        v-model="param.is_active"
                        class="rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                      />
                      <span class="text-xs text-slate-700 font-medium">Active on Reports</span>
                    </label>
                  </div>
                </div>

                <!-- Reference Ranges Table / Cards -->
                <div class="bg-slate-50/70 p-2.5 rounded-lg border border-slate-100 space-y-2">
                  <div class="flex items-center justify-between text-xs font-semibold text-slate-700">
                    <span>Clinical Reference Ranges</span>
                    <button
                      type="button"
                      class="text-sky-600 hover:text-sky-700 font-semibold cursor-pointer text-xs flex items-center space-x-0.5"
                      @click="addReferenceRangeToParam(param)"
                    >
                      <span>+ Add Interval</span>
                    </button>
                  </div>

                  <div v-if="!param.reference_ranges || param.reference_ranges.length === 0" class="text-xs text-slate-400">
                    No range configured. Click "+ Add Interval" to configure baseline normal ranges.
                  </div>

                  <div v-else class="space-y-1.5">
                    <div
                      v-for="(refR, rIdx) in param.reference_ranges"
                      :key="rIdx"
                      class="flex items-center space-x-2 text-xs"
                    >
                      <select
                        v-model="refR.sex"
                        class="w-20 px-1.5 py-0.5 bg-white border border-slate-200 rounded text-xs capitalize"
                      >
                        <option value="all">All / Both</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                      </select>

                      <input
                        v-model.number="refR.low_value"
                        type="number"
                        step="any"
                        placeholder="Min Low"
                        class="w-16 px-1.5 py-0.5 bg-white border border-slate-200 rounded text-xs font-mono text-center"
                      />
                      <span class="text-slate-400">-</span>
                      <input
                        v-model.number="refR.high_value"
                        type="number"
                        step="any"
                        placeholder="Max High"
                        class="w-16 px-1.5 py-0.5 bg-white border border-slate-200 rounded text-xs font-mono text-center"
                      />

                      <input
                        v-model="refR.text_range"
                        placeholder="Text interval (e.g. 13.0 - 17.5)"
                        class="flex-1 px-1.5 py-0.5 bg-white border border-slate-200 rounded text-xs"
                      />

                      <button
                        type="button"
                        class="text-slate-400 hover:text-red-500 cursor-pointer"
                        title="Remove interval"
                        @click="removeReferenceRangeFromParam(param, rIdx)"
                      >
                        &times;
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Drawer Footer -->
        <div class="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <button
            v-if="activeTest.is_overridden"
            type="button"
            class="px-3 py-1.5 text-xs text-red-600 hover:text-red-700 font-semibold border border-red-200 rounded-lg hover:bg-red-50 transition cursor-pointer"
            @click="resetCurrentTestOverride"
          >
            Reset to System Default
          </button>
          <div v-else></div>

          <div class="flex items-center space-x-2">
            <button
              type="button"
              class="px-3.5 py-1.5 border border-slate-300 text-slate-700 rounded-lg text-xs hover:bg-slate-100 font-medium cursor-pointer"
              @click="isDetailDrawerOpen = false"
            >
              Cancel
            </button>
            <button
              type="button"
              :disabled="drawerSaving"
              class="px-4 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-semibold shadow-xs transition cursor-pointer flex items-center space-x-1"
              @click="saveTestDrawerOverride"
            >
              <span>{{ drawerSaving ? 'Saving...' : 'Save Local Changes' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Mass Importer Modal -->
    <div
      v-if="isImportModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden text-left flex flex-col max-h-[90vh]">
        <!-- Modal Header -->
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 class="text-sm font-bold text-slate-900">Mass Importer — Pathology Test Master</h3>
            <p class="text-xs text-slate-500 mt-0.5">
              Supports .xlsx, .csv single-sheet (India Test Master) and two-sheet template formats. Works completely offline.
            </p>
          </div>
          <button type="button" class="text-slate-400 hover:text-slate-600 text-lg font-bold" @click="isImportModalOpen = false">&times;</button>
        </div>

        <!-- Modal Body -->
        <div class="p-6 overflow-y-auto space-y-4 flex-1 text-xs">
          <!-- Step 1: Upload -->
          <div v-if="importStep === 'upload'" class="space-y-4">
            <!-- Mode selection -->
            <div>
              <label class="block font-medium text-slate-700 mb-1">Import Mode:</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  :class="[
                    'p-2.5 rounded-lg border text-left cursor-pointer transition',
                    importMode === 'upsert' ? 'bg-sky-50 border-sky-500 text-sky-900 ring-1 ring-sky-500' : 'bg-slate-50 border-slate-200 text-slate-700'
                  ]"
                  @click="importMode = 'upsert'"
                >
                  <div class="font-bold">Upsert (Recommended)</div>
                  <div class="text-xs text-slate-500 mt-0.5">Create new investigations and update existing rates/TAT</div>
                </button>

                <button
                  type="button"
                  :class="[
                    'p-2.5 rounded-lg border text-left cursor-pointer transition',
                    importMode === 'insert_only' ? 'bg-sky-50 border-sky-500 text-sky-900 ring-1 ring-sky-500' : 'bg-slate-50 border-slate-200 text-slate-700'
                  ]"
                  @click="importMode = 'insert_only'"
                >
                  <div class="font-bold">Insert Only</div>
                  <div class="text-xs text-slate-500 mt-0.5">Add new records; skip existing without altering customizations</div>
                </button>

                <button
                  type="button"
                  :class="[
                    'p-2.5 rounded-lg border text-left cursor-pointer transition',
                    importMode === 'update_existing' ? 'bg-sky-50 border-sky-500 text-sky-900 ring-1 ring-sky-500' : 'bg-slate-50 border-slate-200 text-slate-700'
                  ]"
                  @click="importMode = 'update_existing'"
                >
                  <div class="font-bold">Update Existing</div>
                  <div class="text-xs text-slate-500 mt-0.5">Only modify rates/TAT for already existing investigations</div>
                </button>
              </div>
            </div>

            <!-- Dropzone -->
            <div class="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-sky-500 transition cursor-pointer bg-slate-50/50">
              <input
                type="file"
                accept=".xlsx,.xls,.csv"
                class="hidden"
                id="catalogFileInput"
                @change="handleFileUpload"
              />
              <label for="catalogFileInput" class="cursor-pointer block">
                <svg class="mx-auto h-10 w-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <div class="mt-2 text-xs font-semibold text-slate-700">
                  Click to select or drag &amp; drop your Excel or CSV catalog file
                </div>
                <div class="text-xs text-slate-400 mt-1">
                  Supports india_pathology_test_master_single_sheet.xlsx (1,400+ investigations)
                </div>
              </label>
            </div>
          </div>

          <!-- Step 2: Preview -->
          <div v-else-if="importStep === 'preview'" class="space-y-4">
            <div class="grid grid-cols-4 gap-2">
              <div class="bg-emerald-50 border border-emerald-200 p-2.5 rounded text-center">
                <div class="text-lg font-bold text-emerald-700">{{ importPreview.new_count }}</div>
                <div class="text-xs text-emerald-800 font-medium">New Investigations</div>
              </div>
              <div class="bg-blue-50 border border-blue-200 p-2.5 rounded text-center">
                <div class="text-lg font-bold text-blue-700">{{ importPreview.updated_count }}</div>
                <div class="text-xs text-blue-800 font-medium">Updated / Overridden</div>
              </div>
              <div class="bg-slate-100 border border-slate-200 p-2.5 rounded text-center">
                <div class="text-lg font-bold text-slate-700">{{ importPreview.skipped_count }}</div>
                <div class="text-xs text-slate-600 font-medium">Skipped Records</div>
              </div>
              <div class="bg-amber-50 border border-amber-200 p-2.5 rounded text-center">
                <div class="text-lg font-bold text-amber-700">{{ importPreview.invalid_count }}</div>
                <div class="text-xs text-amber-800 font-medium">Needs Review</div>
              </div>
            </div>

            <div class="border-b border-slate-200 flex space-x-4 text-xs font-medium">
              <button
                type="button"
                :class="['pb-2 cursor-pointer transition', activePreviewTab === 'new' ? 'text-sky-600 border-b-2 border-sky-600 font-bold' : 'text-slate-500']"
                @click="activePreviewTab = 'new'"
              >
                New Tests ({{ importPreview.new_tests.length }})
              </button>
              <button
                type="button"
                :class="['pb-2 cursor-pointer transition', activePreviewTab === 'updates' ? 'text-sky-600 border-b-2 border-sky-600 font-bold' : 'text-slate-500']"
                @click="activePreviewTab = 'updates'"
              >
                Rate Adjustments ({{ importPreview.price_changes.length }})
              </button>
              <button
                type="button"
                :class="['pb-2 cursor-pointer transition', activePreviewTab === 'skipped' ? 'text-sky-600 border-b-2 border-sky-600 font-bold' : 'text-slate-500']"
                @click="activePreviewTab = 'skipped'"
              >
                Skipped ({{ importPreview.skipped_tests.length }})
              </button>
            </div>

            <div class="border border-slate-200 rounded max-h-56 overflow-y-auto">
              <table class="min-w-full divide-y divide-slate-200 text-xs">
                <thead class="bg-slate-50 text-slate-600 font-semibold sticky top-0">
                  <tr>
                    <th class="px-3 py-1.5 text-left">Code</th>
                    <th class="px-3 py-1.5 text-left">Name</th>
                    <th class="px-3 py-1.5 text-right">Price</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 bg-white">
                  <tr v-for="(item, idx) in (activePreviewTab === 'new' ? importPreview.new_tests : (activePreviewTab === 'updates' ? importPreview.price_changes : importPreview.skipped_tests))" :key="idx">
                    <td class="px-3 py-1.5 font-mono font-bold text-sky-800">{{ item.code }}</td>
                    <td class="px-3 py-1.5 text-slate-900">{{ item.name }}</td>
                    <td class="px-3 py-1.5 text-right font-mono">
                      <span v-if="item.old_price !== undefined" class="text-slate-400 line-through mr-1">₹{{ item.old_price }}</span>
                      <span class="font-bold text-slate-900">₹{{ item.new_price || item.price || 0 }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Step 3: Importing Spinner -->
          <div v-else-if="importStep === 'importing'" class="py-12 text-center space-y-3">
            <svg class="h-8 w-8 animate-spin mx-auto text-sky-600" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <div class="font-bold text-slate-800 text-sm">Persisting Investigations Locally...</div>
            <div class="text-xs text-slate-500">Writing records to local database and queueing cloud sync.</div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <button
            type="button"
            class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded text-xs hover:bg-slate-100"
            @click="isImportModalOpen = false"
          >
            Cancel
          </button>

          <div v-if="importStep === 'preview'" class="flex items-center space-x-2">
            <button
              type="button"
              class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded text-xs hover:bg-slate-100"
              @click="importStep = 'upload'"
            >
              Choose Different File
            </button>
            <button
              type="button"
              class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold shadow-xs transition cursor-pointer"
              @click="confirmMassImport"
            >
              Confirm &amp; Import {{ parsedImportTests.length }} Items
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bulk Update Modal -->
    <div
      v-if="isBulkModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden text-left">
        <div class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-sm font-bold text-slate-900">
            Bulk Action ({{ selectedTestIds.length }} Tests)
          </h3>
          <button type="button" class="text-slate-400 hover:text-slate-600 text-lg font-bold" @click="isBulkModalOpen = false">&times;</button>
        </div>

        <div class="p-5 space-y-4 text-xs">
          <div v-if="bulkActionType === 'fixed'">
            <label class="block font-medium text-slate-700 mb-1">Set Standard Rate to Fixed Amount (₹):</label>
            <input
              v-model.number="bulkPriceValue"
              type="number"
              min="0"
              class="w-full px-3 py-1.5 border border-slate-300 rounded font-mono font-bold text-slate-900"
            />
          </div>

          <div v-else-if="bulkActionType === 'increase_pct'">
            <label class="block font-medium text-slate-700 mb-1">Increase Rates by Percentage (%):</label>
            <input
              v-model.number="bulkPriceValue"
              type="number"
              min="1"
              max="200"
              class="w-full px-3 py-1.5 border border-slate-300 rounded font-mono font-bold text-slate-900"
            />
          </div>

          <div v-else-if="bulkActionType === 'tat'">
            <label class="block font-medium text-slate-700 mb-1">Assign Common TAT Target (Hours):</label>
            <select v-model.number="bulkTatValue" class="w-full px-3 py-1.5 border border-slate-300 rounded bg-white">
              <option :value="2">2 Hours (Urgent / Routine Blood)</option>
              <option :value="4">4 Hours (Standard Pathology)</option>
              <option :value="6">6 Hours (Immuno / Specialized)</option>
              <option :value="8">8 Hours (Vitamins / Hormones)</option>
              <option :value="24">24 Hours (Cultures / Biopsy)</option>
            </select>
          </div>

          <div v-else-if="bulkActionType === 'activate'">
            <p class="text-slate-600">Activate all {{ selectedTestIds.length }} selected investigations for new order booking.</p>
          </div>

          <div v-else-if="bulkActionType === 'deactivate'">
            <p class="text-amber-800 bg-amber-50 p-2.5 rounded border border-amber-200">
              Deactivate all {{ selectedTestIds.length }} selected investigations. Deactivated tests will be hidden from new orders but preserved in historical reports and invoices.
            </p>
          </div>
        </div>

        <div class="px-5 py-3.5 bg-slate-50 border-t border-slate-200 flex justify-end space-x-2">
          <button
            type="button"
            class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded text-xs hover:bg-slate-100"
            @click="isBulkModalOpen = false"
          >
            Cancel
          </button>
          <button
            type="button"
            :disabled="bulkSaving"
            class="px-4 py-1.5 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded text-xs shadow-xs"
            @click="applyBulkUpdate"
          >
            {{ bulkSaving ? 'Applying...' : 'Apply to Selected Tests' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Add Custom Investigation Modal with Complete Parameter Builder -->
    <div
      v-if="isCreateModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden text-left flex flex-col max-h-[90vh]">
        <!-- Header -->
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 class="text-sm font-bold text-slate-900">Add Custom Investigation (Layer B)</h3>
            <p class="text-xs text-slate-500 mt-0.5">Define custom test code, rates, and reportable clinical parameters.</p>
          </div>
          <button type="button" class="text-slate-400 hover:text-slate-600 text-lg font-bold" @click="isCreateModalOpen = false">&times;</button>
        </div>

        <!-- Form Body -->
        <form class="p-6 overflow-y-auto space-y-5 flex-1 text-xs" @submit.prevent="createTest">
          <!-- Section 1: Basic Investigation Details -->
          <div class="space-y-3">
            <h4 class="font-bold text-slate-900 text-xs uppercase tracking-wider">1. Investigation Metadata</h4>

            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="block font-medium text-slate-700 mb-1">Test Code *</label>
                <input
                  v-model="newTest.code"
                  required
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono uppercase focus:ring-1 focus:ring-sky-500 focus:outline-none"
                  placeholder="e.g. SER_IRON"
                />
              </div>
              <div class="col-span-2">
                <label class="block font-medium text-slate-700 mb-1">Investigation Name *</label>
                <input
                  v-model="newTest.name"
                  required
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded focus:ring-1 focus:ring-sky-500 focus:outline-none"
                  placeholder="e.g. Serum Iron & TIBC Profile"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block font-medium text-slate-700 mb-1">Discipline</label>
                <select v-model="newTest.department" class="w-full px-2.5 py-1.5 border border-slate-300 rounded bg-white">
                  <option v-for="d in departments.slice(1)" :key="d" :value="d">{{ d }}</option>
                </select>
              </div>
              <div>
                <label class="block font-medium text-slate-700 mb-1">Specimen Tube</label>
                <select v-model="newTest.tube_color" class="w-full px-2.5 py-1.5 border border-slate-300 rounded bg-white">
                  <option value="Red (Plain / Gel)">Red (Plain / Gel Serum)</option>
                  <option value="Purple (EDTA)">Purple (EDTA Whole Blood)</option>
                  <option value="Grey (Fluoride)">Grey (Sodium Fluoride Plasma)</option>
                  <option value="Blue (Citrate)">Blue (Sodium Citrate)</option>
                  <option value="Yellow (Urine)">Yellow (Sterile Urine Container)</option>
                </select>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block font-medium text-slate-700 mb-1">Standard Rate (₹) *</label>
                <input
                  v-model.number="newTest.price"
                  type="number"
                  min="0"
                  required
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono font-bold"
                />
              </div>
              <div>
                <label class="block font-medium text-slate-700 mb-1">Target TAT (Hours) *</label>
                <input
                  v-model.number="newTest.tat_hours"
                  type="number"
                  min="1"
                  required
                  class="w-full px-2.5 py-1.5 border border-slate-300 rounded font-mono"
                />
              </div>
            </div>
          </div>

          <!-- Section 2: Reportable Parameters Builder -->
          <div class="space-y-3 pt-3 border-t border-slate-200">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="font-bold text-slate-900 text-xs uppercase tracking-wider">
                  2. Reportable Parameters ({{ newTest.parameters.length }})
                </h4>
                <p class="text-xs text-slate-500">Every investigation must support 1 or more reportable parameters.</p>
              </div>

              <button
                type="button"
                class="inline-flex items-center space-x-1 px-2.5 py-1 bg-sky-50 text-sky-700 border border-sky-300 hover:bg-sky-100 font-semibold rounded text-xs transition cursor-pointer"
                @click="addParameterToNewTest"
              >
                <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                <span>Add Parameter</span>
              </button>
            </div>

            <div class="space-y-3">
              <div
                v-for="(param, pIdx) in newTest.parameters"
                :key="pIdx"
                class="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2.5"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="w-5 h-5 rounded-full bg-sky-100 text-sky-800 flex items-center justify-center text-xs font-bold">
                    {{ pIdx + 1 }}
                  </span>
                  <input
                    v-model="param.name"
                    required
                    placeholder="Parameter Name (e.g. Total Iron)"
                    class="flex-1 px-2 py-1 bg-white border border-slate-200 rounded font-semibold text-slate-900"
                  />
                  <input
                    v-model="param.code"
                    placeholder="Code (e.g. FE)"
                    class="w-24 px-2 py-1 bg-white border border-slate-200 rounded font-mono text-sky-800 uppercase"
                  />
                  <button
                    v-if="newTest.parameters.length > 1"
                    type="button"
                    class="text-slate-400 hover:text-red-600 p-1 cursor-pointer text-sm"
                    title="Remove parameter"
                    @click="removeParameterFromNewTest(pIdx)"
                  >
                    &times;
                  </button>
                </div>

                <div class="grid grid-cols-3 gap-2">
                  <div>
                    <label class="block text-xs text-slate-500 mb-0.5">Unit of Measure</label>
                    <input
                      v-model="param.unit"
                      placeholder="e.g. µg/dL, mg/dL"
                      class="w-full px-2 py-1 bg-white border border-slate-200 rounded font-mono text-xs"
                    />
                  </div>
                  <div>
                    <label class="block text-xs text-slate-500 mb-0.5">Result Type</label>
                    <select v-model="param.result_type" class="w-full px-2 py-1 bg-white border border-slate-200 rounded text-xs">
                      <option value="numeric">Numeric Value</option>
                      <option value="text">Descriptive Text</option>
                      <option value="qualitative">Qualitative (+/-)</option>
                      <option value="dropdown">Dropdown</option>
                      <option value="calculated">Calculated Formula</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs text-slate-500 mb-0.5">Reference Interval</label>
                    <div v-for="(refR, rIdx) in (param.reference_ranges || [])" :key="rIdx">
                      <input
                        v-model="refR.text_range"
                        placeholder="e.g. 60 - 170 µg/dL"
                        class="w-full px-2 py-1 bg-white border border-slate-200 rounded text-xs"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer Actions -->
          <div class="flex justify-end space-x-2 pt-3 border-t border-slate-200">
            <button
              type="button"
              class="px-3 py-1.5 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 cursor-pointer"
              @click="isCreateModalOpen = false"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-1.5 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-lg shadow-xs cursor-pointer"
            >
              Save Custom Investigation
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes slideLeft {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.animate-slideLeft {
  animation: slideLeft 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.15s ease-out;
}
</style>
