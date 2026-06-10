<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '../stores/authStore'

const auth = useAuthStore()

const props = defineProps<{
  initialMode?: 'login' | 'register' | 'forgot' | 'reset'
  initialToken?: string
}>()

const emit = defineEmits<{
  (e: 'navigate', page: 'landing' | 'pricing' | 'login' | 'register' | 'forgot-password' | 'reset-password'): void
}>()

type AuthMode = 'login' | 'register' | 'forgot' | 'reset'
const mode = ref<AuthMode>(props.initialMode || 'login')

// Watch for external mode changes
watch(() => props.initialMode, (newMode) => {
  if (newMode) {
    clearForm()
    mode.value = newMode
  }
})

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const displayName = ref('')
const referralCode = ref('')
const resetToken = ref('')
const newPassword = ref('')
const showPassword = ref(false)
const successMessage = ref('')
const localError = ref('')

// Auto-populate token from URL or prop
onMounted(() => {
  if (props.initialToken) {
    resetToken.value = props.initialToken
  }
  // Also check URL params as fallback
  const params = new URLSearchParams(window.location.search)
  const urlToken = params.get('token')
  const urlReferral = params.get('ref')
  if (urlToken && !resetToken.value) {
    resetToken.value = urlToken
  }
  if (urlReferral) {
    referralCode.value = urlReferral.toUpperCase()
  }
})

const isValid = computed(() => {
  if (mode.value === 'login') return email.value.length > 0 && password.value.length >= 8
  if (mode.value === 'register')
    return (
      email.value.length > 0 &&
      password.value.length >= 8 &&
      password.value === confirmPassword.value
    )
  if (mode.value === 'forgot') return email.value.length > 0
  if (mode.value === 'reset') return resetToken.value.length > 0 && newPassword.value.length >= 8
  return false
})

