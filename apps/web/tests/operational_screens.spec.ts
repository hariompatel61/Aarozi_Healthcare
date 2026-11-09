import { describe, it, expect } from 'vitest'
import InvoicesPage from '../pages/billing/invoices.vue'
import ReferralsPage from '../pages/billing/referrals.vue'
import DonorsPage from '../pages/blood_bank/donors.vue'
import InventoryPage from '../pages/blood_bank/inventory.vue'
import CrossmatchPage from '../pages/blood_bank/crossmatch.vue'
import CatalogPage from '../pages/pathology/catalog.vue'
import VerificationPage from '../pages/pathology/verification.vue'
import ReleasePage from '../pages/reporting/release.vue'
import LicensingPage from '../pages/admin/licensing.vue'
import LoginPage from '../pages/login.vue'
import DashboardPage from '../pages/dashboard.vue'
import PatientsIndexPage from '../pages/patients/index.vue'

describe('Operational Clinical and Financial Pages', () => {
  it('successfully exports Billing & Financial screens', () => {
    expect(InvoicesPage).toBeDefined()
    expect(ReferralsPage).toBeDefined()
  })

  it('successfully exports Blood Bank management screens', () => {
    expect(DonorsPage).toBeDefined()
    expect(InventoryPage).toBeDefined()
    expect(CrossmatchPage).toBeDefined()
  })

  it('successfully exports Pathology LIS & Workstation screens', () => {
    expect(CatalogPage).toBeDefined()
    expect(VerificationPage).toBeDefined()
    expect(ReleasePage).toBeDefined()
  })

  it('successfully exports System Administration and Authentication screens', () => {
    expect(LicensingPage).toBeDefined()
    expect(LoginPage).toBeDefined()
    expect(DashboardPage).toBeDefined()
    expect(PatientsIndexPage).toBeDefined()
  })
})
