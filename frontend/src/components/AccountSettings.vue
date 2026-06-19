<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { useBetStore } from '../stores/betStore'
import LoadingOverlay from './LoadingOverlay.vue'
import {
  createAutomationToken,
  listAutomationTokens,
  revokeAutomationToken,
  getUploadHistory,
  type AutomationToken,
  type UploadHistoryEntry,
} from '../services/api'

const props = defineProps<{ scrollTo?: string }>()

const auth = useAuthStore()
const betStore = useBetStore()

const emit = defineEmits<{
  (e: 'navigate', page: string): void
}>()

// ─── Profile form ────────────────────────────────────────────────────────────
const displayName = ref('')
const email = ref('')
const profileSuccess = ref('')
const profileError = ref('')
const profileSaving = ref(false)
const portalLoading = ref(false)

// ─── Password form ──────────────────────────────────────────────────────────
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordSuccess = ref('')
const passwordError = ref('')
const passwordSaving = ref(false)
const showPassword = ref(false)

// ─── Commission form ─────────────────────────────────────────────────────────
const commissionRate = ref(2.0)
const commissionRateAusNz = ref(5.0)
const commissionSaving = ref(false)
const commissionRecalculating = ref(false)
const commissionSuccess = ref('')
const commissionError = ref('')
const showCommissionHelp = ref(false)

// ─── Automation uploader tokens ─────────────────────────────────────────────
const automationTokens = ref<AutomationToken[]>([])
const automationTokenName = ref('VPS uploader')
const newAutomationToken = ref('')
const automationLoading = ref(false)
const automationCreating = ref(false)
const automationError = ref('')
const automationSuccess = ref('')

// ─── Upload history ──────────────────────────────────────────────────────────
const uploadHistory = ref<UploadHistoryEntry[]>([])
const uploadHistoryLoading = ref(false)
const uploadHistoryError = ref('')
const showUploadHistory = ref(true)
const latestUpload = computed(() => uploadHistory.value[0] ?? null)

