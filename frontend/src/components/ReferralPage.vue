<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getMyReferrals } from '../services/api'
import { useDarkMode } from '../composables/useDarkMode'

const emit = defineEmits<{ (e: 'navigate', page: string): void }>()
const { isDark, toggle: toggleDark } = useDarkMode()

const loading = ref(true)
const error = ref('')
const copied = ref(false)
const data = ref<any>(null)

const paidReferrals = computed(() => data.value?.referrals?.filter((r: any) => r.reward_earned).length || 0)
const pendingReferrals = computed(() => Math.max((data.value?.referrals?.length || 0) - paidReferrals.value, 0))

async function loadReferrals() {
  loading.value = true
  error.value = ''
  try {
    data.value = await getMyReferrals()
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to load referrals'
  } finally {
    loading.value = false
  }
}

async function copyLink() {
  if (!data.value?.referral_url) return
  await navigator.clipboard.writeText(data.value.referral_url)
  copied.value = true
  setTimeout(() => (copied.value = false), 1600)
}

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function statusClass(status: string) {
  return {
    'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': status === 'active',
    'bg-gray-500/10 text-gray-400 border border-gray-500/20': status === 'inactive',
    'bg-amber-500/10 text-amber-400 border border-amber-500/20': status === 'cancelled',
    'bg-rose-500/10 text-rose-400 border border-rose-500/20': status === 'expired',
  }
}

