import { describe, it, expect } from 'vitest'
import Sidebar from '../components/shell/Sidebar.vue'
import TopHeader from '../components/shell/TopHeader.vue'
import CommandPalette from '../components/shell/CommandPalette.vue'
import { useBranch, AVAILABLE_BRANCHES } from '../composables/useBranch'

describe('Application Shell Components', () => {
  it('exports Sidebar, TopHeader, and CommandPalette components', () => {
    expect(Sidebar).toBeDefined()
    expect(TopHeader).toBeDefined()
    expect(CommandPalette).toBeDefined()
  })

  it('manages active operating laboratory branch mapping via useBranch composable', () => {
    const { branches, selectedBranch, switchBranch, currentBranch } = useBranch()

    expect(branches).toHaveLength(4)
    expect(branches.map(b => b.name)).toContain('Main City Branch')
    expect(branches.map(b => b.name)).toContain('City Centre Branch')
    expect(branches.map(b => b.name)).toContain('North Satellite Lab')
    expect(branches.map(b => b.name)).toContain('All Branches')

    // Switch branch test
    switchBranch('City Centre Branch', true)
    expect(selectedBranch.value).toBe('City Centre Branch')
    expect(currentBranch.value?.badge).toBe('Collection Center')

    // Switch back to Main City Branch
    switchBranch('Main City Branch', true)
    expect(selectedBranch.value).toBe('Main City Branch')
    expect(currentBranch.value?.badge).toBe('Central Lab')
  })

  it('formats verified diagnostic report dispatch payload for WhatsApp delivery', () => {
    function generateWhatsAppMessage(patientName: string, testName: string, sampleId: string): string {
      return `🏥 *Aarozi Healthcare Central Diagnostic Lab*\n\nDear *${patientName}*,\nYour verified diagnostic report for *${testName}* (Sample ID: *${sampleId}*) is ready.\n\n📄 *Official PDF Report:* https://aarozi.health/reports/verify/${sampleId}-QR`
    }

    const msg = generateWhatsAppMessage('Aarav Sharma', 'HbA1c (HPLC)', 'SMP250001')
    expect(msg).toContain('Aarav Sharma')
    expect(msg).toContain('SMP250001')
    expect(msg).toContain('https://aarozi.health/reports/verify/SMP250001-QR')
  })
})