const passwordStrength = computed(() => {
  const p = mode.value === 'reset' ? newPassword.value : password.value
  if (p.length === 0) return { score: 0, label: '', color: '' }
  let score = 0
  if (p.length >= 8) score++
  if (/[A-Z]/.test(p)) score++
  if (/[a-z]/.test(p)) score++
  if (/\d/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  if (score <= 2) return { score, label: 'Weak', color: 'bg-red-500' }
  if (score <= 3) return { score, label: 'Fair', color: 'bg-yellow-500' }
  if (score <= 4) return { score, label: 'Good', color: 'bg-blue-500' }
  return { score, label: 'Strong', color: 'bg-green-500' }
})

function clearForm() {
  email.value = ''
  password.value = ''
  confirmPassword.value = ''
  displayName.value = ''
  referralCode.value = new URLSearchParams(window.location.search).get('ref')?.toUpperCase() || referralCode.value
  resetToken.value = ''
  newPassword.value = ''
  successMessage.value = ''
  localError.value = ''
  auth.error = null
}

function switchMode(m: AuthMode) {
  clearForm()
  mode.value = m
  // Emit navigate so the URL updates
  if (m === 'login' || m === 'register') {
    emit('navigate', m)
  } else if (m === 'forgot') {
    emit('navigate', 'forgot-password')
  } else if (m === 'reset') {
    emit('navigate', 'reset-password')
  }
}

const displayError = computed(() => localError.value || auth.error)

async function handleSubmit() {
  localError.value = ''
  successMessage.value = ''
  auth.error = null

  try {
    if (mode.value === 'login') {
      await auth.login(email.value, password.value)
    } else if (mode.value === 'register') {
      if (password.value !== confirmPassword.value) {
        localError.value = 'Passwords do not match'
        return
      }
      await auth.register(email.value, password.value, displayName.value || undefined, referralCode.value || undefined)
    } else if (mode.value === 'forgot') {
      const msg = await auth.forgotPassword(email.value)
      successMessage.value = msg
    } else if (mode.value === 'reset') {
      await auth.resetPassword(resetToken.value, newPassword.value)
      successMessage.value = 'Password reset successfully! You can now log in.'
      setTimeout(() => switchMode('login'), 2000)
    }
  } catch {
    // Error is already captured in auth.error or localError
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-[#0b0f1a] px-4 relative overflow-hidden">
    <!-- Background gradient mesh -->
    <div class="absolute inset-0 -z-10">
      <div class="absolute top-[20%] left-[10%] w-[500px] h-[500px] rounded-full opacity-10 blur-[120px]" style="background: radial-gradient(circle, #14b8a6, transparent 70%);"></div>
      <div class="absolute bottom-[10%] right-[10%] w-[400px] h-[400px] rounded-full opacity-10 blur-[120px]" style="background: radial-gradient(circle, #0ea5e9, transparent 70%);"></div>
      <div class="absolute inset-0 opacity-[0.02]" style="background-image: linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 64px 64px;"></div>
    </div>

    <div class="w-full max-w-md animate-fade-in-up">
      <!-- Logo / Header -->
      <div class="text-center mb-8">
        <div
          class="mx-auto w-14 h-14 rounded-2xl flex items-center justify-center shadow-glow-teal mb-4"
          style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);"
        >
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">BFBM<span class="text-teal-600 dark:text-teal-400">Explorer</span></h1>
        <p class="text-sm text-gray-500 mt-1">Betting Analytics Dashboard</p>
      </div>

      <!-- Card -->
      <div class="glass-card p-8">
        <!-- Tab title -->
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-1">
          {{ mode === 'login' ? 'Welcome back' : mode === 'register' ? 'Create account' : mode === 'forgot' ? 'Reset password' : 'Set new password' }}
        </h2>
        <p class="text-sm text-gray-500 mb-6">
          {{ mode === 'login' ? 'Sign in to your account' : mode === 'register' ? 'Enter your details to get started' : mode === 'forgot' ? "Enter your email and we'll send you a reset link" : 'Enter your reset token and new password' }}
        </p>

        <!-- Success -->
        <div v-if="successMessage" class="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
          {{ successMessage }}
        </div>

        <!-- Error -->
        <div v-if="displayError" class="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {{ displayError }}
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- Display name (register only) -->
          <div v-if="mode === 'register'">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Display Name <span class="text-gray-400 dark:text-gray-600">(optional)</span></label>
            <input v-model="displayName" type="text" autocomplete="name" class="input-field" placeholder="Your name" />
          </div>

          <div v-if="mode === 'register'">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Referral Code <span class="text-gray-400 dark:text-gray-600">(optional)</span></label>
            <input v-model.trim="referralCode" type="text" autocomplete="off" class="input-field font-mono uppercase" placeholder="ABC12345" />
          </div>

          <!-- Email -->
          <div v-if="mode !== 'reset'">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Email</label>
            <input v-model="email" type="email" required autocomplete="email" class="input-field" placeholder="you@example.com" />
          </div>

          <!-- Password -->
          <div v-if="mode === 'login' || mode === 'register'">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Password</label>
            <div class="relative">
              <input v-model="password" :type="showPassword ? 'text' : 'password'" required autocomplete="current-password" class="input-field !pr-10" placeholder="••••••••" />
              <button type="button" @click="showPassword = !showPassword" class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
                <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></svg>
              </button>
            </div>
            <!-- Password strength -->
            <div v-if="mode === 'register' && password.length > 0" class="mt-2">
              <div class="flex gap-1 mb-1">
                <div v-for="i in 5" :key="i" class="h-1 flex-1 rounded-full transition-colors" :class="i <= passwordStrength.score ? passwordStrength.color : 'bg-gray-200 dark:bg-gray-800'" />
              </div>
              <p class="text-xs" :class="{ 'text-rose-400': passwordStrength.score <= 2, 'text-amber-400': passwordStrength.score === 3, 'text-sky-400': passwordStrength.score === 4, 'text-emerald-400': passwordStrength.score === 5 }">
                {{ passwordStrength.label }} <span class="text-gray-600">— Min 8 chars, upper, lower & number required</span>
              </p>
            </div>
          </div>

          <!-- Confirm password -->
          <div v-if="mode === 'register'">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Confirm Password</label>
            <input v-model="confirmPassword" :type="showPassword ? 'text' : 'password'" required autocomplete="new-password" class="input-field" placeholder="••••••••" />
            <p v-if="confirmPassword && confirmPassword !== password" class="mt-1 text-xs text-rose-400">Passwords do not match</p>
          </div>

          <!-- Reset token -->
          <div v-if="mode === 'reset'">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Reset Token</label>
            <input v-model="resetToken" type="text" required class="input-field font-mono text-sm" placeholder="Paste your reset token here" />
          </div>

          <!-- New password (reset) -->
          <div v-if="mode === 'reset'">
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">New Password</label>
            <input v-model="newPassword" :type="showPassword ? 'text' : 'password'" required class="input-field" placeholder="••••••••" />
            <div v-if="newPassword.length > 0" class="mt-2">
              <div class="flex gap-1 mb-1">
                <div v-for="i in 5" :key="i" class="h-1 flex-1 rounded-full transition-colors" :class="i <= passwordStrength.score ? passwordStrength.color : 'bg-gray-200 dark:bg-gray-800'" />
              </div>
              <p class="text-xs" :class="{ 'text-rose-400': passwordStrength.score <= 2, 'text-amber-400': passwordStrength.score === 3, 'text-sky-400': passwordStrength.score === 4, 'text-emerald-400': passwordStrength.score === 5 }">{{ passwordStrength.label }}</p>
            </div>
          </div>

          <!-- Forgot link -->
          <div v-if="mode === 'login'" class="flex justify-end">
            <button type="button" @click="switchMode('forgot')" class="text-sm text-teal-400 hover:text-teal-300">Forgot password?</button>
          </div>

          <!-- Submit -->
          <button type="submit" :disabled="!isValid || auth.loading" class="w-full btn-glow !py-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:!transform-none">
            <span v-if="auth.loading" class="flex items-center justify-center gap-2">
              <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
              Processing…
            </span>
            <span v-else>{{ mode === 'login' ? 'Sign In' : mode === 'register' ? 'Create Account' : mode === 'forgot' ? 'Send Reset Link' : 'Reset Password' }}</span>
          </button>
        </form>

        <!-- Mode toggle links -->
        <div class="mt-6 text-center text-sm text-gray-500 space-y-2">
          <div v-if="mode === 'login'">Don't have an account? <button @click="switchMode('register')" class="text-teal-400 font-medium hover:text-teal-300">Sign up</button></div>
          <div v-if="mode === 'register'">Already have an account? <button @click="switchMode('login')" class="text-teal-400 font-medium hover:text-teal-300">Sign in</button></div>
          <div v-if="mode === 'register'" class="text-xs text-gray-600">
            After creating your account, you'll need an <button @click="$emit('navigate', 'pricing')" class="text-teal-400 font-medium hover:text-teal-300">active subscription</button> to access the dashboard.
          </div>
          <div v-if="mode === 'forgot'">
            <button @click="switchMode('login')" class="text-teal-400 font-medium hover:text-teal-300">← Back to sign in</button>
            <span class="mx-2 text-gray-700">|</span>
            <button @click="switchMode('reset')" class="text-teal-400 font-medium hover:text-teal-300">I have a reset token</button>
          </div>
          <div v-if="mode === 'reset'"><button @click="switchMode('login')" class="text-teal-400 font-medium hover:text-teal-300">← Back to sign in</button></div>
        </div>
      </div>

      <!-- Back to homepage -->
      <div class="text-center mt-4">
        <button @click="$emit('navigate', 'landing')" class="text-sm text-gray-400 dark:text-gray-600 hover:text-gray-600 dark:hover:text-gray-400 transition-colors">← Back to homepage</button>
      </div>

      <p class="text-center text-xs text-gray-400 dark:text-gray-700 mt-6">Your data is encrypted and stored securely.</p>
    </div>
  </div>
</template>
