<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useBetStore } from './stores/betStore'
import { useAuthStore } from './stores/authStore'
import { useDarkMode } from './composables/useDarkMode'
import FilterPanel from './components/FilterPanel.vue'
import StrategyStats from './components/StrategyStats.vue'
import BetTable from './components/BetTable.vue'
import Charts from './components/Charts.vue'
import OddsBandsChart from './components/OddsBandsChart.vue'
import StakingCalculator from './components/StakingCalculator.vue'
import SummaryHeader from './components/SummaryHeader.vue'
import IngestData from './components/IngestData.vue'
import MonthlyPLTable from './components/MonthlyPLTable.vue'
import ArchivedStrategies from './components/ArchivedStrategies.vue'
import AuthPage from './components/AuthPage.vue'
import LandingPage from './components/LandingPage.vue'
import PricingPage from './components/PricingPage.vue'

const betStore = useBetStore()
const auth = useAuthStore()
const { isDark, toggle: toggleDark } = useDarkMode()

// ─── Page routing (SPA-style) ────────────────────────────────────────────────
type AppPage = 'landing' | 'login' | 'register' | 'pricing' | 'dashboard'
const currentPage = ref<AppPage>('landing')
const authInitialMode = ref<'login' | 'register'>('login')

// Determine which page to show on load
function determineInitialPage(): AppPage {
  // Check for Stripe redirect
  const params = new URLSearchParams(window.location.search)
  if (params.get('payment') === 'success') {
    return auth.isAuthenticated ? 'dashboard' : 'login'
  }
  if (auth.isAuthenticated && auth.hasActiveSubscription) return 'dashboard'
  if (auth.isAuthenticated && !auth.hasActiveSubscription) return 'pricing'
  return 'landing'
}

function navigateTo(page: string) {
  if (page === 'login' || page === 'register') {
    authInitialMode.value = page as 'login' | 'register'
    currentPage.value = 'login' // Both use AuthPage
  } else {
    currentPage.value = page as AppPage
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Show the full dashboard? (authenticated + active subscription)
const showDashboard = computed(() =>
  auth.isAuthenticated && auth.hasActiveSubscription && currentPage.value === 'dashboard'
)

// ─── Dashboard state ─────────────────────────────────────────────────────────
const activeTab = ref<'dashboard' | 'archive'>('dashboard')
const sidebarOpen = ref(false)
const showScrollTop = ref(false)
const showUserMenu = ref(false)
const showChangePassword = ref(false)
const cpCurrentPassword = ref('')
const cpNewPassword = ref('')
const cpConfirm = ref('')
const cpError = ref('')
const cpSuccess = ref('')

function handleKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    sidebarOpen.value = !sidebarOpen.value
  }
  if (e.key === 'Escape') {
    sidebarOpen.value = false
    showUserMenu.value = false
  }
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleScroll() {
  showScrollTop.value = window.scrollY > 400
}

function handleLogout() {
  auth.logout()
  showUserMenu.value = false
  currentPage.value = 'landing'
}

async function handleChangePassword() {
  cpError.value = ''
  cpSuccess.value = ''
  if (cpNewPassword.value !== cpConfirm.value) {
    cpError.value = 'Passwords do not match'
    return
  }
  try {
    await auth.changePassword(cpCurrentPassword.value, cpNewPassword.value)
    cpSuccess.value = 'Password changed successfully!'
    cpCurrentPassword.value = ''
    cpNewPassword.value = ''
    cpConfirm.value = ''
    setTimeout(() => {
      showChangePassword.value = false
      cpSuccess.value = ''
    }, 1500)
  } catch {
    cpError.value = auth.error || 'Failed to change password'
  }
}

const archivedCount = computed(() => betStore.archivedStrategies.length)

async function loadDashboardData() {
  await betStore.migrateDeletedToArchived()
  await betStore.loadFilterOptions()
  await betStore.loadSummaryStats()
  await betStore.refreshAll()
  await betStore.loadArchivedStrategies()
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('scroll', handleScroll)
  document.addEventListener('click', (e) => {
    const target = e.target as HTMLElement
    if (!target.closest('.user-menu-container')) {
      showUserMenu.value = false
    }
  })

  // Handle Stripe payment redirect
  const params = new URLSearchParams(window.location.search)
  const paymentStatus = params.get('payment')
  const sessionId = params.get('session_id')

  if (paymentStatus === 'success' && sessionId && auth.isAuthenticated) {
    // Verify the payment and activate subscription
    await auth.verifyPaymentSession(sessionId)
    // Clean up URL
    window.history.replaceState({}, '', window.location.pathname)
  } else if (paymentStatus === 'cancelled') {
    window.history.replaceState({}, '', window.location.pathname)
  }

  // Determine initial page
  currentPage.value = determineInitialPage()

  // If user is authenticated, refresh their profile to get latest subscription status
  if (auth.isAuthenticated) {
    await auth.refreshUserProfile()
    // Re-check after profile refresh
    if (auth.hasActiveSubscription) {
      currentPage.value = 'dashboard'
      await loadDashboardData()
    } else {
      currentPage.value = 'pricing'
    }
  }
})