onMounted(loadReferrals)
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-[#0b0f1a] text-gray-800 dark:text-gray-200 transition-colors duration-200">
    <nav class="sticky top-0 z-50 bg-white/80 dark:bg-[#0b0f1a]/80 backdrop-blur-2xl border-b border-gray-200 dark:border-gray-800/40">
      <div class="max-w-6xl mx-auto px-4 sm:px-6">
        <div class="flex h-16 items-center justify-between">
          <button @click="$emit('navigate', 'dashboard')" class="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center shadow-glow-teal" style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
            </div>
            <span class="text-lg font-bold text-gray-900 dark:text-white tracking-tight">BFBM<span class="text-teal-600 dark:text-teal-400">Explorer</span></span>
          </button>
          <div class="flex items-center gap-2">
            <button @click="toggleDark" class="p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">
              <svg v-if="isDark" class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
            </button>
            <button @click="$emit('navigate', 'dashboard')" class="px-4 py-2 text-sm font-medium rounded-lg border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">Dashboard</button>
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
      <div v-if="loading" class="glass-card p-8 text-center text-gray-500">Loading referrals...</div>
      <div v-else-if="error" class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">{{ error }}</div>
      <div v-else-if="data" class="space-y-6">
        <section class="rounded-2xl overflow-hidden border border-teal-500/20 bg-white dark:bg-gray-900/40">
          <div class="p-6 sm:p-8 bg-gradient-to-r from-teal-500/10 via-sky-500/10 to-emerald-500/10">
            <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
              <div>
                <p class="text-sm font-semibold text-teal-500 dark:text-teal-400 uppercase tracking-wider">Referral Offer</p>
                <h1 class="mt-2 text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">Earn £{{ data.credit_value_gbp }} off your next purchase</h1>
                <p class="mt-3 text-gray-500 dark:text-gray-400 max-w-2xl">Your credit is awarded when a referred signup completes their first paid subscription.</p>
              </div>
              <div class="grid grid-cols-3 gap-3 min-w-full sm:min-w-[420px]">
                <div class="rounded-xl bg-white/80 dark:bg-[#0b0f1a]/60 border border-gray-200 dark:border-gray-800 p-4">
                  <p class="text-xs text-gray-500 uppercase tracking-wider">Credits</p>
                  <p class="mt-1 text-2xl font-bold text-emerald-500">{{ data.credit_balance }}</p>
                </div>
                <div class="rounded-xl bg-white/80 dark:bg-[#0b0f1a]/60 border border-gray-200 dark:border-gray-800 p-4">
                  <p class="text-xs text-gray-500 uppercase tracking-wider">Paid</p>
                  <p class="mt-1 text-2xl font-bold text-gray-900 dark:text-white">{{ paidReferrals }}</p>
                </div>
                <div class="rounded-xl bg-white/80 dark:bg-[#0b0f1a]/60 border border-gray-200 dark:border-gray-800 p-4">
                  <p class="text-xs text-gray-500 uppercase tracking-wider">Pending</p>
                  <p class="mt-1 text-2xl font-bold text-amber-500">{{ pendingReferrals }}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="grid grid-cols-1 lg:grid-cols-[1.4fr_0.8fr] gap-6">
          <div class="glass-card p-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Your referral link</h2>
            <div class="mt-4 flex flex-col sm:flex-row gap-3">
              <input :value="data.referral_url" readonly class="input-field font-mono text-sm flex-1" />
              <button @click="copyLink" class="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-teal-500 hover:bg-teal-400 transition-colors">
                {{ copied ? 'Copied' : 'Copy Link' }}
              </button>
            </div>
            <div class="mt-4 inline-flex items-center gap-2 rounded-xl bg-gray-100 dark:bg-gray-800/60 px-3 py-2">
              <span class="text-xs text-gray-500">Code</span>
              <span class="font-mono text-sm font-bold text-gray-900 dark:text-white">{{ data.referral_code }}</span>
            </div>
          </div>

          <div class="glass-card p-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Your credits</h2>
            <dl class="mt-4 space-y-3 text-sm">
              <div class="flex items-center justify-between">
                <dt class="text-gray-500">Available</dt>
                <dd class="font-semibold text-emerald-500">{{ data.credit_balance }} x £{{ data.credit_value_gbp }}</dd>
              </div>
              <div class="flex items-center justify-between">
                <dt class="text-gray-500">Awarded</dt>
                <dd class="font-semibold text-gray-900 dark:text-white">{{ data.credits_awarded }}</dd>
              </div>
              <div class="flex items-center justify-between">
                <dt class="text-gray-500">Redeemed</dt>
                <dd class="font-semibold text-gray-900 dark:text-white">{{ data.credits_redeemed }}</dd>
              </div>
            </dl>
            <button @click="$emit('navigate', 'pricing')" class="mt-5 w-full px-4 py-2.5 rounded-xl text-sm font-semibold text-teal-400 bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/20 transition-colors">View Pricing</button>
          </div>
        </section>

        <section v-if="data.referred_by" class="rounded-xl border border-sky-500/20 bg-sky-500/10 p-4 text-sm text-sky-500 dark:text-sky-300">
          You were referred by <span class="font-semibold">{{ data.referred_by.display_name || data.referred_by.email }}</span>.
        </section>

        <section class="glass-card overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-800/60 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Your referred signups</h2>
            <span class="text-sm text-gray-400">{{ data.referrals.length }} total</span>
          </div>

          <div v-if="data.referrals.length === 0" class="p-8 text-center text-gray-500">
            No referred signups yet.
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-800/60 text-left">
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">User</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Joined</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Subscription</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Reward</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="referral in data.referrals" :key="referral.id" class="border-b border-gray-100 dark:border-gray-800/30">
                  <td class="px-4 py-3">
                    <div class="font-medium text-gray-900 dark:text-white">{{ referral.display_name || referral.email }}</div>
                    <div class="text-xs text-gray-400">{{ referral.email }}</div>
                  </td>
                  <td class="px-4 py-3 text-gray-500 dark:text-gray-400">{{ formatDate(referral.created_at) }}</td>
                  <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold capitalize" :class="statusClass(referral.subscription_status)">{{ referral.subscription_status }}</span>
                    <span v-if="referral.subscription_plan" class="ml-1 text-xs text-gray-400">{{ referral.subscription_plan }}</span>
                  </td>
                  <td class="px-4 py-3">
                    <span v-if="referral.reward_earned" class="text-emerald-500 font-medium">Awarded {{ formatDate(referral.reward_earned_at) }}</span>
                    <span v-else class="text-amber-500">Pending payment</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>
