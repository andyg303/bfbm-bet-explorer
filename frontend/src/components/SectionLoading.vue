<script setup lang="ts">
withDefaults(defineProps<{
  loading: boolean
  label?: string
}>(), {
  label: 'Loading...',
})
</script>

<template>
  <div class="relative">
    <div :class="{ 'pointer-events-none select-none opacity-45': loading }">
      <slot />
    </div>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="loading"
        class="absolute inset-0 z-20 flex min-h-[6rem] items-center justify-center rounded-2xl bg-white/70 backdrop-blur-[2px] dark:bg-[#0b0f1a]/70"
        role="status"
        aria-live="polite"
      >
        <div class="flex items-center gap-2 rounded-lg border border-gray-200 bg-white/90 px-3 py-2 text-xs font-medium text-gray-600 shadow-sm dark:border-gray-700 dark:bg-gray-900/90 dark:text-gray-300">
          <svg class="h-4 w-4 animate-spin text-teal-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <span>{{ label }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>
