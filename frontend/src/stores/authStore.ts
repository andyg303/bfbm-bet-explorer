import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios, { type AxiosError } from 'axios'

interface AuthUser {
  id: number
  email: string
  display_name: string
  is_admin?: boolean
  subscription_status?: string  // inactive | active | cancelled | expired
  subscription_plan?: string    // 6month | 12month
  subscription_expires?: string // ISO date
}

interface TokenPair {
  access_token: string
  refresh_token: string
  user: AuthUser
}

const STORAGE_KEY_TOKEN = 'bfbm_access_token'
const STORAGE_KEY_REFRESH = 'bfbm_refresh_token'
const STORAGE_KEY_USER = 'bfbm_user'

export const useAuthStore = defineStore('auth', () => {
  // --------------- State ---------------
  const accessToken = ref<string | null>(localStorage.getItem(STORAGE_KEY_TOKEN))
  const refreshToken = ref<string | null>(localStorage.getItem(STORAGE_KEY_REFRESH))
  const user = ref<AuthUser | null>(
    (() => {
      try {
        const raw = localStorage.getItem(STORAGE_KEY_USER)
        return raw ? JSON.parse(raw) : null
      } catch {
        return null
      }
    })(),
  )
  const loading = ref(false)
  const error = ref<string | null>(null)

  // --------------- Computed ---------------
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const displayName = computed(() => user.value?.display_name || user.value?.email || '')
  const hasActiveSubscription = computed(() => {
    if (!user.value) return false
    if (user.value.is_admin) return true
    if (user.value.subscription_status !== 'active') return false
    if (user.value.subscription_expires) {
      return new Date(user.value.subscription_expires) > new Date()
    }
    return true
  })
  const subscriptionStatus = computed(() => user.value?.subscription_status || 'inactive')

  // --------------- Helpers ---------------
  function persistTokens(data: TokenPair) {
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    user.value = data.user
    localStorage.setItem(STORAGE_KEY_TOKEN, data.access_token)
    localStorage.setItem(STORAGE_KEY_REFRESH, data.refresh_token)
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(data.user))
  }

  function clearTokens() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem(STORAGE_KEY_TOKEN)
    localStorage.removeItem(STORAGE_KEY_REFRESH)
    localStorage.removeItem(STORAGE_KEY_USER)
  }

  function extractError(e: unknown): string {
    const axErr = e as AxiosError<{ detail?: string | { msg?: string }[] }>
    if (axErr.response?.data?.detail) {
      const detail = axErr.response.data.detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail) && detail.length > 0) {
        // Pydantic validation error array
        return detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
      }
    }
    return (e as Error).message || 'An unexpected error occurred'
  }

  // --------------- Actions ---------------
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  async function register(email: string, password: string, displayName?: string) {
    loading.value = true
    error.value = null
    try {
      const res = await axios.post<TokenPair>(`${API_BASE_URL}/auth/register`, {
        email,
        password,
        display_name: displayName,
      })
      persistTokens(res.data)
    } catch (e) {
      error.value = extractError(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    error.value = null
    try {
      const res = await axios.post<TokenPair>(`${API_BASE_URL}/auth/login`, {
        email,
        password,
      })
      persistTokens(res.data)
    } catch (e) {
      error.value = extractError(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function refreshAccessToken(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const res = await axios.post<TokenPair>(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken.value,
      })
      persistTokens(res.data)
      return true
    } catch {
      clearTokens()
      return false
    }
  }

  async function forgotPassword(email: string): Promise<string> {
    loading.value = true
    error.value = null
    try {
      const res = await axios.post(`${API_BASE_URL}/auth/forgot-password`, { email })
      return res.data.message || 'Check your email for reset instructions.'
    } catch (e) {
      error.value = extractError(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function resetPassword(token: string, newPassword: string) {
    loading.value = true
    error.value = null
    try {
      await axios.post(`${API_BASE_URL}/auth/reset-password`, {
        token,
        new_password: newPassword,
      })
    } catch (e) {
      error.value = extractError(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    loading.value = true
    error.value = null
    try {
      await axios.post(
        `${API_BASE_URL}/auth/change-password`,
        { current_password: currentPassword, new_password: newPassword },
        { headers: { Authorization: `Bearer ${accessToken.value}` } },
      )
    } catch (e) {
      error.value = extractError(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function checkSubscription(): Promise<{ is_active: boolean; status: string }> {
    try {
      const res = await axios.get(`${API_BASE_URL}/stripe/subscription-status`, {
        headers: { Authorization: `Bearer ${accessToken.value}` },
      })
      // Update local user data with fresh subscription info
      if (user.value) {
        user.value = {
          ...user.value,
          subscription_status: res.data.status,
          subscription_plan: res.data.plan,
          subscription_expires: res.data.expires,
        }
        localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user.value))
      }
      return res.data
    } catch {
      return { is_active: false, status: 'unknown' }
    }
  }

  async function verifyPaymentSession(sessionId: string): Promise<boolean> {
    try {
      const res = await axios.get(`${API_BASE_URL}/stripe/verify-session/${sessionId}`, {
        headers: { Authorization: `Bearer ${accessToken.value}` },
      })
      if (res.data.activated && user.value) {
        user.value = {
          ...user.value,
          subscription_status: res.data.status || 'active',
          subscription_plan: res.data.plan,
          subscription_expires: res.data.expires,
        }
        localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user.value))
      }
      return res.data.activated
    } catch {
      return false
    }
  }

  async function refreshUserProfile() {
    try {
      const res = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${accessToken.value}` },
      })
      if (user.value) {
        user.value = {
          ...user.value,
          ...res.data,
        }
        localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user.value))
      }
    } catch {
      // Silently fail — will be caught by 401 interceptor if token expired
    }
  }

  function logout() {
    clearTokens()
  }

  return {
    accessToken,
    refreshToken,
    user,
    loading,
    error,
    isAuthenticated,
    displayName,
    hasActiveSubscription,
    subscriptionStatus,
    register,
    login,
    refreshAccessToken,
    forgotPassword,
    resetPassword,
    changePassword,
    checkSubscription,
    verifyPaymentSession,
    refreshUserProfile,
    logout,
    clearTokens,
  }
})
