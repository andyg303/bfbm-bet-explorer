<script setup lang="ts">
import { computed } from 'vue'
import { useDarkMode } from '../composables/useDarkMode'

const { isDark, toggle: toggleDark } = useDarkMode()

const emit = defineEmits<{
  (e: 'navigate', page: 'login' | 'register' | 'pricing'): void
}>()

const features = [
  {
    icon: 'chart',
    title: 'Deep Analytics',
    desc: 'Comprehensive P&L tracking, ROI analysis, and strategy performance breakdown across all your betting activity.',
  },
  {
    icon: 'filter',
    title: 'Powerful Filters',
    desc: 'Slice and dice your data by strategy, market type, odds range, date, and dozens more parameters.',
  },
  {
    icon: 'staking',
    title: 'Staking Simulator',
    desc: 'Model level stakes, percentage, or Kelly criterion strategies and see how they would have performed.',
  },
  {
    icon: 'calendar',
    title: 'Monthly Breakdown',
    desc: 'Visualise your monthly P&L with detailed tables and charts showing trends over time.',
  },
  {
    icon: 'upload',
    title: 'Easy CSV Import',
    desc: 'Import your Betfair bet history directly. Just export from BFBM and upload — we handle the rest.',
  },
  {
    icon: 'shield',
    title: 'Secure & Private',
    desc: 'Your data is encrypted, scoped to your account, and never shared. Enterprise-grade security.',
  },
]

const stats = [
  { value: '50+', label: 'Filter options' },
  { value: '6', label: 'Chart types' },
  { value: '∞', label: 'Strategies tracked' },
  { value: '< 1s', label: 'Load time' },
]
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-gray-950 transition-colors duration-200">
    <!-- ═══════════ Navbar ═══════════ -->
    <nav class="sticky top-0 z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-800/50">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <span class="text-lg font-bold text-gray-900 dark:text-white">BFBM Bet Explorer</span>
          </div>
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
            <button
              @click="$emit('navigate', 'login')"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              Sign In
            </button>
            <button
              @click="$emit('navigate', 'pricing')"
              class="px-5 py-2 text-sm font-medium text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl shadow-md shadow-indigo-500/25 transition-all duration-200"
            >
              Get Started
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- ═══════════ Hero ═══════════ -->
    <section class="relative overflow-hidden">
      <!-- Gradient bg decorations -->
      <div class="absolute inset-0 -z-10">
        <div class="absolute top-0 left-1/4 w-96 h-96 bg-indigo-400/10 dark:bg-indigo-500/5 rounded-full blur-3xl"></div>
        <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-400/10 dark:bg-purple-500/5 rounded-full blur-3xl"></div>
      </div>

      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 sm:pt-28 sm:pb-32">
        <div class="text-center max-w-3xl mx-auto">
          <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200/50 dark:border-indigo-800/50 text-indigo-700 dark:text-indigo-300 text-sm font-medium mb-6">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Betfair Betting Analytics
          </div>

          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-gray-900 dark:text-white leading-[1.1]">
            Turn your bets into
            <span class="bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent"> profitable insights</span>
          </h1>

          <p class="mt-6 text-lg sm:text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed">
            The most powerful analytics dashboard for Betfair & BFBM users.
            Track every strategy, model every staking plan, and find your edge — all in one place.
          </p>

          <div class="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <button
              @click="$emit('navigate', 'pricing')"
              class="px-8 py-3.5 text-base font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30 transition-all duration-200 hover:-translate-y-0.5"
            >
              View Plans & Pricing
            </button>
            <button
              @click="$emit('navigate', 'login')"
              class="px-8 py-3.5 text-base font-semibold text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600 rounded-xl shadow-sm hover:shadow transition-all duration-200"
            >
              Sign In →
            </button>
          </div>
        </div>

        <!-- Stats row -->
        <div class="mt-20 grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-2xl mx-auto">
          <div
            v-for="stat in stats"
            :key="stat.label"
            class="text-center"
          >
            <div class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</div>
            <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════ Features Grid ═══════════ -->
    <section class="py-20 sm:py-28 bg-gray-50/50 dark:bg-gray-900/30">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">Everything you need to find your edge</h2>
          <p class="mt-4 text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Purpose-built for serious Betfair punters who want to understand their results, not just track them.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div
            v-for="feature in features"
            :key="feature.title"
            class="group relative bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800 hover:border-indigo-300 dark:hover:border-indigo-700 hover:shadow-lg hover:shadow-indigo-500/5 transition-all duration-300"
          >
            <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/50 dark:to-purple-950/50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <!-- Chart icon -->
              <svg v-if="feature.icon === 'chart'" class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <!-- Filter icon -->
              <svg v-else-if="feature.icon === 'filter'" class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              <!-- Staking icon -->
              <svg v-else-if="feature.icon === 'staking'" class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <!-- Calendar icon -->
              <svg v-else-if="feature.icon === 'calendar'" class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <!-- Upload icon -->
              <svg v-else-if="feature.icon === 'upload'" class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <!-- Shield icon -->
              <svg v-else-if="feature.icon === 'shield'" class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">{{ feature.title }}</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{{ feature.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════ CTA Section ═══════════ -->
    <section class="py-20 sm:py-28">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div class="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl p-10 sm:p-14 shadow-2xl shadow-indigo-500/20 relative overflow-hidden">
          <!-- Decorative circles -->
          <div class="absolute top-0 right-0 w-40 h-40 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2"></div>
          <div class="absolute bottom-0 left-0 w-32 h-32 bg-white/10 rounded-full translate-y-1/2 -translate-x-1/2"></div>

          <h2 class="text-3xl sm:text-4xl font-bold text-white mb-4 relative">
            Ready to take your betting seriously?
          </h2>
          <p class="text-indigo-100 text-lg mb-8 max-w-xl mx-auto relative">
            Join punters who track, analyse, and improve their results. Plans from just £40 for 6 months.
          </p>
          <div class="flex flex-col sm:flex-row gap-4 justify-center relative">
            <button
              @click="$emit('navigate', 'pricing')"
              class="px-8 py-3.5 text-base font-semibold text-indigo-600 bg-white hover:bg-gray-50 rounded-xl shadow-lg transition-all duration-200 hover:-translate-y-0.5"
            >
              See Pricing
            </button>
            <button
              @click="$emit('navigate', 'register')"
              class="px-8 py-3.5 text-base font-semibold text-white border-2 border-white/30 hover:border-white/60 rounded-xl transition-all duration-200"
            >
              Create Free Account
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════ Footer ═══════════ -->
    <footer class="border-t border-gray-200 dark:border-gray-800 py-8">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <div class="w-5 h-5 rounded bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          BFBM Bet Explorer © {{ new Date().getFullYear() }}
        </div>
        <div class="text-xs text-gray-400 dark:text-gray-500">
          Secure payments powered by Stripe
        </div>
      </div>
    </footer>
  </div>
</template>
