<script setup lang="ts">
import { ref } from 'vue'
import { useDarkMode } from '../composables/useDarkMode'
import { api } from '../services/api'

const { isDark, toggle: toggleDark } = useDarkMode()

const emit = defineEmits<{
  (e: 'navigate', page: string): void
}>()

const name = ref('')
const email = ref('')
const subject = ref('')
const message = ref('')
const submitting = ref(false)
const success = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''
  submitting.value = true
  try {
    await api.post('/contact', {
      name: name.value,
      email: email.value,
      subject: subject.value,
      message: message.value,
    })
    success.value = true
    name.value = ''
    email.value = ''
    subject.value = ''
    message.value = ''
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Something went wrong. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-[#0b0f1a] text-gray-800 dark:text-gray-200 transition-colors duration-200">
    <!-- Navbar -->
    <nav class="sticky top-0 z-50 bg-white/80 dark:bg-[#0b0f1a]/80 backdrop-blur-2xl border-b border-gray-200 dark:border-gray-800/40">
      <div class="max-w-5xl mx-auto px-4 sm:px-6">
        <div class="flex h-16 items-center justify-between">
          <button @click="$emit('navigate', 'landing')" class="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center shadow-glow-teal" style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
            </div>
            <span class="text-lg font-bold text-gray-900 dark:text-white tracking-tight">BFBM<span class="text-teal-600 dark:text-teal-400">Explorer</span></span>
          </button>
          <div class="flex items-center gap-3">
            <button @click="toggleDark" class="p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">
              <svg v-if="isDark" class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
            </button>
            <button @click="$emit('navigate', 'login')" class="px-4 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Sign In</button>
            <button @click="$emit('navigate', 'pricing')" class="btn-glow text-sm !py-2 !px-5">Get Started</button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Content -->
    <div class="max-w-2xl mx-auto px-4 sm:px-6 py-16 sm:py-24">
      <!-- Header -->
      <div class="text-center mb-12">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-5 shadow-glow-teal" style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);">
          <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">Get in touch</h1>
        <p class="mt-4 text-lg text-gray-500 dark:text-gray-400 max-w-md mx-auto">
          Questions about the platform, your subscription, or anything else? We'll get back to you quickly.
        </p>
      </div>

      <!-- Success state -->
      <div v-if="success" class="glass-card p-10 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-5">
          <svg class="w-8 h-8 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">Message sent!</h2>
        <p class="text-gray-500 dark:text-gray-400 mb-6">Thanks for reaching out. We'll be in touch soon.</p>
        <button @click="success = false; $emit('navigate', 'landing')" class="btn-glow text-sm !py-2 !px-6">
          Back to homepage
        </button>
      </div>

      <!-- Form -->
      <form v-else @submit.prevent="handleSubmit" class="glass-card p-8 space-y-5">
        <div v-if="error" class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">
          {{ error }}
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Your name <span class="text-rose-400">*</span></label>
            <input
              v-model="name"
              type="text"
              required
              placeholder="John Smith"
              class="input-field"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Email address <span class="text-rose-400">*</span></label>
            <input
              v-model="email"
              type="email"
              required
              placeholder="you@example.com"
              class="input-field"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Subject <span class="text-rose-400">*</span></label>
          <input
            v-model="subject"
            type="text"
            required
            placeholder="e.g. Question about pricing"
            class="input-field"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Message <span class="text-rose-400">*</span></label>
          <textarea
            v-model="message"
            required
            rows="6"
            placeholder="Tell us how we can help…"
            class="input-field resize-none"
          />
        </div>

        <button
          type="submit"
          :disabled="submitting"
          class="w-full btn-glow !py-3 text-sm disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <span v-if="submitting" class="flex items-center justify-center gap-2">
            <svg class="animate-spin w-4 h-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>
            Sending…
          </span>
          <span v-else class="flex items-center justify-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
            Send message
          </span>
        </button>
      </form>

      <div class="mt-8 text-center">
        <button @click="$emit('navigate', 'landing')" class="text-sm text-teal-400 font-medium hover:text-teal-300">← Back to homepage</button>
      </div>
    </div>
  </div>
</template>
