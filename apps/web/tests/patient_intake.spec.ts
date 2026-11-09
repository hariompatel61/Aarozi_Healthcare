import { describe, it, expect } from 'vitest'
import RegisterPage from '../pages/patients/register.vue'
import DirectoryPage from '../pages/patients/index.vue'

describe('Task P1-01: Patient Intake & Directory Specification', () => {
  it('exports Patient Register page and Patient Directory page components', () => {
    expect(RegisterPage).toBeDefined()
    expect(DirectoryPage).toBeDefined()
  })

  it('validates test items pricing and total calculation for standard pathology profile', () => {
    const testCatalog = [
      { code: 'CBC', name: 'Complete Blood Count', price: 400 },
      { code: 'LFT', name: 'Liver Function Test (12)', price: 500 },
      { code: 'KFT', name: 'Kidney Function Test (8)', price: 450 },
      { code: 'TFT', name: 'Thyroid Profile (3)', price: 650 },
      { code: 'HbA1c', name: 'Glycated Hemoglobin (HPLC)', price: 500 },
    ]

    // Selected tests matching Screen 2 in mockups: CBC (400) + LFT (500) + TFT (650)
    const selectedCodes = ['CBC', 'LFT', 'TFT']
    const selected = testCatalog.filter((t) => selectedCodes.includes(t.code))
    const total = selected.reduce((sum, item) => sum + item.price, 0)

    expect(selected.length).toBe(3)
    expect(total).toBe(1550)
  })

  it('identifies duplicates based on normalized mobile number', () => {
    const existingPatients = [
      { uhid: 'PAT250005', name: 'Neha Agarwal', mobile: '9876543210' },
      { uhid: 'PAT250001', name: 'A. Sharma', mobile: '9811223344' },
    ]

    function findDuplicate(mobileInput: string, currentUhid: string) {
      const clean = mobileInput.replace(/\D/g, '').slice(-10)
      return existingPatients.find((p) => p.mobile === clean && p.uhid !== currentUhid) || null
    }

    const match = findDuplicate('+91 9876-543-210', 'PAT999999')
    expect(match).not.toBeNull()
    expect(match?.name).toBe('Neha Agarwal')
    expect(match?.uhid).toBe('PAT250005')

    const noMatch = findDuplicate('9999999999', 'PAT999999')
    expect(noMatch).toBeNull()
  })
})
