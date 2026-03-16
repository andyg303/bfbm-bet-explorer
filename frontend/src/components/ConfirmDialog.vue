<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title?: string
    message?: string
    confirmLabel?: string
    cancelLabel?: string
    variant?: 'danger' | 'warning' | 'info'
    icon?: 'archive' | 'trash' | 'restore' | 'warning'
  }>(),
  {
    title: 'Are you sure?',
    message: '',
    confirmLabel: 'Confirm',
    cancelLabel: 'Cancel',
    variant: 'warning',
    icon: 'warning',
  }
)

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'danger':
      return {
        iconBg: 'bg-rose-500/10',
        iconColor: 'text-rose-400',
        button: 'bg-rose-500/20 border border-rose-500/30 text-rose-400 hover:bg-rose-500/30',
      }
    case 'info':
      return {
        iconBg: 'bg-teal-500/10',
        iconColor: 'text-teal-400',
        button: 'bg-teal-500/20 border border-teal-500/30 text-teal-400 hover:bg-teal-500/30',
      }
    default:
      return {
        iconBg: 'bg-amber-500/10',
        iconColor: 'text-amber-400',
        button: 'bg-amber-500/20 border border-amber-500/30 text-amber-400 hover:bg-amber-500/30',
      }
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="open" class="fixed inset-0 z-[100] overflow-y-auto">
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="emit('cancel')" />

        <!-- Dialog -->
        <div class="flex min-h-full items-center justify-center p-4">
          <Transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="opacity-0 scale-95 translate-y-4"
            enter-to-class="opacity-100 scale-100 translate-y-0"
            leave-active-class="transition duration-150 ease-in"
            leave-from-class="opacity-100 scale-100 translate-y-0"
            leave-to-class="opacity-0 scale-95 translate-y-4"
          >
            <div
              v-if="open"
              class="relative w-full max-w-md transform glass-card !p-6 shadow-2xl shadow-black/40"
            >
              <div class="flex items-start gap-4">
                <!-- Icon -->
                <div
                  class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full"
                  :class="variantClasses.iconBg"
                >
                  <!-- Archive icon -->
                  <svg
                    v-if="icon === 'archive'"
                    class="h-6 w-6"
                    :class="variantClasses.iconColor"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                  </svg>
                  <!-- Restore icon -->
                  <svg
                    v-else-if="icon === 'restore'"
                    class="h-6 w-6"
                    :class="variantClasses.iconColor"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <!-- Trash icon -->
                  <svg
                    v-else-if="icon === 'trash'"
                    class="h-6 w-6"
                    :class="variantClasses.iconColor"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  <!-- Warning icon (default) -->
                  <svg
                    v-else
                    class="h-6 w-6"
                    :class="variantClasses.iconColor"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>

                <!-- Content -->
                <div class="flex-1">
                  <h3 class="text-base font-semibold text-white">
                    {{ title }}
                  </h3>
                  <p class="mt-2 text-sm text-gray-400">
                    {{ message }}
                  </p>
                </div>
              </div>

              <!-- Actions -->
              <div class="mt-6 flex justify-end gap-3">
                <button
                  @click="emit('cancel')"
                  class="rounded-lg px-4 py-2 text-sm font-medium text-gray-400 bg-white/5 border border-white/10 hover:bg-white/10 focus:outline-none transition-all"
                >
                  {{ cancelLabel }}
                </button>
                <button
                  @click="emit('confirm')"
                  class="rounded-lg px-4 py-2 text-sm font-medium focus:outline-none transition-all"
                  :class="variantClasses.button"
                >
                  {{ confirmLabel }}
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
