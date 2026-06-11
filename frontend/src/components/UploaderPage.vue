<script setup lang="ts">
import { ref } from 'vue'

const downloadUrl = '/downloads/BFBM%20Bet%20Explorer%20Uploader.exe'
const showHelp = ref(false)

defineEmits<{
  (e: 'navigate', page: string): void
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
            <button @click="$emit('navigate', 'account#section-automation')" class="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-base font-semibold text-teal-500 dark:text-teal-400 bg-teal-500/10 border border-teal-500/20 hover:bg-teal-500/20 transition-colors">
              Manage Tokens
            </button>
            <button @click="$emit('navigate', 'account#section-upload-history')" class="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-base font-semibold text-teal-500 dark:text-teal-400 bg-teal-500/10 border border-teal-500/20 hover:bg-teal-500/20 transition-colors">
              View Upload History
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

      <!-- Expandable help guide — mirrors the desktop app help window -->
      <section class="mt-12">
        <button
          @click="showHelp = !showHelp"
          class="w-full flex items-center justify-between px-5 py-4 rounded-xl bg-white dark:bg-gray-800/30 border border-gray-200 dark:border-gray-700/50 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        >
          <span class="flex items-center gap-2">
            <svg class="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            Desktop App Help &amp; Full Guide
          </span>
          <svg class="w-4 h-4 text-gray-400 transition-transform" :class="showHelp ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
        </button>

        <div v-if="showHelp" class="mt-3 rounded-xl bg-white dark:bg-gray-800/20 border border-gray-200 dark:border-gray-700/50 p-6 sm:p-8 text-sm space-y-8">

          <!-- Quick-start -->
          <div>
            <h3 class="text-base font-bold text-gray-900 dark:text-white mb-3">Quick-start checklist</h3>
            <div class="space-y-2">
              <div class="flex gap-3"><div class="w-5 h-5 shrink-0 rounded bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-bold flex items-center justify-center">1</div><p class="text-gray-600 dark:text-gray-400">Enter your BFBM Bet Explorer email and password, then click <strong class="text-gray-800 dark:text-gray-200">Connect</strong>.</p></div>
              <div class="flex gap-3"><div class="w-5 h-5 shrink-0 rounded bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-bold flex items-center justify-center">2</div><p class="text-gray-600 dark:text-gray-400">Click <strong class="text-gray-800 dark:text-gray-200">Auto</strong> to find your BFBM history file (or use File / Folder).</p></div>
              <div class="flex gap-3"><div class="w-5 h-5 shrink-0 rounded bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-bold flex items-center justify-center">3</div><p class="text-gray-600 dark:text-gray-400">Set the daily upload time (e.g. <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">02:15</code> for 2:15 AM).</p></div>
              <div class="flex gap-3"><div class="w-5 h-5 shrink-0 rounded bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-bold flex items-center justify-center">4</div><p class="text-gray-600 dark:text-gray-400">Click <strong class="text-gray-800 dark:text-gray-200">Install Daily Task</strong>. Once installed you can usually close the app.</p></div>
            </div>
            <div class="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs">
              ✔ After "Install Daily Task" the upload runs automatically each day — the task is set to run whether you are logged in or not, even when the app is closed or the machine is locked.
            </div>
            <div class="mt-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 text-xs">
              ⚠ On some locked-down VPS setups Windows only allows tasks that run while you are logged in. If uploads are not happening overnight, either stay logged in to the VPS, or use "Run in Background" and leave the app open.
            </div>
          </div>

          <hr class="border-gray-200 dark:border-gray-700/50" />

          <!-- BFBM Save Settings -->
          <div>
            <h3 class="text-base font-bold text-gray-900 dark:text-white mb-1">BFBM Save Settings <span class="text-amber-500 font-medium">⚠ Important</span></h3>
            <p class="text-gray-600 dark:text-gray-400 mb-3">The uploader reads the <code class="bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded text-xs">uk_bets_history.gz</code> file that BFBM writes to disk. BFBM only saves this file at certain times — you must ensure it is saved <strong class="text-gray-800 dark:text-gray-200">before</strong> your scheduled upload runs. In BFBM go to <strong class="text-gray-800 dark:text-gray-200">General Settings → Bets</strong> and choose one of:</p>
            <div class="space-y-3 text-gray-600 dark:text-gray-400">
              <div class="flex gap-2.5"><span class="text-teal-400 shrink-0 mt-0.5">•</span><p><strong class="text-gray-800 dark:text-gray-200">Save bets history automatically after midnight</strong> — BFBM saves the file once per day just after midnight. Set your upload time to early morning (e.g. <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">02:15</code>) so the file is ready before the upload runs.</p></div>
              <div class="flex gap-2.5"><span class="text-teal-400 shrink-0 mt-0.5">•</span><p><strong class="text-gray-800 dark:text-gray-200">Save bets history whenever bets are updated</strong> — BFBM saves the file every time a bet is settled. With this option the history is always up-to-date so you can set the upload time to whatever you like.</p></div>
            </div>
            <div class="mt-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs">
              ⚠ If neither option is ticked, BFBM only saves the history file when you close the app — the uploader will read stale data and report 0 new bets even when bets have settled.
            </div>
          </div>

          <hr class="border-gray-200 dark:border-gray-700/50" />

          <!-- Section guide -->
          <div>
            <h3 class="text-base font-bold text-gray-900 dark:text-white mb-4">Section guide</h3>
            <div class="space-y-5">
              <div>
                <h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-2">1. Connect Account</h4>
                <ul class="space-y-1.5 text-gray-600 dark:text-gray-400">
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">API URL</strong> — the address of your BFBM Bet Explorer dashboard. The default is correct; do not change it.</p></li>
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">Email / Password</strong> — your dashboard login credentials. Your password is never stored on disk; only a secure upload token is saved.</p></li>
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">Connect</strong> — logs you in and generates an upload token. You only need to reconnect if you revoke the token from Account Settings.</p></li>
                </ul>
              </div>
              <div>
                <h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-2">2. CSV Source</h4>
                <ul class="space-y-1.5 text-gray-600 dark:text-gray-400">
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">Auto</strong> — searches the default BFBM V3 folder for <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">uk_bets_history.gz</code> automatically. Use this first.</p></li>
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">File</strong> — manually select a single CSV or .gz history file.</p></li>
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">Folder</strong> — select a folder; every CSV file inside it will be uploaded.</p></li>
                </ul>
              </div>
              <div>
                <h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-2">3. Schedule</h4>
                <ul class="space-y-1.5 text-gray-600 dark:text-gray-400">
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">Daily time (HH:MM)</strong> — the time the task runs each day (24-hour clock). <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">02:15</code> is recommended if using the midnight BFBM save option.</p></li>
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">Lookback hours</strong> — how far back to include settled bets (default 48 h). Increase this if you restart your VPS infrequently.</p></li>
                </ul>
              </div>
            </div>
          </div>

          <hr class="border-gray-200 dark:border-gray-700/50" />

          <!-- Buttons guide -->
          <div>
            <h3 class="text-base font-bold text-gray-900 dark:text-white mb-3">Buttons</h3>
            <ul class="space-y-1.5 text-gray-600 dark:text-gray-400">
              <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">Save Settings</strong> — saves all fields to disk without uploading anything.</p></li>
              <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">Run Upload Now</strong> — immediately uploads recent bets. Use this to verify everything is working before relying on the daily task.</p></li>
              <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">Install Daily Task</strong> — registers the task with Windows Task Scheduler. You can close the app straight after this.</p></li>
              <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p><strong class="text-gray-800 dark:text-gray-200">Run in Background</strong> — keeps the app open and uploads every day at the set time. Use this if the scheduled task does not run on your VPS. The app must stay open; click again to stop.</p></li>
            </ul>
          </div>

          <hr class="border-gray-200 dark:border-gray-700/50" />

          <!-- Troubleshooting -->
          <div>
            <h3 class="text-base font-bold text-gray-900 dark:text-white mb-4">Troubleshooting</h3>
            <div class="space-y-6">
              <div>
                <p class="text-amber-600 dark:text-amber-400 font-semibold mb-1">⚠ "Install Daily Task" fails with a non-zero exit status</p>
                <p class="text-gray-600 dark:text-gray-400 mb-2">This usually means Windows Task Scheduler cannot be accessed from your current session (common on Virtual Desktop / RDP sessions inside a VPS).</p>
                <ul class="space-y-1.5 text-gray-600 dark:text-gray-400">
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p>Right-click the .exe and choose "Run as administrator", then try "Install Daily Task" again.</p></li>
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p>If running inside a Virtual Desktop (e.g. multiple BFBM instances via RDP), run the uploader directly on the host VPS desktop — Task Scheduler is a host-level service.</p></li>
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p>As a fallback, open Windows Task Scheduler (<code class="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">taskschd.msc</code>) and create the task manually with action: <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">"BFBM Bet Explorer Uploader.exe" run</code></p></li>
                </ul>
              </div>
              <div>
                <p class="text-amber-600 dark:text-amber-400 font-semibold mb-1">⚠ The daily task was created but nothing uploaded overnight</p>
                <p class="text-gray-600 dark:text-gray-400 mb-2">Some Windows/VPS configurations only run scheduled tasks while a user is logged in. If you disconnect or log off your VPS session the task will not fire.</p>
                <ul class="space-y-1.5 text-gray-600 dark:text-gray-400">
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p>Stay logged in to the VPS (disconnect the RDP window without logging off), or</p></li>
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p>Click "Run in Background" and leave the app open — it uploads daily on its own.</p></li>
                  <li class="flex gap-2"><span class="text-teal-400 shrink-0">•</span><p>Also check your BFBM Save Settings above — if BFBM is not saving the history file before your upload time you will see 0 new bets.</p></li>
                </ul>
              </div>
              <div>
                <p class="text-amber-600 dark:text-amber-400 font-semibold mb-1">⚠ SSL: CERTIFICATE_VERIFY_FAILED</p>
                <p class="text-gray-600 dark:text-gray-400">This can occur on some Windows Server / VPS environments. Download the latest version of the uploader from this page — newer builds bundle the required certificates.</p>
              </div>
              <div>
                <p class="text-amber-600 dark:text-amber-400 font-semibold mb-1">⚠ "Not connected" after reopening the app</p>
                <p class="text-gray-600 dark:text-gray-400">Your token is saved between sessions. If it shows "Not connected", the token may have been revoked from your Account Settings page. Just enter your email and password and click Connect again.</p>
              </div>
            </div>
          </div>

        </div>
      </section>
    </main>
  </div>
</template>
