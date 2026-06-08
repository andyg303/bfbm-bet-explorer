<script setup lang="ts">
const downloadUrl = '/downloads/BFBM%20Bet%20Explorer%20Uploader.exe'

defineEmits<{
  (e: 'navigate', page: 'dashboard' | 'account'): void
}>()

const steps = [
  'Download and run the Windows uploader on the PC or VPS where BFBM runs.',
  'Sign in once with your dashboard account to create an upload-only token.',
  'Choose the BFBM history file, pick a time, and install the daily task.',
]
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-[#0b0f1a] text-gray-800 dark:text-gray-200 transition-colors duration-200">
    <nav class="sticky top-0 z-50 bg-white/80 dark:bg-[#0b0f1a]/80 backdrop-blur-2xl border-b border-gray-200 dark:border-gray-800/40">
      <div class="max-w-5xl mx-auto px-4 sm:px-6">
        <div class="flex h-16 items-center justify-between">
          <button @click="$emit('navigate', 'dashboard')" class="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center shadow-glow-teal" style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            </div>
            <span class="text-lg font-bold text-gray-900 dark:text-white tracking-tight">BFBM<span class="text-teal-600 dark:text-teal-400">Uploader</span></span>
          </button>
          <button @click="$emit('navigate', 'dashboard')" class="px-4 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800/50 rounded-lg transition-colors">
            Back to Dashboard
          </button>
        </div>
      </div>
    </nav>

    <main class="max-w-5xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
      <section class="grid lg:grid-cols-[1.05fr_0.95fr] gap-8 lg:gap-12 items-center">
        <div>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-500 dark:text-teal-400 text-xs font-semibold uppercase tracking-wider">
            Automatic daily uploads
          </div>
          <h1 class="mt-5 text-3xl sm:text-5xl font-bold tracking-tight text-gray-900 dark:text-white leading-tight">
            Keep your BFBM data current without manual CSV exports.
          </h1>
          <p class="mt-5 text-base sm:text-lg text-gray-500 dark:text-gray-400 leading-relaxed">
            The Windows companion app sits on your BFBM machine, reads the native bet history file, and uploads recent settled bets to your account on a schedule.
          </p>
          <div class="mt-8 flex flex-col sm:flex-row gap-3">
            <a
              :href="downloadUrl"
              download
              class="btn-glow inline-flex items-center justify-center gap-2 text-base !py-3 !px-6"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1M12 4v12m0 0l-4-4m4 4l4-4" /></svg>
              Download Windows App
            </a>
            <button @click="$emit('navigate', 'account')" class="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-base font-semibold text-teal-500 dark:text-teal-400 bg-teal-500/10 border border-teal-500/20 hover:bg-teal-500/20 transition-colors">
              Manage Tokens
            </button>
          </div>
        </div>

        <div class="glass-card p-6">
          <h2 class="text-base font-semibold text-gray-900 dark:text-white">Setup flow</h2>
          <div class="mt-5 space-y-4">
            <div v-for="(step, index) in steps" :key="step" class="flex gap-3">
              <div class="w-7 h-7 shrink-0 rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-500 dark:text-teal-400 text-sm font-bold flex items-center justify-center">{{ index + 1 }}</div>
              <p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{{ step }}</p>
            </div>
          </div>
        </div>
      </section>

      <section class="mt-12 grid md:grid-cols-3 gap-5">
        <div class="stat-card !p-5">
          <div class="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center mb-4">
            <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
          </div>
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">No saved password</h3>
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400 leading-relaxed">Your password is used only for the initial connection. Scheduled uploads use a revocable upload token.</p>
        </div>
        <div class="stat-card !p-5">
          <div class="w-10 h-10 rounded-lg bg-sky-500/10 flex items-center justify-center mb-4">
            <svg class="w-5 h-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4V7m4 10H5a2 2 0 01-2-2V5a2 2 0 012-2h5l2 2h7a2 2 0 012 2v8a2 2 0 01-2 2z" /></svg>
          </div>
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Native BFBM history</h3>
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400 leading-relaxed">The app can auto-detect BFBM's `uk_bets_history.gz` file or upload a CSV folder you choose.</p>
        </div>
        <div class="stat-card !p-5">
          <div class="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center mb-4">
            <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          </div>
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Nightly schedule</h3>
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400 leading-relaxed">Windows Task Scheduler runs the app daily and uploads a 48-hour overlap so late settlements are picked up.</p>
        </div>
      </section>
    </main>
  </div>
</template>
