<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  message: string
  type?: 'success' | 'error' | 'info'
  show: boolean
  duration?: number
}>()

const emit = defineEmits<{
  close: []
}>()

watch(
  () => props.show,
  (val) => {
    if (val) {
      setTimeout(() => emit('close'), props.duration || 4000)
    }
  }
)

const typeClasses = {
  success: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
  error: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
  info: 'bg-teal-500/10 text-teal-400 border border-teal-500/20',
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="translate-y-4 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-4 opacity-0"
    >
      <div
        v-if="show"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[200] max-w-md w-full px-4"
      >
        <div
          class="flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl shadow-black/40 backdrop-blur-xl text-sm font-medium"
          :class="typeClasses[type || 'info']"
        >
          <!-- Icon -->
          <svg v-if="type === 'success'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <svg v-else-if="type === 'error'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <svg v-else class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="flex-1">{{ message }}</span>
          <button @click="emit('close')" class="shrink-0 p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
