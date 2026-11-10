import { ref } from 'vue'

const isDark = ref<boolean>(false)
let initialized = false

export function useTheme() {
  function initTheme() {
    if (typeof window === 'undefined') return
    const stored = localStorage.getItem('aarozi_theme')
    if (stored) {
      isDark.value = stored === 'dark'
    } else {
      isDark.value = false // Default to clean minimal Light Mode (Soft Lavender White & Powder Blue)
    }
    applyTheme()
    initialized = true
  }

  function applyTheme() {
    if (typeof document === 'undefined') return
    const root = document.documentElement
    const body = document.body
    if (isDark.value) {
      root.classList.add('dark')
      root.setAttribute('data-theme', 'dark')
      if (body) {
        body.classList.add('dark')
        body.setAttribute('data-theme', 'dark')
      }
    } else {
      root.classList.remove('dark')
      root.setAttribute('data-theme', 'light')
      if (body) {
        body.classList.remove('dark')
        body.setAttribute('data-theme', 'light')
      }
    }
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('aarozi_theme', isDark.value ? 'dark' : 'light')
    }
  }

  function toggleTheme() {
    if (!initialized) initTheme()
    isDark.value = !isDark.value
    applyTheme()
  }

  return {
    isDark,
    initTheme,
    applyTheme,
    toggleTheme,
  }
}
