import { ref, reactive, computed, onMounted, getCurrentInstance } from 'vue'
import { useToast } from '~/composables/useToast'

export type ThemeId = 'drlogy' | 'healthplus' | 'medicore' | 'guru' | 'varad' | 'dragon'

export interface LabIdentity {
  labName: string
  tagline: string
  logoUrl: string
  address: string
  phoneNumbers: string
  email: string
  website: string
  homeCollectionPhone: string
  isoNablBadges: boolean
}

export interface Signatory {
  id: string
  name: string
  qualification: string
  designation: string
  regNo: string
  signatureImageUrl: string
  enabled: boolean
}

export interface ThemePrintOptions {
  primaryColor: string
  showWatermark: boolean
  showQrAndBarcode: boolean
  letterheadMode: 'blank' | 'preprinted'
  marginMm: number
  preprintedTopMarginMm: number
  preprintedBottomMarginMm: number
}

export interface ReportThemeInfo {
  id: ThemeId
  name: string
  tagline: string
  badge: string
  accentColor: string
  description: string
  highlights: string[]
}

export const REPORT_THEMES: ReportThemeInfo[] = [
  {
    id: 'drlogy',
    name: 'Drlogy Modern Blue',
    tagline: 'Diagonal Stripes & Home Delivery Ribbon',
    badge: 'Most Popular',
    accentColor: '#0052cc',
    description: 'Modern Indian lab report featuring bold dual-tone blue logo, diagonal striped dividers, 3-column patient header with QR/barcode, and home collection WhatsApp footer ribbon.',
    highlights: ['Diagonal striped dividers', 'Home collection delivery scooter badge', '3 Signatory footer columns'],
  },
  {
    id: 'healthplus',
    name: 'HealthPlus Clinical Navy',
    tagline: 'Structured Card & Out-of-Range Badges',
    badge: 'Clinical Standard',
    accentColor: '#0c3b5e',
    description: 'Corporate diagnostic report with dark navy banner, structured icon grid for patient demographics, boxed verification QR, and high-visibility red out-of-range flag badges.',
    highlights: ['Dark navy block headers', 'Iconified patient info cards', 'Red arrow high/low flag badges'],
  },
  {
    id: 'medicore',
    name: 'MediCore Eco Green',
    tagline: 'ISO/NABL Accreditations & Dual QR Layout',
    badge: 'Eco & NABL',
    accentColor: '#16a34a',
    description: 'Clean medical green theme with dual accreditation badges (NABL & ISO), green contact strip, inline barcode, and bottom E-Report QR booking barcode.',
    highlights: ['Dual ISO & IAF certification badges', 'Inline 1D barcode under table', 'Bottom booking QR code'],
  },
  {
    id: 'guru',
    name: 'Guru Vertical Sidebar',
    tagline: 'Full-Height Vertical Accent Strip & Path Lab 2.0',
    badge: 'Distinctive',
    accentColor: '#0f2942',
    description: 'A distinctive layout featuring a full-height dark blue vertical sidebar on the left margin, pill title badge, and dual-tone blue/magenta home collection footer.',
    highlights: ['Full-height vertical sidebar strip', 'Path Lab 2.0 footer badge', 'Dual-tone WhatsApp footer'],
  },
  {
    id: 'varad',
    name: 'Varad Classic Doctor Letterhead',
    tagline: 'Traditional Indian Clinic Letterhead Style',
    badge: 'Classic Heritage',
    accentColor: '#881337',
    description: 'Traditional clinic & nursing home letterhead with maroon consultant doctor profile on top right, uppercase colon-aligned patient details, and clean red/blue border lines.',
    highlights: ['Right consultant doctor letterhead', 'Colon-aligned classic patient block', 'Traditional prescription style'],
  },
  {
    id: 'dragon',
    name: 'DragonHealth Gold & Charcoal',
    tagline: 'Split Charcoal/Yellow Ribbon & Compact Grid',
    badge: 'Executive',
    accentColor: '#1e293b',
    description: 'High-contrast executive report with charcoal black header, bright gold contact ribbon, overlapping emblem logo, and dense structured grid cells.',
    highlights: ['Charcoal & gold split banner', 'Compact multi-column grid', 'Dual license signatory blocks'],
  },
]

// Singleton Shared Reactive State
const currentThemeId = ref<ThemeId>('drlogy')

const labIdentity = reactive<LabIdentity>({
  labName: 'Drlogy Pathology Lab',
  tagline: 'Accurate | Caring | Instant',
  logoUrl: '',
  address: 'Plot 42, Knowledge Park III, Greater Noida, UP - 201310',
  phoneNumbers: '+91 98765 43210 / +91 98111 22233',
  email: 'reports@aarozi.health',
  website: 'www.aarozi.health',
  homeCollectionPhone: '+91 98765 43210',
  isoNablBadges: true,
})

