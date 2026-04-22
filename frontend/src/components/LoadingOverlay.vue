<script setup lang="ts">
// Reusable fullscreen loading overlay with a spinning indicator.
// Used for any long-running async action (initial dashboard load,
// recalculating staking, etc.). Teleported to body so it always
// floats above the rest of the UI.
defineProps<{
  show: boolean
  title?: string
  message?: string
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="loading-overlay-fade">
      <div
        v-if="show"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      >
        <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-4 max-w-xs mx-4">
          <svg class="w-12 h-12 animate-spin text-teal-400" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <p class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ title ?? 'Loading…' }}
          </p>
          <p v-if="message" class="text-xs text-gray-500 text-center">{{ message }}</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.loading-overlay-fade-enter-active,
.loading-overlay-fade-leave-active {
  transition: opacity 0.2s ease;
}
.loading-overlay-fade-enter-from,
.loading-overlay-fade-leave-to {
  opacity: 0;
}
</style>
