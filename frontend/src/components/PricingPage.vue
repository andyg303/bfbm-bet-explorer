<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { useDarkMode } from '../composables/useDarkMode'
import { api } from '../services/api'

const auth = useAuthStore()
const { isDark, toggle: toggleDark } = useDarkMode()

const emit = defineEmits<{
  (e: 'navigate', page: 'login' | 'register' | 'landing'): void
  (e: 'checkout-complete'): void
}>()

const loadingPlan = ref<string | null>(null)
const error = ref('')

const plans = [
  {
    key: '6month',
    name: '6 Months',
    price: '£40',
    perMonth: '£6.67',
    period: '6 months',
    features: [
      'Full analytics dashboard',
      'Unlimited CSV imports',
      'All chart types & filters',
      'Staking simulator',
      'Strategy archiving',
      'Secure encrypted data',
    ],
    popular: false,
  },
  {
    key: '12month',
    name: '12 Months',
    price: '£60',
    perMonth: '£5.00',
    period: '12 months',
    savings: 'Save £20',
    features: [
      'Everything in 6 Months',
      'Full analytics dashboard',
      'Unlimited CSV imports',
      'All chart types & filters',
      'Staking simulator',
      'Strategy archiving',
      'Secure encrypted data',
      'Best value — 25% cheaper',
    ],
    popular: true,
  },
]

async function startCheckout(planKey: string) {
  error.value = ''
  loadingPlan.value = planKey

  try {
    const res = await api.post('/stripe/create-checkout-session', { plan: planKey })
    // Redirect to Stripe Checkout
    window.location.href = res.data.checkout_url
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to start checkout. Please try again.'
    loadingPlan.value = null
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors duration-200">
    <!-- Nav -->
    <nav class="sticky top-0 z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-800/50">
      <div class="max-w-5xl mx-auto px-4 sm:px-6">
        <div class="flex h-16 items-center justify-between">
          <button
            @click="$emit('navigate', 'landing')"
            class="flex items-center gap-2.5 hover:opacity-80 transition-opacity"
          >
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <span class="text-lg font-bold text-gray-900 dark:text-white">BFBM Bet Explorer</span>
          </button>
          <div class="flex items-center gap-3">
            <button
              @click="toggleDark"
              class="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <svg v-if="!isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
              <svg v-else class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </button>
            <template v-if="auth.isAuthenticated">
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ auth.displayName }}</span>
            </template>
            <template v-else>
              <button
                @click="$emit('navigate', 'login')"
                class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                Sign In
              </button>
            </template>
          </div>
        </div>
      </div>
    </nav>

    <!-- Content -->
    <div class="max-w-5xl mx-auto px-4 sm:px-6 py-16 sm:py-24">
      <!-- Header -->
      <div class="text-center mb-14">
        <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
          Simple, transparent pricing
        </h1>
        <p class="mt-4 text-lg text-gray-600 dark:text-gray-400 max-w-xl mx-auto">
          One-time payment, no recurring charges. Full access to every feature. Pick the plan that suits you.
        </p>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="mb-8 max-w-lg mx-auto p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm text-center"
      >
        {{ error }}
      </div>

      <!-- Not logged in notice -->
      <div
        v-if="!auth.isAuthenticated"
        class="mb-8 max-w-lg mx-auto p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 text-sm text-center"
      >
        You'll need to
        <button @click="$emit('navigate', 'register')" class="font-semibold underline underline-offset-2 hover:text-amber-800 dark:hover:text-amber-200">create a free account</button>
        before subscribing.
      </div>

      <!-- Pricing cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
        <div
          v-for="plan in plans"
          :key="plan.key"
          class="relative rounded-2xl border-2 transition-all duration-300"
          :class="plan.popular
            ? 'border-indigo-500 dark:border-indigo-400 shadow-xl shadow-indigo-500/10 scale-[1.02]'
            : 'border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700'"
        >
          <!-- Popular badge -->
          <div
            v-if="plan.popular"
            class="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-bold uppercase tracking-wider rounded-full shadow-lg"
          >
            Best Value
          </div>

          <div class="p-8">
            <!-- Plan name -->
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ plan.name }}</h3>

            <!-- Price -->
            <div class="mt-4 flex items-baseline gap-2">
              <span class="text-4xl sm:text-5xl font-extrabold text-gray-900 dark:text-white">{{ plan.price }}</span>
              <div class="text-sm text-gray-500 dark:text-gray-400">
                <div>one-time</div>
                <div class="font-medium text-indigo-600 dark:text-indigo-400">{{ plan.perMonth }}/mo</div>
              </div>
            </div>

            <!-- Savings badge -->
            <div v-if="plan.savings" class="mt-3">
              <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800">
                {{ plan.savings }}
              </span>
            </div>

            <!-- Features -->
            <ul class="mt-6 space-y-3">
              <li
                v-for="feat in plan.features"
                :key="feat"
                class="flex items-start gap-2.5 text-sm text-gray-700 dark:text-gray-300"
              >
                <svg class="w-5 h-5 text-indigo-500 dark:text-indigo-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                {{ feat }}
              </li>
            </ul>

            <!-- CTA button -->
            <button
              @click="auth.isAuthenticated ? startCheckout(plan.key) : $emit('navigate', 'register')"
              :disabled="loadingPlan === plan.key"
              class="mt-8 w-full py-3 px-6 rounded-xl font-semibold text-sm transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
              :class="plan.popular
                ? 'text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:-translate-y-0.5'
                : 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/50 hover:bg-indigo-100 dark:hover:bg-indigo-950/80 border border-indigo-200 dark:border-indigo-800'"
            >
              <span v-if="loadingPlan === plan.key" class="flex items-center justify-center gap-2">
                <svg class="animate-spin w-4 h-4" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Redirecting to checkout…
              </span>
              <span v-else>
                {{ auth.isAuthenticated ? `Subscribe — ${plan.price}` : 'Create Account to Subscribe' }}
              </span>
            </button>
          </div>
        </div>
      </div>

      <!-- Trust signals -->
      <div class="mt-14 text-center">
        <div class="flex flex-wrap items-center justify-center gap-6 text-sm text-gray-500 dark:text-gray-400">
          <span class="flex items-center gap-1.5">
            <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Secure payment via Stripe
          </span>
          <span class="flex items-center gap-1.5">
            <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            256-bit encryption
          </span>
          <span class="flex items-center gap-1.5">
            <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Instant access after payment
          </span>
        </div>
      </div>

      <!-- Back link -->
      <div class="mt-10 text-center">
        <button
          @click="$emit('navigate', 'landing')"
          class="text-sm text-indigo-600 dark:text-indigo-400 font-medium hover:underline"
        >
          ← Back to homepage
        </button>
      </div>
    </div>
  </div>
</template>
