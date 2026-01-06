import { ref, watch } from 'vue'

const isDark = ref(false)

// Initialize from localStorage
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('darkMode')
  isDark.value = stored === 'true'
  
  // Apply initial class
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// Watch for changes and persist
watch(isDark, (newValue) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('darkMode', String(newValue))
    if (newValue) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }
})

export function useDarkMode() {
  const toggle = () => {
    isDark.value = !isDark.value
  }

  return {
    isDark,
    toggle
  }
}