// Watch for auth changes — when user logs in, check subscription
watch(() => auth.isAuthenticated, async (loggedIn) => {
  if (loggedIn) {
    await auth.refreshUserProfile()
    if (auth.hasActiveSubscription) {
      currentPage.value = 'dashboard'
      await loadDashboardData()
    } else {
      currentPage.value = 'pricing'
    }
  }
})
</script>

<template>
  <!-- ═══════ Landing page (unauthenticated, default) ═══════ -->
  <LandingPage
    v-if="currentPage === 'landing'"
    @navigate="navigateTo"
  />

  <!-- ═══════ Auth pages (login / register) ═══════ -->
  <AuthPage
    v-else-if="currentPage === 'login'"
    :initial-mode="authInitialMode"
    @navigate="navigateTo"
  />

  <!-- ═══════ Pricing page ═══════ -->
  <PricingPage
    v-else-if="currentPage === 'pricing'"
    @navigate="navigateTo"
  />  <!-- ═══════ Dashboard (authenticated + active subscription) ═══════ -->
  <div v-else-if="showDashboard" class="min-h-screen bg-gray-100 dark:bg-gray-950 transition-colors duration-200">
    <!-- ═══════════ Top Navbar ═══════════ -->
    <nav class="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800 shadow-sm">
      <div class="max-w-[1920px] mx-auto px-4 sm:px-6">
        <div class="flex h-16 items-center justify-between">
          <!-- Left: Menu button + Logo -->
          <div class="flex items-center gap-3">
            <button
              @click="sidebarOpen = !sidebarOpen"
              class="lg:hidden p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Toggle sidebar"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="!sidebarOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-sm">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div class="hidden sm:block">
                <h1 class="text-lg font-bold text-gray-900 dark:text-white leading-tight">BFBM Bet Explorer</h1>
                <p class="text-[10px] text-gray-400 dark:text-gray-500 font-medium -mt-0.5">Betting Analytics Dashboard</p>
              </div>
            </div>
          </div>

          <!-- Center: Navigation tabs -->
          <div class="hidden sm:flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              @click="activeTab = 'dashboard'"
              class="relative px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
              :class="activeTab === 'dashboard'
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
            >
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
                Dashboard
              </span>
            </button>
            <button
              @click="activeTab = 'archive'"
              class="relative px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
              :class="activeTab === 'archive'
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
            >
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
                Archive
                <span
                  v-if="archivedCount > 0"
                  class="ml-1 inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold leading-none rounded-full"
                  :class="activeTab === 'archive'
                    ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'"
                >
                  {{ archivedCount }}
                </span>
              </span>
            </button>
          </div>

          <!-- Right: Actions -->
          <div class="flex items-center gap-2">
            <IngestData />
            <button
              @click="toggleDark"
              class="relative p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200"
              :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
            >
              <Transition
                enter-active-class="transition duration-200 ease-out"
                enter-from-class="rotate-90 opacity-0"
                enter-to-class="rotate-0 opacity-100"
                leave-active-class="transition duration-150 ease-in"
                leave-from-class="rotate-0 opacity-100"
                leave-to-class="-rotate-90 opacity-0"
                mode="out-in"
              >
                <svg v-if="!isDark" key="moon" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
                <svg v-else key="sun" class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </Transition>
            </button>

            <!-- User menu -->
            <div class="relative user-menu-container">
              <button
                @click.stop="showUserMenu = !showUserMenu"
                class="flex items-center gap-2 p-1.5 pr-3 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <div class="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                  {{ auth.displayName?.charAt(0)?.toUpperCase() || '?' }}
                </div>
                <span class="hidden sm:block text-sm font-medium max-w-[120px] truncate">{{ auth.displayName }}</span>
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <Transition
                enter-active-class="transition ease-out duration-100"
                enter-from-class="opacity-0 scale-95"
                enter-to-class="opacity-100 scale-100"
                leave-active-class="transition ease-in duration-75"
                leave-from-class="opacity-100 scale-100"
                leave-to-class="opacity-0 scale-95"
              >
                <div
                  v-if="showUserMenu"
                  class="absolute right-0 mt-2 w-64 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-xl z-50 overflow-hidden"
                >
                  <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                    <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ auth.user?.display_name }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ auth.user?.email }}</p>
                    <div class="mt-1.5 flex items-center gap-1.5">
                      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold"
                        :class="auth.hasActiveSubscription
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'"
                      >
                        {{ auth.hasActiveSubscription ? '● Active' : '○ No subscription' }}
                      </span>
                      <span v-if="auth.user?.subscription_plan" class="text-[10px] text-gray-400 dark:text-gray-500">
                        {{ auth.user.subscription_plan === '12month' ? '12 mo' : '6 mo' }}
                      </span>
                    </div>
                  </div>
                  <div class="py-1">
                    <button
                      @click="showChangePassword = true; showUserMenu = false"
                      class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center gap-2"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                      </svg>
                      Change Password
                    </button>
                    <button
                      @click="handleLogout"
                      class="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      Sign Out
                    </button>
                  </div>
                </div>
              </Transition>
            </div>
          </div>
        </div>
      </div>

      <!-- Mobile navigation tabs -->
      <div class="sm:hidden border-t border-gray-200 dark:border-gray-800 px-4 py-2">
        <div class="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            @click="activeTab = 'dashboard'"
            class="flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-all"
            :class="activeTab === 'dashboard'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-500 dark:text-gray-400'"
          >
            Dashboard
          </button>
          <button
            @click="activeTab = 'archive'"
            class="flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-all"
            :class="activeTab === 'archive'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-500 dark:text-gray-400'"
          >
            Archive
            <span v-if="archivedCount > 0" class="ml-1 text-[10px] bg-gray-200 dark:bg-gray-600 px-1.5 py-0.5 rounded-full">{{ archivedCount }}</span>
          </button>
        </div>
      </div>
    </nav>

    <!-- ═══════════ Main Content ═══════════ -->
    <main class="max-w-[1920px] mx-auto">
      <div v-if="activeTab === 'dashboard'" class="px-4 py-6 sm:px-6">
        <SummaryHeader />
        <div class="mt-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
          <aside
            class="lg:col-span-1"
            :class="{ 'fixed inset-0 z-40 bg-black/50 lg:static lg:bg-transparent': sidebarOpen }"
          >
            <div
              v-if="sidebarOpen"
              class="absolute inset-0 lg:hidden"
              @click="sidebarOpen = false"
            />
            <div
              class="relative h-full lg:h-auto overflow-y-auto bg-white dark:bg-gray-900 lg:bg-transparent lg:dark:bg-transparent max-w-sm lg:max-w-none"
              :class="{ 'p-4 lg:p-0': sidebarOpen }"
            >
              <FilterPanel />
              <div class="mt-6">
                <StakingCalculator />
              </div>
            </div>
          </aside>
          <div class="lg:col-span-3 space-y-6">
            <StrategyStats />
            <Charts />
            <MonthlyPLTable />
            <OddsBandsChart />
            <BetTable />
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'archive'" class="px-4 py-6 sm:px-6">
        <ArchivedStrategies />
      </div>
    </main>

    <!-- ═══════════ Footer ═══════════ -->
    <footer class="mt-12 border-t border-gray-200 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50">
      <div class="max-w-[1920px] mx-auto px-4 sm:px-6 py-6">
        <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div class="flex items-center gap-2 text-sm text-gray-400 dark:text-gray-500">
            <div class="w-5 h-5 rounded bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            BFBM Bet Explorer
          </div>
          <div class="flex items-center gap-4 text-xs text-gray-400 dark:text-gray-500">
            <span>{{ betStore.summaryStats?.num_bets?.toLocaleString() || 0 }} bets tracked</span>
            <span>•</span>
            <span>{{ betStore.strategyStats?.length || 0 }} strategies</span>
            <span>•</span>
            <kbd class="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-[10px] font-mono">⌘K</kbd>
          </div>
        </div>
      </div>
    </footer>

    <!-- Scroll-to-top button -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-4"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-4"
    >
      <button
        v-if="showScrollTop"
        @click="scrollToTop"
        class="fixed bottom-6 right-6 z-50 p-3 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/25 transition-colors"
        aria-label="Scroll to top"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      </button>
    </Transition>

    <!-- Loading progress bar -->
    <Transition
      enter-active-class="transition duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="betStore.loading"
        class="fixed top-0 left-0 right-0 z-[60] h-0.5 bg-indigo-200 dark:bg-indigo-900 overflow-hidden"
      >
        <div class="h-full bg-indigo-500 animate-progress-bar" />
      </div>
    </Transition>

    <!-- ═══════════ Change Password Modal ═══════════ -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="showChangePassword"
        class="fixed inset-0 z-[70] flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="showChangePassword = false; cpError = ''; cpSuccess = ''"
      >
        <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md mx-4 overflow-hidden">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <svg class="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              Change Password
            </h3>
            <button
              @click="showChangePassword = false; cpError = ''; cpSuccess = ''"
              class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Form -->
          <form @submit.prevent="handleChangePassword" class="p-6 space-y-4">
            <div v-if="cpError" class="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
              {{ cpError }}
            </div>
            <div v-if="cpSuccess" class="p-3 rounded-lg bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 text-sm text-green-700 dark:text-green-300">
              {{ cpSuccess }}
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Current Password</label>
              <input
                v-model="cpCurrentPassword"
                type="password"
                required
                class="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors"
                placeholder="Enter current password"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">New Password</label>
              <input
                v-model="cpNewPassword"
                type="password"
                required
                minlength="8"
                class="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors"
                placeholder="Enter new password"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Confirm New Password</label>
              <input
                v-model="cpConfirm"
                type="password"
                required
                class="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors"
                placeholder="Confirm new password"
              />
            </div>

            <div class="flex gap-3 pt-2">
              <button
                type="button"
                @click="showChangePassword = false; cpError = ''; cpSuccess = ''"
                class="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 font-medium text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="flex-1 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors shadow-sm"
              >
                Update Password
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style>
@keyframes progress-bar {
  0% { transform: translateX(-100%); width: 40%; }
  50% { transform: translateX(40%); width: 60%; }
  100% { transform: translateX(200%); width: 40%; }
}
.animate-progress-bar {
  animation: progress-bar 1.5s ease-in-out infinite;
}
</style>
