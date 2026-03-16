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
  <div class="min-h-screen bg-gray-50 dark:bg-[#0b0f1a] text-gray-800 dark:text-gray-200 transition-colors duration-200">
    <!-- ═══════════ Navbar ═══════════ -->
    <nav class="sticky top-0 z-50 bg-white/80 dark:bg-[#0b0f1a]/80 backdrop-blur-2xl border-b border-gray-200 dark:border-gray-800/40">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center shadow-glow-teal" style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <span class="text-lg font-bold text-gray-900 dark:text-white tracking-tight">BFBM<span class="text-teal-600 dark:text-teal-400 ml-0.5">Explorer</span></span>
          </div>
          <div class="flex items-center gap-3">
            <button
              @click="toggleDark"
              class="p-2 rounded-lg text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors"
            >
              <svg v-if="isDark" class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            </button>
            <button
              @click="$emit('navigate', 'login')"
              class="px-4 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              Sign In
            </button>
            <button
              @click="$emit('navigate', 'pricing')"
              class="btn-glow text-sm !py-2 !px-5"
            >
              Get Started
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- ═══════════ Hero ═══════════ -->
    <section class="relative overflow-hidden">
      <!-- Background gradient mesh -->
      <div class="absolute inset-0 -z-10">
        <div class="absolute top-[-20%] left-[10%] w-[600px] h-[600px] rounded-full opacity-20 blur-[120px]" style="background: radial-gradient(circle, #14b8a6 0%, transparent 70%);"></div>
        <div class="absolute bottom-[-10%] right-[5%] w-[500px] h-[500px] rounded-full opacity-15 blur-[120px]" style="background: radial-gradient(circle, #0ea5e9 0%, transparent 70%);"></div>
        <!-- Grid pattern overlay -->
        <div class="absolute inset-0 opacity-[0.03]" style="background-image: linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 64px 64px;"></div>
      </div>

      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-28 sm:pt-32 sm:pb-36">
        <div class="text-center max-w-3xl mx-auto">
          <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-sm font-medium mb-8 animate-fade-in-up">
            <span class="w-2 h-2 rounded-full bg-teal-400 animate-pulse"></span>
            Betfair Betting Analytics
          </div>

          <h1 class="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-gray-900 dark:text-white leading-[1.05] animate-fade-in-up stagger-1">
            Turn your bets into
            <span class="gradient-text"> profitable insights</span>
          </h1>

          <p class="mt-7 text-lg sm:text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed animate-fade-in-up stagger-2">
            The most powerful analytics dashboard for Betfair & BFBM users.
            Track every strategy, model every staking plan, and find your edge.
          </p>

          <div class="mt-12 flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up stagger-3">
            <button
              @click="$emit('navigate', 'pricing')"
              class="btn-glow text-base !py-3.5 !px-8"
            >
              View Plans & Pricing
              <svg class="w-4 h-4 ml-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
            </button>
            <button
              @click="$emit('navigate', 'login')"
              class="px-8 py-3.5 text-base font-semibold text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700/50 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-900 dark:hover:text-white rounded-xl transition-all duration-200"
            >
              Sign In →
            </button>
          </div>
        </div>

        <!-- Stats row -->
        <div class="mt-24 grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-2xl mx-auto">
          <div
            v-for="(stat, i) in stats"
            :key="stat.label"
            class="text-center animate-fade-in-up"
            :class="'stagger-' + (i + 4)"
          >
            <div class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white font-mono">{{ stat.value }}</div>
            <div class="text-sm text-gray-500 mt-1.5">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════ Features Grid ═══════════ -->
    <section class="py-24 sm:py-32 relative">
      <div class="absolute inset-0 bg-gradient-to-b from-transparent via-gray-900/30 to-transparent"></div>
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div class="text-center mb-16">
          <h2 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">Everything you need to find your edge</h2>
          <p class="mt-4 text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
            Purpose-built for serious Betfair punters who want to understand their results, not just track them.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <div
            v-for="feature in features"
            :key="feature.title"
            class="group stat-card !p-6 hover:!border-teal-800/40"
          >
            <div class="w-10 h-10 rounded-lg bg-teal-500/10 flex items-center justify-center mb-4 group-hover:bg-teal-500/20 transition-colors">
              <svg v-if="feature.icon === 'chart'" class="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <svg v-else-if="feature.icon === 'filter'" class="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              <svg v-else-if="feature.icon === 'staking'" class="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <svg v-else-if="feature.icon === 'calendar'" class="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <svg v-else-if="feature.icon === 'upload'" class="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <svg v-else-if="feature.icon === 'shield'" class="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-2">{{ feature.title }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">{{ feature.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════ CTA Section ═══════════ -->
    <section class="py-24 sm:py-28">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div class="accent-stripe rounded-3xl p-10 sm:p-14 relative overflow-hidden" style="background: linear-gradient(135deg, #0f2027 0%, #111827 50%, #0f2027 100%);">
          <!-- Decorative elements -->
          <div class="absolute top-0 right-0 w-64 h-64 rounded-full opacity-10 -translate-y-1/2 translate-x-1/2" style="background: radial-gradient(circle, #14b8a6, transparent 70%);"></div>
          <div class="absolute bottom-0 left-0 w-48 h-48 rounded-full opacity-10 translate-y-1/2 -translate-x-1/2" style="background: radial-gradient(circle, #0ea5e9, transparent 70%);"></div>

          <h2 class="text-3xl sm:text-4xl font-bold text-white mb-4 relative">
            Ready to take your betting seriously?
          </h2>
          <p class="text-gray-400 text-lg mb-10 max-w-xl mx-auto relative">
            Join punters who track, analyse, and improve their results. Plans from just £40 for 6 months.
          </p>
          <div class="flex flex-col sm:flex-row gap-4 justify-center relative">
            <button
              @click="$emit('navigate', 'pricing')"
              class="btn-glow text-base !py-3.5 !px-8"
            >
              See Pricing
            </button>
            <button
              @click="$emit('navigate', 'register')"
              class="px-8 py-3.5 text-base font-semibold text-gray-300 border border-gray-600/50 hover:border-gray-500 rounded-xl transition-all duration-200"
            >
              Create Free Account
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════ Footer ═══════════ -->
    <footer class="border-t border-gray-200 dark:border-gray-800/50 py-8">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2.5 text-sm text-gray-400 dark:text-gray-500">
          <div class="w-5 h-5 rounded flex items-center justify-center" style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);">
            <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          BFBM Explorer © {{ new Date().getFullYear() }}
        </div>
        <div class="text-xs text-gray-600">
          Secure payments powered by Stripe
        </div>
      </div>
    </footer>
  </div>
</template>