const signatories = ref<Signatory[]>([
  {
    id: 'sig-1',
    name: 'Pooja Verma',
    qualification: 'DMLT, BMLT',
    designation: 'Medical Lab Technician',
    regNo: 'MLT-9021',
    signatureImageUrl: '',
    enabled: true,
  },
  {
    id: 'sig-2',
    name: 'Dr. Payal Shah',
    qualification: 'MD, Pathologist',
    designation: 'Consultant Pathologist',
    regNo: 'MCI-48921',
    signatureImageUrl: '',
    enabled: true,
  },
  {
    id: 'sig-3',
    name: 'Dr. Vimal Shah',
    qualification: 'MD, Pathologist',
    designation: 'Chief Pathologist',
    regNo: 'Reg. No: MCI 1345',
    signatureImageUrl: '',
    enabled: true,
  },
])

const themeOptions = reactive<ThemePrintOptions>({
  primaryColor: '#0052cc',
  showWatermark: true,
  showQrAndBarcode: true,
  letterheadMode: 'blank',
  marginMm: 10,
  preprintedTopMarginMm: 38,
  preprintedBottomMarginMm: 28,
})

export function useReportTheme() {
  const { success, info } = useToast()

  function loadSavedSettings() {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('aarozi_report_theme_settings')
        if (saved) {
          const parsed = JSON.parse(saved)
          if (parsed.currentThemeId && REPORT_THEMES.some((t) => t.id === parsed.currentThemeId)) {
            currentThemeId.value = parsed.currentThemeId
          }
          if (parsed.labIdentity) {
            Object.assign(labIdentity, parsed.labIdentity)
          }
          if (Array.isArray(parsed.signatories)) {
            signatories.value = parsed.signatories
          }
          if (parsed.themeOptions) {
            Object.assign(themeOptions, parsed.themeOptions)
          }
        }
      } catch (err) {
        console.warn('Could not parse saved theme settings:', err)
      }
    }
  }

  // Auto-init safely
  if (typeof window !== 'undefined') {
    if (getCurrentInstance()) {
      onMounted(loadSavedSettings)
    } else {
      loadSavedSettings()
    }
  }

  const DEFAULT_THEME: ReportThemeInfo = REPORT_THEMES[0]!

  const currentTheme = computed<ReportThemeInfo>(() => {
    return REPORT_THEMES.find((t) => t.id === currentThemeId.value) ?? DEFAULT_THEME
  })

  function selectTheme(id: ThemeId) {
    currentThemeId.value = id
    const theme = REPORT_THEMES.find((t) => t.id === id)
    if (theme) {
      themeOptions.primaryColor = theme.accentColor
      // Contextual presets
      if (id === 'drlogy') {
        labIdentity.labName = 'Drlogy Pathology Lab'
        labIdentity.tagline = 'Accurate | Caring | Instant'
      } else if (id === 'healthplus') {
        labIdentity.labName = 'HealthPlus Diagnostics'
        labIdentity.tagline = 'Accurate Tests, Better Care'
      } else if (id === 'medicore') {
        labIdentity.labName = 'MediCore Reference Lab'
        labIdentity.tagline = 'Healing Through Precision & Care'
      } else if (id === 'guru') {
        labIdentity.labName = 'Guru Diagnostic Center'
        labIdentity.tagline = 'Comprehensive Pathology & Clinical Care'
      } else if (id === 'varad') {
        labIdentity.labName = 'Varad Clinic & Nursing Home'
        labIdentity.tagline = 'Trusted Healthcare Since 1998'
      } else if (id === 'dragon') {
        labIdentity.labName = 'DragonHealth Clinical Labs'
        labIdentity.tagline = 'State-of-the-Art Automated Diagnostics'
      }
      info('Theme Selected', `Loaded layout for "${theme.name}"`)
    }
  }

  function saveAsDefault() {
    if (typeof window !== 'undefined') {
      const payload = {
        currentThemeId: currentThemeId.value,
        labIdentity: { ...labIdentity },
        signatories: signatories.value,
        themeOptions: { ...themeOptions },
      }
      localStorage.setItem('aarozi_report_theme_settings', JSON.stringify(payload))
      success(
        'Default Theme Saved!',
        `"${currentTheme.value.name}" is now the primary letterhead for all laboratory reports & patient printouts.`
      )
    }
  }

  function resetToDefaults() {
    selectTheme('drlogy')
    labIdentity.labName = 'Drlogy Pathology Lab'
    labIdentity.tagline = 'Accurate | Caring | Instant'
    labIdentity.logoUrl = ''
    labIdentity.address = 'Plot 42, Knowledge Park III, Greater Noida, UP - 201310'
    labIdentity.phoneNumbers = '+91 98765 43210 / +91 98111 22233'
    labIdentity.email = 'reports@aarozi.health'
    labIdentity.website = 'www.aarozi.health'
    labIdentity.homeCollectionPhone = '+91 98765 43210'
    labIdentity.isoNablBadges = true

    themeOptions.primaryColor = '#0052cc'
    themeOptions.showWatermark = true
    themeOptions.showQrAndBarcode = true
    themeOptions.letterheadMode = 'blank'

    saveAsDefault()
    info('Defaults Restored', 'Theme configuration reset to standard Drlogy layout.')
  }

  return {
    themes: REPORT_THEMES,
    currentThemeId,
    currentTheme,
    labIdentity,
    signatories,
    themeOptions,
    selectTheme,
    saveAsDefault,
    resetToDefaults,
    loadSavedSettings,
  }
}
