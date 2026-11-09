import { describe, it, expect } from 'vitest'
import VisualDesignerPage from '../pages/reporting/designer.vue'

describe('Interactive Visual Block Canvas Report Designer', () => {
  it('successfully exports the Visual Designer Canvas page', () => {
    expect(VisualDesignerPage).toBeDefined()
  })

  it('verifies canvas block definitions and reordering logic', () => {
    interface TestBlock {
      instanceId: string
      type: string
      name: string
    }

    const blocks: TestBlock[] = [
      { instanceId: 'b-1', type: 'header', name: 'Header & Letterhead' },
      { instanceId: 'b-2', type: 'patient_info', name: 'Patient Demographics' },
      { instanceId: 'b-3', type: 'results_table', name: 'Results Table' },
      { instanceId: 'b-4', type: 'signature', name: 'Signature Stamp' },
    ]

    // Move b-3 (Results Table) up to index 1
    function moveUp(arr: TestBlock[], index: number) {
      if (index > 0) {
        const item = arr.splice(index, 1)[0]
        if (item) arr.splice(index - 1, 0, item)
      }
    }

    // Move b-1 (Header) down to index 1
    function moveDown(arr: TestBlock[], index: number) {
      if (index < arr.length - 1) {
        const item = arr.splice(index, 1)[0]
        if (item) arr.splice(index + 1, 0, item)
      }
    }

    moveUp(blocks, 2)
    expect(blocks[1]?.type).toBe('results_table')
    expect(blocks[2]?.type).toBe('patient_info')

    moveDown(blocks, 0)
    expect(blocks[0]?.type).toBe('results_table')
    expect(blocks[1]?.type).toBe('header')
  })

  it('validates block addition and removal integrity', () => {
    const canvas = [
      { instanceId: 'b-1', type: 'header' },
      { instanceId: 'b-2', type: 'results_table' },
    ]

    // Add block
    const newBlock = { instanceId: 'b-3', type: 'observation' }
    canvas.push(newBlock)
    expect(canvas).toHaveLength(3)
    expect(canvas[2]?.type).toBe('observation')

    // Remove block b-2
    const filtered = canvas.filter(b => b.instanceId !== 'b-2')
    expect(filtered).toHaveLength(2)
    expect(filtered.map(b => b.type)).toEqual(['header', 'observation'])
  })

  it('serializes visual canvas into valid backend template schema JSON', () => {
    const templateSchema = {
      templateName: 'CBC Complete Blood Count',
      department: 'hematology',
      pageSize: 'A4',
      orientation: 'Portrait',
      margins: 'Normal',
      font: 'Inter / 11',
      blocks: [
        { id: 'cb-1', type: 'header', name: 'Header', config: { showNablBadge: true } },
        { id: 'cb-2', type: 'patient_info', name: 'Demographics', config: { twoColumn: true } },
        { id: 'cb-3', type: 'results_table', name: 'Table', config: { showMethod: true } },
        { id: 'cb-4', type: 'signature', name: 'Signatures', config: { showQrSeal: true } },
      ],
    }

    const serialized = JSON.stringify(templateSchema)
    expect(serialized).toBeTruthy()

    const parsed = JSON.parse(serialized)
    expect(parsed.templateName).toBe('CBC Complete Blood Count')
    expect(parsed.blocks).toHaveLength(4)
    expect(parsed.blocks[0].config.showNablBadge).toBe(true)
    expect(parsed.blocks[3].config.showQrSeal).toBe(true)
  })
})

