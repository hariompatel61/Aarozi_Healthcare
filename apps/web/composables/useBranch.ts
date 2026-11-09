import { ref, computed, onMounted, getCurrentInstance } from 'vue'
import { useToast } from '~/composables/useToast'

export interface BranchInfo {
  id: string
  name: string
  badge: string
  code: string
  address: string
}

export const AVAILABLE_BRANCHES: BranchInfo[] = [
  {
    id: 'BR-01',
    name: 'Main City Branch',
    badge: 'Central Lab',
    code: 'HQ',
    address: 'Plot 42, Knowledge Park III, Greater Noida',
  },
  {
    id: 'BR-02',
    name: 'City Centre Branch',
    badge: 'Collection Center',
    code: 'CC',
    address: 'Shop 12, Metro Commercial Complex, Sector 18',
  },
  {
    id: 'BR-03',
    name: 'North Satellite Lab',
    badge: 'Emergency Unit',
    code: 'SAT',
    address: 'Civil Lines Road, Near Medical College',
  },
  {
    id: 'BR-ALL',
    name: 'All Branches',
    badge: 'Enterprise HQ',
    code: 'ALL',
    address: 'Consolidated Multi-Branch View',
  },
]

// Singleton reactive state shared across all components
const selectedBranchName = ref<string>('Main City Branch')

export function useBranch() {
  const { info } = useToast()

  if (typeof window !== 'undefined') {
    const initBranch = () => {
      const stored = localStorage.getItem('active_branch')
      if (stored && AVAILABLE_BRANCHES.some((b) => b.name === stored)) {
        selectedBranchName.value = stored
      }
    }
    if (getCurrentInstance()) {
      onMounted(initBranch)
    } else {
      initBranch()
    }
  }

  const DEFAULT_BRANCH: BranchInfo = AVAILABLE_BRANCHES[0]!

  const currentBranch = computed<BranchInfo>(() => {
    return (
      AVAILABLE_BRANCHES.find((b) => b.name === selectedBranchName.value) ??
      DEFAULT_BRANCH
    )
  })

  function switchBranch(branchName: string, silent: boolean = false) {
    if (selectedBranchName.value === branchName) return
    selectedBranchName.value = branchName
    if (typeof window !== 'undefined') {
      localStorage.setItem('active_branch', branchName)
    }
    if (!silent) {
      info(
        'Branch Switched',
        `Active operational context set to "${branchName}" (${currentBranch.value.badge})`
      )
    }
  }

  return {
    branches: AVAILABLE_BRANCHES,
    selectedBranch: selectedBranchName,
    currentBranch,
    switchBranch,
  }
}