const passwordStrength = computed(() => {
  const p = newPassword.value
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

const passwordValid = computed(() =>
  currentPassword.value.length > 0 &&
  newPassword.value.length >= 8 &&
  newPassword.value === confirmPassword.value
)

const profileChanged = computed(() => {
  if (!auth.user) return false
  return (
    displayName.value.trim() !== (auth.user.display_name || '') ||
    email.value.trim().toLowerCase() !== (auth.user.email || '').toLowerCase()
  )
})

onMounted(async () => {
  await auth.refreshUserProfile()
  if (auth.user) {
    displayName.value = auth.user.display_name || ''
    email.value = auth.user.email || ''
    commissionRate.value = auth.user.commission_rate ?? 2.0
    commissionRateAusNz.value = auth.user.commission_rate_aus_nz ?? 5.0
  }
  await loadAutomationTokens()
  await loadUploadHistory()
  if (props.scrollTo) {
    await nextTick()
    const el = document.getElementById(props.scrollTo)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
})

async function handleUpdateProfile() {
  profileError.value = ''
  profileSuccess.value = ''
  profileSaving.value = true

  try {
    const updates: { display_name?: string; email?: string } = {}
    if (displayName.value.trim() !== (auth.user?.display_name || '')) {
      updates.display_name = displayName.value.trim()
    }
    if (email.value.trim().toLowerCase() !== (auth.user?.email || '').toLowerCase()) {
      updates.email = email.value.trim()
    }
    await auth.updateProfile(updates)
    profileSuccess.value = 'Profile updated successfully!'
    setTimeout(() => { profileSuccess.value = '' }, 3000)
  } catch {
    profileError.value = auth.error || 'Failed to update profile'
  } finally {
    profileSaving.value = false
  }
}

async function handleChangePassword() {
  passwordError.value = ''
  passwordSuccess.value = ''

  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = 'Passwords do not match'
    return
  }

  passwordSaving.value = true
  try {
    await auth.changePassword(currentPassword.value, newPassword.value)
    passwordSuccess.value = 'Password changed successfully!'
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    setTimeout(() => { passwordSuccess.value = '' }, 3000)
  } catch {
    passwordError.value = auth.error || 'Failed to change password'
  } finally {
    passwordSaving.value = false
  }
}

async function handleSaveCommission() {
  commissionError.value = ''
  commissionSuccess.value = ''
  commissionSaving.value = true
  try {
    await auth.updateCommissionSettings(commissionRate.value, commissionRateAusNz.value)
    commissionSuccess.value = 'Commission rates saved!'
    setTimeout(() => { commissionSuccess.value = '' }, 3000)
  } catch {
    commissionError.value = auth.error || 'Failed to save commission rates'
  } finally {
    commissionSaving.value = false
  }
}

async function handleRecalculateCommission() {
  commissionError.value = ''
  commissionSuccess.value = ''
  // Save first, then recalculate
  commissionRecalculating.value = true
  try {
    await auth.updateCommissionSettings(commissionRate.value, commissionRateAusNz.value)
    const result = await auth.recalculateCommission()
    // Reload bets so table reflects new P/L and commission_paid values
    await betStore.loadBets(0, 100, 'start_time', 'desc')
    commissionSuccess.value = `Commission recalculated for ${result.bets_processed.toLocaleString()} bets.`
    setTimeout(() => { commissionSuccess.value = '' }, 5000)
  } catch {
    commissionError.value = auth.error || 'Recalculation failed'
  } finally {
    commissionRecalculating.value = false
  }
}

async function loadAutomationTokens() {
  automationLoading.value = true
  automationError.value = ''
  try {
    automationTokens.value = await listAutomationTokens()
  } catch {
    automationError.value = 'Failed to load upload tokens'
  } finally {
    automationLoading.value = false
  }
}

async function loadUploadHistory() {
  uploadHistoryLoading.value = true
  uploadHistoryError.value = ''
  try {
    uploadHistory.value = await getUploadHistory(20)
  } catch {
    uploadHistoryError.value = 'Failed to load upload history'
  } finally {
    uploadHistoryLoading.value = false
  }
}

async function handleCreateAutomationToken() {
  automationCreating.value = true
  automationError.value = ''
  automationSuccess.value = ''
  newAutomationToken.value = ''
  try {
    const res = await createAutomationToken(automationTokenName.value)
    newAutomationToken.value = res.token
    automationTokens.value = [res.token_record, ...automationTokens.value]
    automationSuccess.value = 'Upload token created.'
  } catch {
    automationError.value = 'Failed to create upload token'
  } finally {
    automationCreating.value = false
  }
}

async function handleRevokeAutomationToken(id: number) {
  automationError.value = ''
  automationSuccess.value = ''
  try {
    await revokeAutomationToken(id)
    automationTokens.value = automationTokens.value.filter((token) => token.id !== id)
    automationSuccess.value = 'Upload token revoked.'
  } catch {
    automationError.value = 'Failed to revoke upload token'
  }
}

async function copyAutomationToken() {
  if (!newAutomationToken.value) return
  try {
    await navigator.clipboard.writeText(newAutomationToken.value)
    automationSuccess.value = 'Token copied.'
  } catch {
    automationError.value = 'Could not copy token automatically'
  }
}

function formatDate(dateStr?: string | null) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

async function handleManageSubscription() {
  portalLoading.value = true
  try {
    const url = await auth.openCustomerPortal()
    if (url) {
      window.location.href = url
    } else {
      profileError.value = 'Could not open subscription management. Please try again.'
    }
  } finally {
    portalLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-[#0b0f1a] px-4 py-8 relative overflow-hidden">
    <!-- Background gradient mesh -->
    <div class="absolute inset-0 -z-10">
      <div class="absolute top-[20%] left-[10%] w-[500px] h-[500px] rounded-full opacity-10 blur-[120px]" style="background: radial-gradient(circle, #14b8a6, transparent 70%);"></div>
      <div class="absolute bottom-[10%] right-[10%] w-[400px] h-[400px] rounded-full opacity-10 blur-[120px]" style="background: radial-gradient(circle, #0ea5e9, transparent 70%);"></div>
    </div>

    <div class="max-w-3xl mx-auto space-y-6 animate-fade-in-up">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">Account Settings</h1>
          <p class="text-sm text-gray-500 mt-1">Manage your profile, email, and password</p>
        </div>
        <button @click="$emit('navigate', 'dashboard')" class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 bg-gray-100 dark:bg-gray-800/50 hover:bg-gray-200 dark:hover:bg-gray-800 rounded-xl transition-colors">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          Back to Dashboard
        </button>
      </div>

      <!-- ═══════ Profile Section ═══════ -->
      <div class="glass-card overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800/40">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <svg class="w-5 h-5 text-teal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
            Profile
          </h2>
        </div>
        <form @submit.prevent="handleUpdateProfile" class="p-6 space-y-4">
          <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
            <div v-if="profileSuccess" class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-400">{{ profileSuccess }}</div>
          </Transition>
          <div v-if="profileError" class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">{{ profileError }}</div>

          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Display Name</label>
            <input v-model="displayName" type="text" class="input-field" placeholder="Your name" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Email Address</label>
            <input v-model="email" type="email" class="input-field" placeholder="you@example.com" />
          </div>

          <div class="pt-2">
            <button
              type="submit"
              :disabled="!profileChanged || profileSaving"
              class="btn-glow !py-2.5 text-sm disabled:opacity-40 disabled:cursor-not-allowed disabled:!transform-none"
            >
              <span v-if="profileSaving" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
                Saving…
              </span>
              <span v-else>Save Changes</span>
            </button>
          </div>
        </form>
      </div>

      <!-- ═══════ Change Password Section ═══════ -->
      <div class="glass-card overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800/40">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <svg class="w-5 h-5 text-teal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
            Change Password
          </h2>
        </div>
        <form @submit.prevent="handleChangePassword" class="p-6 space-y-4">
          <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
            <div v-if="passwordSuccess" class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-400">{{ passwordSuccess }}</div>
          </Transition>
          <div v-if="passwordError" class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">{{ passwordError }}</div>

          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Current Password</label>
            <input v-model="currentPassword" type="password" required class="input-field" placeholder="Enter current password" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">New Password</label>
            <div class="relative">
              <input v-model="newPassword" :type="showPassword ? 'text' : 'password'" required minlength="8" class="input-field !pr-10" placeholder="Enter new password" />
              <button type="button" @click="showPassword = !showPassword" class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
                <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></svg>
              </button>
            </div>
            <div v-if="newPassword.length > 0" class="mt-2">
              <div class="flex gap-1 mb-1">
                <div v-for="i in 5" :key="i" class="h-1 flex-1 rounded-full transition-colors" :class="i <= passwordStrength.score ? passwordStrength.color : 'bg-gray-200 dark:bg-gray-800'" />
              </div>
              <p class="text-xs" :class="{ 'text-rose-400': passwordStrength.score <= 2, 'text-amber-400': passwordStrength.score === 3, 'text-sky-400': passwordStrength.score === 4, 'text-emerald-400': passwordStrength.score === 5 }">
                {{ passwordStrength.label }} <span class="text-gray-600">— Min 8 chars, upper, lower & number required</span>
              </p>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Confirm New Password</label>
            <input v-model="confirmPassword" :type="showPassword ? 'text' : 'password'" required class="input-field" placeholder="Confirm new password" />
            <p v-if="confirmPassword && confirmPassword !== newPassword" class="mt-1 text-xs text-rose-400">Passwords do not match</p>
          </div>

          <div class="pt-2">
            <button
              type="submit"
              :disabled="!passwordValid || passwordSaving"
              class="btn-glow !py-2.5 text-sm disabled:opacity-40 disabled:cursor-not-allowed disabled:!transform-none"
            >
              <span v-if="passwordSaving" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
                Updating…
              </span>
              <span v-else>Update Password</span>
            </button>
          </div>
        </form>
      </div>

      <!-- ═══════ Commission Settings ═══════ -->
      <div class="glass-card overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800/40">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <svg class="w-5 h-5 text-teal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" /></svg>
            Commission Settings
          </h2>
        </div>
        <div class="p-6 space-y-4">
          <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
            <div v-if="commissionSuccess" class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-400">{{ commissionSuccess }}</div>
          </Transition>
          <div v-if="commissionError" class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">{{ commissionError }}</div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Global Commission Rate (%)</label>
              <input v-model.number="commissionRate" type="number" min="0" max="100" step="0.1" class="input-field" placeholder="e.g. 2" />
              <p class="mt-1 text-xs text-gray-500">Applied to all non-AUS/NZ markets (Betfair default: 2%)</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">AUS / NZ Commission Rate (%)</label>
              <input v-model.number="commissionRateAusNz" type="number" min="0" max="100" step="0.1" class="input-field" placeholder="e.g. 5" />
              <p class="mt-1 text-xs text-gray-500">Applied when (AUS) or (NZL) is detected in the market name</p>
            </div>
          </div>

          <!-- Expandable help section -->
          <div class="border border-gray-200 dark:border-gray-700/50 rounded-xl overflow-hidden">
            <button
              @click="showCommissionHelp = !showCommissionHelp"
              class="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white bg-gray-50 dark:bg-gray-800/30 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors"
            >
              <span class="flex items-center gap-2">
                <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                How commission calculation works
              </span>
              <svg class="w-4 h-4 transition-transform" :class="showCommissionHelp ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
            </button>
            <div v-if="showCommissionHelp" class="px-4 py-4 space-y-3 text-xs text-gray-500 dark:text-gray-400 bg-gray-50/50 dark:bg-gray-800/10 border-t border-gray-200 dark:border-gray-700/50">
              <p><strong class="text-gray-700 dark:text-gray-300">Why commission isn't in the raw export:</strong> BFBM's bet history screen shows individual bets, but Betfair deducts commission from the overall market profit. Because a market can have multiple bets (e.g. hedge strategies), the export cannot correctly split commission per bet — so it omits it.</p>
              <p><strong class="text-gray-700 dark:text-gray-300">How this tool applies commission:</strong> Bets from the same market and same strategy are grouped together. The net P/L for the group is calculated. If it is positive, commission is applied to that net profit and deducted from the <em>first positively-settled bet</em> in the group. All other bets carry zero commission. If the group has a net loss, no commission is charged (Betfair doesn't charge commission on losing markets). For single bet back/lay strategies commission will always be calculated on bets with a positive return.</p>
              <p><strong class="text-gray-700 dark:text-gray-300">Hedge strategies:</strong> If your bot places both BACK and LAY bets on the same market (hedge bets), they are grouped correctly — commission is only applied if the combined result is profitable, preventing over-deduction.</p>
              <p><strong class="text-gray-700 dark:text-gray-300">AUS / NZ detection:</strong> A market is treated as AUS/NZ if <code class="font-mono bg-gray-200 dark:bg-gray-700 px-1 rounded">(AUS)</code> or <code class="font-mono bg-gray-200 dark:bg-gray-700 px-1 rounded">(NZL)</code> appears in the market name. If you include the <strong>Competition</strong> column in your data export, markets with "Australia" or "New Zealand" in the competition name are also detected. Note: some football and rugby matches may not be detected without the Competition column.</p>
              <p><strong class="text-gray-700 dark:text-gray-300">The P/L column</strong> in the Bets table always shows the commission-adjusted figure. The separate <strong>Commission Paid</strong> column shows how much commission was attributed to each bet.</p>
              <p><strong class="text-gray-700 dark:text-gray-300">Recalculate All Bets</strong> saves your new rates and re-runs commission across all your bets. Use this whenever you change your rates.</p>
            </div>
          </div>

          <div class="flex flex-wrap gap-3 pt-1">
            <button
              @click="handleSaveCommission"
              :disabled="commissionSaving || commissionRecalculating"
              class="btn-glow !py-2.5 text-sm disabled:opacity-40 disabled:cursor-not-allowed disabled:!transform-none"
            >
              <span v-if="commissionSaving" class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
                Saving…
              </span>
              <span v-else>Save Rates</span>
            </button>
            <button
              @click="handleRecalculateCommission"
              :disabled="commissionSaving || commissionRecalculating"
              class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <span class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                Recalculate All Bets
              </span>
            </button>

            <LoadingOverlay
              :show="commissionRecalculating"
              title="Recalculating commission…"
              message="Please do not close or refresh this page. This may take a few minutes for large bet histories."
            />
          </div>
        </div>
      </div>

      <!-- ═══════ Automation Uploads ═══════ -->
      <div id="section-automation" class="glass-card overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800/40">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <svg class="w-5 h-5 text-teal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            Automation Uploads
          </h2>
        </div>
        <div class="p-6 space-y-4">
          <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
            <div v-if="automationSuccess" class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-400">{{ automationSuccess }}</div>
          </Transition>
          <div v-if="automationError" class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">{{ automationError }}</div>

          <div class="flex flex-col sm:flex-row gap-3">
            <div class="flex-1">
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Token Name</label>
              <input v-model="automationTokenName" type="text" maxlength="100" class="input-field" placeholder="VPS uploader" />
            </div>
            <div class="flex items-end">
              <button
                @click="handleCreateAutomationToken"
                :disabled="automationCreating"
                class="btn-glow !py-2.5 text-sm w-full sm:w-auto disabled:opacity-40 disabled:cursor-not-allowed disabled:!transform-none"
              >
                <span v-if="automationCreating" class="flex items-center gap-2">
                  <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                  Creating…
                </span>
                <span v-else>Create Token</span>
              </button>
            </div>
          </div>

          <div v-if="newAutomationToken" class="rounded-xl border border-teal-500/20 bg-teal-500/10 p-3">
            <p class="mb-2 text-xs font-medium text-teal-300">New token</p>
            <div class="flex flex-col sm:flex-row gap-2">
              <input :value="newAutomationToken" readonly class="input-field font-mono text-xs min-w-0" />
              <button @click="copyAutomationToken" class="px-3 py-2 rounded-lg bg-teal-500/20 text-teal-300 text-sm font-medium hover:bg-teal-500/30 transition-colors">
                Copy
              </button>
            </div>
          </div>

          <div class="border border-gray-200 dark:border-gray-700/50 rounded-xl overflow-hidden">
            <div class="px-4 py-3 bg-gray-50 dark:bg-gray-800/30 flex items-center justify-between">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Active Tokens</p>
              <button @click="loadAutomationTokens" :disabled="automationLoading" class="text-xs font-medium text-teal-400 hover:text-teal-300 disabled:opacity-40">
                Refresh
              </button>
            </div>
            <div v-if="automationLoading" class="px-4 py-4 text-sm text-gray-500">Loading…</div>
            <div v-else-if="automationTokens.length === 0" class="px-4 py-4 text-sm text-gray-500">No active upload tokens.</div>
            <div v-else class="divide-y divide-gray-100 dark:divide-gray-800/50">
              <div v-for="token in automationTokens" :key="token.id" class="px-4 py-3 flex items-center justify-between gap-4">
                <div class="min-w-0">
                  <p class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{{ token.name }}</p>
                  <p class="text-xs text-gray-500 font-mono">{{ token.token_prefix }}</p>
                  <p class="text-xs text-gray-500 mt-0.5">
                    Created {{ formatDate(token.created_at) }} · Last used {{ formatDate(token.last_used_at) }}
                  </p>
                </div>
                <button
                  @click="handleRevokeAutomationToken(token.id)"
                  class="shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium text-rose-400 bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 transition-colors"
                >
                  Revoke
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══════ Upload History ═══════ -->
      <div id="section-upload-history" class="glass-card overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800/40">
          <button @click="showUploadHistory = !showUploadHistory" class="w-full flex items-center justify-between">
            <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <svg class="w-5 h-5 text-teal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
              Upload History
              <span v-if="uploadHistory.length" class="ml-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-500">{{ uploadHistory.length }}</span>
            </h2>
            <div class="flex items-center gap-3">
              <button @click.stop="loadUploadHistory" :disabled="uploadHistoryLoading" class="text-xs font-medium text-teal-400 hover:text-teal-300 disabled:opacity-40">Refresh</button>
              <svg class="w-4 h-4 text-gray-400 transition-transform" :class="showUploadHistory ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
            </div>
          </button>
        </div>

        <div v-if="showUploadHistory" class="p-6">
          <div v-if="uploadHistoryError" class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400 mb-4">{{ uploadHistoryError }}</div>
          <div v-if="uploadHistoryLoading" class="text-center py-6">
            <svg class="animate-spin h-5 w-5 mx-auto text-teal-400" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          </div>
          <div v-else-if="uploadHistory.length === 0" class="text-sm text-gray-500 text-center py-4">No uploads recorded yet.</div>
          <div v-else class="space-y-3">

            <!-- Last upload summary banner -->
            <div v-if="latestUpload" class="flex flex-wrap items-center gap-x-4 gap-y-1 p-3 rounded-xl border text-sm"
              :class="{
                'bg-emerald-500/5 border-emerald-500/20': latestUpload.status === 'success',
                'bg-amber-500/5 border-amber-500/20': latestUpload.status === 'partial',
                'bg-rose-500/5 border-rose-500/20': latestUpload.status === 'error',
                'bg-sky-500/5 border-sky-500/20': latestUpload.status === 'processing',
              }"
            >
              <span class="font-semibold" :class="{
                'text-emerald-400': latestUpload.status === 'success',
                'text-amber-400': latestUpload.status === 'partial',
                'text-rose-400': latestUpload.status === 'error',
                'text-sky-400': latestUpload.status === 'processing',
              }">Last upload:</span>
              <span class="text-gray-700 dark:text-gray-300">
                {{ latestUpload.created_at ? new Date(latestUpload.created_at).toLocaleString('en-GB') : '—' }}
              </span>
              <span v-if="latestUpload.status !== 'error'" class="text-gray-500">
                {{ latestUpload.rows_total.toLocaleString() }} total ·
                +{{ latestUpload.inserted.toLocaleString() }} new ·
                {{ latestUpload.updated.toLocaleString() }} updated ·
                {{ latestUpload.skipped.toLocaleString() }} skipped
              </span>
              <span v-if="latestUpload.status === 'error'" class="text-rose-400 truncate max-w-xs" :title="latestUpload.error || ''">
                {{ latestUpload.error || 'Error' }}
              </span>
              <span v-if="latestUpload.warnings_count" class="text-amber-400">
                · {{ latestUpload.warnings_count }} warning{{ latestUpload.warnings_count !== 1 ? 's' : '' }}
              </span>
            </div>

            <!-- Full log table -->
            <div class="border border-gray-200 dark:border-gray-700/50 rounded-xl overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="bg-gray-50 dark:bg-gray-800/40 text-gray-500 uppercase tracking-wider">
                    <th class="px-3 py-2 text-left font-medium">Date &amp; Time</th>
                    <th class="px-3 py-2 text-left font-medium">File</th>
                    <th class="px-3 py-2 text-center font-medium">Status</th>
                    <th class="px-3 py-2 text-right font-medium">Total</th>
                    <th class="px-3 py-2 text-right font-medium">New</th>
                    <th class="px-3 py-2 text-right font-medium">Updated</th>
                    <th class="px-3 py-2 text-right font-medium">Skipped</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-gray-800/50">
                  <tr v-for="entry in uploadHistory" :key="entry.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/20 transition-colors">
                    <td class="px-3 py-2 whitespace-nowrap text-gray-600 dark:text-gray-400">
                      {{ entry.created_at ? new Date(entry.created_at).toLocaleString('en-GB') : '—' }}
                    </td>
                    <td class="px-3 py-2 max-w-[160px] truncate text-gray-700 dark:text-gray-300" :title="entry.filename">{{ entry.filename }}</td>
                    <td class="px-3 py-2 text-center">
                      <span
                        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium"
                        :class="{
                          'bg-emerald-500/10 text-emerald-400': entry.status === 'success',
                          'bg-amber-500/10 text-amber-400': entry.status === 'partial',
                          'bg-rose-500/10 text-rose-400': entry.status === 'error',
                          'bg-sky-500/10 text-sky-400': entry.status === 'processing',
                        }"
                        :title="entry.status === 'error' ? (entry.error || 'Error') : entry.status === 'partial' ? entry.warnings_count + ' warning(s)' : ''"
                      >
                        <svg v-if="entry.status === 'success'" class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
                        <svg v-else-if="entry.status === 'error'" class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
                        <svg v-else-if="entry.status === 'processing'" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                        <svg v-else class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
                        {{ entry.status }}
                      </span>
                    </td>
                    <td class="px-3 py-2 text-right font-mono text-gray-500">{{ entry.rows_total.toLocaleString() }}</td>
                    <td class="px-3 py-2 text-right font-mono text-gray-700 dark:text-gray-300">{{ entry.inserted.toLocaleString() }}</td>
                    <td class="px-3 py-2 text-right font-mono text-gray-700 dark:text-gray-300">{{ entry.updated.toLocaleString() }}</td>
                    <td class="px-3 py-2 text-right font-mono text-gray-700 dark:text-gray-300">{{ entry.skipped.toLocaleString() }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══════ Subscription Info ═══════ -->
      <div class="glass-card overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800/40">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <svg class="w-5 h-5 text-teal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
            Subscription
          </h2>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Status</p>
              <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold" :class="auth.hasActiveSubscription ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'">
                {{ auth.hasActiveSubscription ? '● Active' : '○ Inactive' }}
              </span>
            </div>
            <div>
              <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Plan</p>
              <p class="text-sm font-medium text-gray-800 dark:text-gray-200">
                {{ auth.user?.subscription_plan === '12month' ? '12 Month' : auth.user?.subscription_plan === '6month' ? '6 Month' : 'None' }}
              </p>
            </div>
            <div>
              <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Expires</p>
              <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ formatDate(auth.user?.subscription_expires) }}</p>
            </div>
            <div>
              <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Member Since</p>
              <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ formatDate((auth.user as any)?.created_at) }}</p>
            </div>
          </div>

          <div class="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800/40 flex flex-wrap gap-3">
            <button v-if="auth.hasActiveSubscription" @click="handleManageSubscription" :disabled="portalLoading" class="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium bg-teal-500/10 text-teal-400 border border-teal-500/20 hover:bg-teal-500/20 transition-colors disabled:opacity-50">
              <svg v-if="!portalLoading" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
              <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              {{ portalLoading ? 'Opening…' : 'Manage Subscription' }}
            </button>
            <button v-else @click="$emit('navigate', 'pricing')" class="btn-glow !py-2.5 text-sm">
              View Plans & Subscribe
            </button>
          </div>
        </div>
      </div>

      <!-- ═══════ Danger Zone ═══════ -->
      <div class="glass-card overflow-hidden border border-rose-500/10">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800/40">
          <h2 class="text-base font-semibold text-rose-400 flex items-center gap-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
            Sign Out
          </h2>
        </div>
        <div class="p-6">
          <p class="text-sm text-gray-500 mb-4">Sign out of your account on this device. Your data will be preserved.</p>
          <button @click="auth.logout(); $emit('navigate', 'landing')" class="px-4 py-2.5 rounded-xl text-sm font-medium text-rose-400 bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 transition-colors">
            Sign Out
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
