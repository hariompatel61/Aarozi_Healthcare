import { describe, it, expect, beforeEach } from 'vitest'
import { useReportTheme, REPORT_THEMES, type ThemeId } from '../composables/useReportTheme'

describe('Pathology Report Theme & Branding Engine', () => {
  beforeEach(() => {
    const { resetToDefaults } = useReportTheme()
    resetToDefaults()
  })

  it('exposes exactly 6 pre-built A4 pathology report themes', () => {
    expect(REPORT_THEMES.length).toBe(6)
    const themeIds = REPORT_THEMES.map((t) => t.id)
    expect(themeIds).toContain('drlogy')
    expect(themeIds).toContain('healthplus')
    expect(themeIds).toContain('medicore')
    expect(themeIds).toContain('guru')
    expect(themeIds).toContain('varad')
    expect(themeIds).toContain('dragon')
  })

  it('switches themes and sets appropriate accent colors & branding presets', () => {
    const { selectTheme, currentThemeId, themeOptions, labIdentity } = useReportTheme()

    selectTheme('healthplus')
    expect(currentThemeId.value).toBe('healthplus')
    expect(themeOptions.primaryColor).toBe('#0c3b5e')
    expect(labIdentity.labName).toContain('HealthPlus')

    selectTheme('medicore')
    expect(currentThemeId.value).toBe('medicore')
    expect(themeOptions.primaryColor).toBe('#16a34a')
    expect(labIdentity.labName).toContain('MediCore')

    selectTheme('guru')
    expect(currentThemeId.value).toBe('guru')
    expect(themeOptions.primaryColor).toBe('#0f2942')

    selectTheme('varad')
    expect(currentThemeId.value).toBe('varad')
    expect(themeOptions.primaryColor).toBe('#881337')

    selectTheme('dragon')
    expect(currentThemeId.value).toBe('dragon')
    expect(themeOptions.primaryColor).toBe('#1e293b')
  })

  it('manages 3 distinct signatories in the footer', () => {
    const { signatories } = useReportTheme()
    expect(signatories.value.length).toBe(3)

    // Left signatory (Lab Tech)
    expect(signatories.value[0]?.designation).toBe('Medical Lab Technician')
    expect(signatories.value[0]?.enabled).toBe(true)

    // Center signatory (Consultant Pathologist)
    expect(signatories.value[1]?.qualification).toContain('Pathologist')

    // Right signatory (Chief Pathologist)
    expect(signatories.value[2]?.regNo).toBeDefined()
  })

  it('supports pre-printed letterhead mode with configurable margins', () => {
    const { themeOptions } = useReportTheme()
    expect(themeOptions.letterheadMode).toBe('blank')

    themeOptions.letterheadMode = 'preprinted'
    themeOptions.preprintedTopMarginMm = 40
    themeOptions.preprintedBottomMarginMm = 30

    expect(themeOptions.letterheadMode).toBe('preprinted')
    expect(themeOptions.preprintedTopMarginMm).toBe(40)
    expect(themeOptions.preprintedBottomMarginMm).toBe(30)
  })

  it('toggles watermark, QR code, and NABL badges', () => {
    const { themeOptions, labIdentity } = useReportTheme()

    expect(themeOptions.showWatermark).toBe(true)
    expect(themeOptions.showQrAndBarcode).toBe(true)
    expect(labIdentity.isoNablBadges).toBe(true)

    themeOptions.showWatermark = false
    themeOptions.showQrAndBarcode = false
    labIdentity.isoNablBadges = false

    expect(themeOptions.showWatermark).toBe(false)
    expect(themeOptions.showQrAndBarcode).toBe(false)
    expect(labIdentity.isoNablBadges).toBe(false)
  })
})
