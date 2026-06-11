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
import AdvancedOddsCharts from './components/AdvancedOddsCharts.vue'
import StakingCalculator from './components/StakingCalculator.vue'
import SummaryHeader from './components/SummaryHeader.vue'
import IngestData from './components/IngestData.vue'
import MonthlyPLTable from './components/MonthlyPLTable.vue'
import ArchivedStrategies from './components/ArchivedStrategies.vue'
import StrategyManager from './components/StrategyManager.vue'
import AuthPage from './components/AuthPage.vue'
import LandingPage from './components/LandingPage.vue'
import PricingPage from './components/PricingPage.vue'
import AccountSettings from './components/AccountSettings.vue'
import AdminDashboard from './components/AdminDashboard.vue'
import LoadingOverlay from './components/LoadingOverlay.vue'
import ContactPage from './components/ContactPage.vue'
import UploaderPage from './components/UploaderPage.vue'
import ReferralPage from './components/ReferralPage.vue'

const betStore = useBetStore()
const auth = useAuthStore()
const { isDark, toggle: toggleDark } = useDarkMode()

// ─── Page routing (SPA-style with real URLs) ────────────────────────────────
type AppPage = 'landing' | 'login' | 'register' | 'pricing' | 'dashboard' | 'forgot-password' | 'reset-password' | 'account' | 'admin' | 'contact' | 'uploader' | 'referrals'
const currentPage = ref<AppPage>('landing')
const authInitialMode = ref<'login' | 'register' | 'forgot' | 'reset'>('login')
const resetTokenFromUrl = ref('')

// URL ↔ page mapping
const PAGE_PATHS: Record<AppPage, string> = {
  landing: '/',
  login: '/login',
  register: '/register',
  pricing: '/pricing',
  dashboard: '/dashboard',
  'forgot-password': '/forgot-password',
  'reset-password': '/reset-password',
  account: '/account',
  admin: '/admin',
  contact: '/contact',
  uploader: '/uploader',
  referrals: '/referrals',
}

function pageFromPath(path: string): AppPage {
  const clean = path.replace(/\/+$/, '') || '/'
  for (const [page, p] of Object.entries(PAGE_PATHS)) {
    if (clean === p) return page as AppPage
  }
  return 'landing'
}

// Determine which page to show on load
function determineInitialPage(): AppPage {
  // Check for Stripe redirect
  const params = new URLSearchParams(window.location.search)
  if (params.get('payment') === 'success') {
    return auth.isAuthenticated ? 'dashboard' : 'login'
  }
  // Respect the current URL path first
  const urlPage = pageFromPath(window.location.pathname)

  if (urlPage === 'login' || urlPage === 'register') {
    authInitialMode.value = urlPage
    return urlPage
  }
  // Handle password reset link from email
  if (urlPage === 'reset-password') {
    const token = params.get('token')
    if (token) resetTokenFromUrl.value = token
    authInitialMode.value = 'reset'
    return 'reset-password'
  }
  if (urlPage === 'forgot-password') {
    authInitialMode.value = 'forgot'
    return 'forgot-password'
  }
  // Guard: account/uploader pages require auth + subscription
  if (urlPage === 'account' || urlPage === 'uploader') {
    if (!auth.isAuthenticated) return 'login'
    if (!auth.hasActiveSubscription) return 'pricing'
    return urlPage
  }
  if (urlPage === 'referrals') {
    if (!auth.isAuthenticated) return 'login'
    return 'referrals'
  }
  // Guard: admin page requires auth + admin
  if (urlPage === 'admin') {
    if (!auth.isAuthenticated) return 'login'
    if (!auth.user?.is_admin) return 'dashboard'
    return 'admin'
  }
  // Guard: dashboard requires auth + subscription
  if (urlPage === 'dashboard') {
    if (!auth.isAuthenticated) return 'login'
    if (!auth.hasActiveSubscription) return 'pricing'
    return 'dashboard'
  }
  // Guard: pricing while not logged in → allow (they can view it)
  // If authenticated with subscription and on landing → go to dashboard
  if (urlPage === 'landing' && auth.isAuthenticated && auth.hasActiveSubscription) return 'dashboard'
  if (urlPage === 'landing' && auth.isAuthenticated && !auth.hasActiveSubscription) return 'pricing'
  return urlPage
}

const accountScrollTarget = ref<string>('')

function navigateTo(page: string, replace = false) {
  const hashIdx = page.indexOf('#')
  const scrollTarget = hashIdx !== -1 ? page.slice(hashIdx + 1) : ''
  const pageClean = hashIdx !== -1 ? page.slice(0, hashIdx) : page
  if (scrollTarget) accountScrollTarget.value = scrollTarget
  let targetPage = pageClean as AppPage
  if ((targetPage === 'dashboard' || targetPage === 'account' || targetPage === 'uploader') && (!auth.isAuthenticated || !auth.hasActiveSubscription)) {
    targetPage = auth.isAuthenticated ? 'pricing' : 'login'
  } else if (targetPage === 'referrals' && !auth.isAuthenticated) {
    targetPage = 'login'
  } else if (targetPage === 'admin' && (!auth.isAuthenticated || !auth.user?.is_admin)) {
    targetPage = !auth.isAuthenticated ? 'login' : auth.hasActiveSubscription ? 'dashboard' : 'pricing'
  }

  if (targetPage === 'login' || targetPage === 'register') {
    authInitialMode.value = targetPage as 'login' | 'register'
    currentPage.value = targetPage
  } else if (targetPage === 'forgot-password') {
    authInitialMode.value = 'forgot'
    currentPage.value = 'forgot-password'
  } else if (targetPage === 'reset-password') {
    authInitialMode.value = 'reset'
    currentPage.value = 'reset-password'
  } else {
    currentPage.value = targetPage
  }
  // Update the browser URL
  const targetPath = PAGE_PATHS[currentPage.value] || '/'
  if (window.location.pathname !== targetPath) {
    if (replace) {
      window.history.replaceState({ page: currentPage.value }, '', targetPath)
    } else {
      window.history.pushState({ page: currentPage.value }, '', targetPath)
    }
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Handle browser back/forward buttons
function handlePopState(e: PopStateEvent) {
  const page = e.state?.page || pageFromPath(window.location.pathname)
  if (page === 'login' || page === 'register') {
    authInitialMode.value = page as 'login' | 'register'
  } else if (page === 'forgot-password') {
    authInitialMode.value = 'forgot'
  } else if (page === 'reset-password') {
    authInitialMode.value = 'reset'
  }
  currentPage.value = page as AppPage
}

// Show the full dashboard? (authenticated + active subscription)
const showDashboard = computed(() =>
  auth.isAuthenticated && auth.hasActiveSubscription && currentPage.value === 'dashboard'
)

// ─── Dashboard state ─────────────────────────────────────────────────────────
const activeTab = ref<'dashboard' | 'archive' | 'strategies'>('dashboard')
const sidebarOpen = ref(false)
const desktopFilterOpen = ref(true)

function toggleFilterPanel() {
  if (window.innerWidth >= 1024) {
    desktopFilterOpen.value = !desktopFilterOpen.value
  } else {
    sidebarOpen.value = !sidebarOpen.value
  }
}
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
  navigateTo('landing', true)
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

// Tracks the initial dashboard data load (first paint after login/refresh).
// Used to show a full-screen spinner so users know something is happening
// while the various endpoints (which can take 5-10 seconds) return.
const initialDashboardLoading = ref(false)
const hasLoadedDashboardOnce = ref(false)

async function loadDashboardData() {
  if (!hasLoadedDashboardOnce.value) {
    initialDashboardLoading.value = true
  }
  try {
    await betStore.migrateDeletedToArchived()
    await betStore.loadFilterOptions()
    await betStore.loadSummaryStats()
    await betStore.refreshAll()
    await betStore.loadArchivedStrategies()
    // Load merge suggestions in the background for the badge count
    betStore.loadMergeSuggestions()
  } finally {
    initialDashboardLoading.value = false
    hasLoadedDashboardOnce.value = true
  }
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('scroll', handleScroll)
  window.addEventListener('popstate', handlePopState)
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
    // Clean up URL → go to dashboard
    window.history.replaceState({ page: 'dashboard' }, '', '/dashboard')
  } else if (paymentStatus === 'cancelled') {
    window.history.replaceState({ page: 'pricing' }, '', '/pricing')
  }

  // Determine initial page from URL + auth state
  currentPage.value = determineInitialPage()

  // If user is authenticated, refresh their profile to get latest subscription status
  if (auth.isAuthenticated) {
    await auth.refreshUserProfile()
    currentPage.value = determineInitialPage()
    // Load dashboard data if needed
    if (currentPage.value === 'dashboard') {
      await loadDashboardData()
    }
  }

  // Sync URL to match the determined page (use replaceState so we don't add a history entry)
  const correctPath = PAGE_PATHS[currentPage.value] || '/'
  if (window.location.pathname !== correctPath && !paymentStatus) {
    window.history.replaceState({ page: currentPage.value }, '', correctPath)
  }
})

// Watch for auth changes — when user logs in, check subscription
watch(() => auth.isAuthenticated, async (loggedIn) => {
  if (loggedIn) {
    await auth.refreshUserProfile()
    if (auth.hasActiveSubscription) {
      navigateTo('dashboard', true)
      await loadDashboardData()
    } else {
      navigateTo('pricing', true)
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

  <!-- ═══════ Auth pages (login / register / forgot / reset) ═══════ -->
  <AuthPage
    v-else-if="currentPage === 'login' || currentPage === 'register' || currentPage === 'forgot-password' || currentPage === 'reset-password'"
    :initial-mode="authInitialMode"
    :initial-token="resetTokenFromUrl"
    @navigate="navigateTo"
  />

  <!-- ═══════ Pricing page ═══════ -->
  <PricingPage
    v-else-if="currentPage === 'pricing'"
    @navigate="navigateTo"
  />

  <!-- ═══════ Account Settings ═══════ -->
  <AccountSettings
    v-else-if="currentPage === 'account'"
    :scroll-to="accountScrollTarget"
    @navigate="navigateTo"
  />

  <!-- ═══════ Contact page ═══════ -->
  <ContactPage
    v-else-if="currentPage === 'contact'"
    @navigate="navigateTo"
  />

  <!-- ═══════ Windows uploader download page ═══════ -->
  <UploaderPage
    v-else-if="currentPage === 'uploader'"
    @navigate="navigateTo"
  />

  <!-- ═══════ Referral page ═══════ -->
  <ReferralPage
    v-else-if="currentPage === 'referrals'"
    @navigate="navigateTo"
  />

  <!-- ═══════ Admin Dashboard (admin only) ═══════ -->
  <AdminDashboard
    v-else-if="currentPage === 'admin' && auth.user?.is_admin"
    @navigate="navigateTo"
  />

  <!-- ═══════ Dashboard (authenticated + active subscription) ═══════ -->
  <div v-else-if="showDashboard" class="min-h-screen bg-gray-50 dark:bg-[#0b0f1a] text-gray-800 dark:text-gray-200 transition-colors duration-200">
    <!-- ═══════════ Top Navbar ═══════════ -->
    <nav class="sticky top-0 z-50 bg-white/80 dark:bg-[#0b0f1a]/80 backdrop-blur-2xl border-b border-gray-200 dark:border-gray-800/40">
      <div class="px-4 sm:px-6">
        <div class="flex h-14 items-center justify-between">
          <!-- Left: Menu button + Logo -->
          <div class="flex items-center gap-3">
            <button @click="toggleFilterPanel" class="p-2 rounded-lg text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors" aria-label="Toggle filters">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="!sidebarOpen && desktopFilterOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center shadow-glow-teal" style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
              </div>
              <div class="hidden sm:block">
                <h1 class="text-base font-bold text-gray-900 dark:text-white leading-tight tracking-tight">BFBM<span class="text-teal-600 dark:text-teal-400">Explorer</span></h1>
                <p class="text-[10px] text-gray-400 dark:text-gray-500 font-medium font-mono -mt-0.5">Analytics Dashboard</p>
              </div>
            </div>
          </div>

          <!-- Center: Navigation tabs (pill-nav) -->
          <div class="hidden sm:flex pill-nav">
            <button @click="activeTab = 'dashboard'" :class="activeTab === 'dashboard' ? 'active' : ''">
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
                Dashboard
              </span>
            </button>
            <button @click="activeTab = 'strategies'" :class="activeTab === 'strategies' ? 'active' : ''">
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
                Strategies
                <span v-if="betStore.mergeSuggestions.length > 0" class="ml-1 inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold leading-none rounded-full bg-amber-500/20 text-amber-400">{{ betStore.mergeSuggestions.length }}</span>
              </span>
            </button>
            <button @click="activeTab = 'archive'" :class="activeTab === 'archive' ? 'active' : ''">
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg>
                Archive
                <span v-if="archivedCount > 0" class="ml-1 inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold leading-none rounded-full bg-teal-500/20 text-teal-400">{{ archivedCount }}</span>
              </span>
            </button>
          </div>

          <!-- Right: Actions -->
          <div class="flex items-center gap-1.5">
            <button @click="navigateTo('referrals')" class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold text-white bg-emerald-500 hover:bg-emerald-400 rounded-lg shadow-sm transition-colors" title="Refer a friend">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12v10H4V12m16 0H4m16 0h-5m-6 0H4m5 0a3 3 0 116 0m-6 0a3 3 0 106 0m-3 0v10m0-10V7" /></svg>
              <span class="hidden md:inline">Refer & Earn £10</span>
            </button>
            <button @click="navigateTo('contact')" class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800/50 rounded-lg transition-colors" title="Contact / Help">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
              Help
            </button>
            <IngestData />
            <button @click="navigateTo('uploader')" class="hidden lg:flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800/50 rounded-lg transition-colors" title="Windows auto uploader">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
              Auto Uploader
            </button>
            <button @click="toggleDark" class="relative p-2 rounded-lg text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-all duration-200" :title="isDark ? 'Light Mode' : 'Dark Mode'">
              <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="rotate-90 opacity-0" enter-to-class="rotate-0 opacity-100" leave-active-class="transition duration-150 ease-in" leave-from-class="rotate-0 opacity-100" leave-to-class="-rotate-90 opacity-0" mode="out-in">
                <svg v-if="isDark" key="sun" class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                <svg v-else key="moon" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
              </Transition>
            </button>

            <!-- User menu -->
            <div class="relative user-menu-container">
              <button @click.stop="showUserMenu = !showUserMenu" class="flex items-center gap-2 p-1.5 pr-3 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">
                <div class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold" style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);">
                  {{ auth.displayName?.charAt(0)?.toUpperCase() || '?' }}
                </div>
                <span class="hidden sm:block text-sm font-medium text-gray-700 dark:text-gray-300 max-w-[120px] truncate">{{ auth.displayName }}</span>
                <svg class="w-4 h-4 text-gray-400 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
              </button>
              <Transition enter-active-class="transition ease-out duration-100" enter-from-class="opacity-0 scale-95" enter-to-class="opacity-100 scale-100" leave-active-class="transition ease-in duration-75" leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-95">
                <div v-if="showUserMenu" class="absolute right-0 mt-2 w-64 rounded-xl bg-white dark:bg-[#111827] border border-gray-200 dark:border-gray-800 shadow-xl dark:shadow-2xl dark:shadow-black/40 z-50 overflow-hidden">
                  <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                    <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ auth.user?.display_name }}</p>
                    <p class="text-xs text-gray-500 truncate">{{ auth.user?.email }}</p>
                    <div class="mt-1.5 flex items-center gap-1.5">
                      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold" :class="auth.hasActiveSubscription ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'">
                        {{ auth.hasActiveSubscription ? '● Active' : '○ No subscription' }}
                      </span>
                      <span v-if="auth.user?.subscription_plan" class="text-[10px] text-gray-600">{{ auth.user.subscription_plan === '12month' ? '12 mo' : '6 mo' }}</span>
                    </div>
                  </div>
                  <div class="py-1">
                    <button v-if="auth.user?.is_admin" @click="navigateTo('admin'); showUserMenu = false" class="w-full text-left px-4 py-2.5 text-sm text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 flex items-center gap-2 transition-colors">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                      Admin Dashboard
                    </button>
                    <button @click="navigateTo('account'); showUserMenu = false" class="w-full text-left px-4 py-2.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800/50 flex items-center gap-2 transition-colors">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                      Account Settings
                    </button>
                    <button @click="navigateTo('referrals'); showUserMenu = false" class="w-full text-left px-4 py-2.5 text-sm text-emerald-500 hover:text-emerald-400 hover:bg-emerald-500/10 flex items-center gap-2 transition-colors">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12v10H4V12m16 0H4m16 0h-5m-6 0H4m5 0a3 3 0 116 0m-6 0a3 3 0 106 0m-3 0v10m0-10V7" /></svg>
                      Referrals
                    </button>
                    <button @click="navigateTo('uploader'); showUserMenu = false" class="w-full text-left px-4 py-2.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800/50 flex items-center gap-2 transition-colors">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                      Windows Uploader
                    </button>
                    <button @click="showChangePassword = true; showUserMenu = false" class="w-full text-left px-4 py-2.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800/50 flex items-center gap-2 transition-colors">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
                      Change Password
                    </button>
                    <button @click="handleLogout" class="w-full text-left px-4 py-2.5 text-sm text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 flex items-center gap-2 transition-colors">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
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
      <div class="sm:hidden border-t border-gray-200 dark:border-gray-800/40 px-4 py-2">
        <div class="pill-nav w-full">
          <button @click="activeTab = 'dashboard'" :class="[activeTab === 'dashboard' ? 'active' : '', 'flex-1']">Dashboard</button>
          <button @click="activeTab = 'strategies'" :class="[activeTab === 'strategies' ? 'active' : '', 'flex-1']">
            Strategies
            <span v-if="betStore.mergeSuggestions.length > 0" class="ml-1 text-[10px] bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded-full">{{ betStore.mergeSuggestions.length }}</span>
          </button>
          <button @click="activeTab = 'archive'" :class="[activeTab === 'archive' ? 'active' : '', 'flex-1']">
            Archive
            <span v-if="archivedCount > 0" class="ml-1 text-[10px] bg-teal-500/20 text-teal-400 px-1.5 py-0.5 rounded-full">{{ archivedCount }}</span>
          </button>
        </div>
      </div>
    </nav>

    <!-- ═══════════ Main Content ═══════════ -->
    <main>
      <div v-if="activeTab === 'dashboard'" class="px-4 py-6 sm:px-6">
        <SummaryHeader />
        <div class="mt-6 flex flex-col lg:flex-row gap-6">
          <aside class="lg:flex-shrink-0 transition-all duration-300" :class="[
            sidebarOpen ? 'fixed inset-0 z-40 bg-black/60 backdrop-blur-sm' : 'hidden lg:block',
            desktopFilterOpen ? 'lg:w-72 xl:w-80' : 'lg:hidden'
          ]">
            <div v-if="sidebarOpen" class="absolute inset-0 lg:hidden" @click="sidebarOpen = false" />
            <div class="relative h-full lg:h-auto overflow-y-auto bg-gray-50 dark:bg-[#0b0f1a] lg:bg-transparent max-w-sm lg:max-w-none" :class="sidebarOpen ? 'p-4' : ''">
              <FilterPanel />
              <div class="mt-6">
                <StakingCalculator />
              </div>
            </div>
          </aside>
          <div class="min-w-0 flex-1 space-y-6">
            <StrategyStats />
            <Charts />
            <MonthlyPLTable />
            <OddsBandsChart />
            <AdvancedOddsCharts />
            <BetTable />
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'strategies'" class="px-4 py-6 sm:px-6">
        <StrategyManager />
      </div>

      <div v-else-if="activeTab === 'archive'" class="px-4 py-6 sm:px-6">
        <ArchivedStrategies />
      </div>
    </main>

    <!-- ═══════════ Footer ═══════════ -->
    <footer class="mt-12 border-t border-gray-200 dark:border-gray-800/40 bg-white/60 dark:bg-[#0b0f1a]/80">
      <div class="px-4 sm:px-6 py-5">
        <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div class="flex items-center gap-2 text-sm text-gray-400 dark:text-gray-600">
            <div class="w-5 h-5 rounded flex items-center justify-center" style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);">
              <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
            </div>
            <span class="text-gray-400 dark:text-gray-500">BFBM<span class="text-teal-600 dark:text-teal-500">Explorer</span></span>
          </div>
          <div class="flex items-center gap-4 text-xs text-gray-400 dark:text-gray-600 font-mono">
            <span>{{ betStore.summaryStats?.num_bets?.toLocaleString() || 0 }} bets</span>
            <span class="text-gray-300 dark:text-gray-700">•</span>
            <span>{{ betStore.strategyStats?.length || 0 }} strategies</span>
          </div>
        </div>
      </div>
    </footer>

    <!-- Scroll-to-top button -->
    <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 translate-y-4" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100 translate-y-0" leave-to-class="opacity-0 translate-y-4">
      <button v-if="showScrollTop" @click="scrollToTop" class="fixed bottom-6 right-6 z-50 p-3 rounded-full text-white shadow-lg shadow-teal-500/20 transition-colors hover:shadow-glow-teal" style="background: linear-gradient(135deg, #14b8a6, #0ea5e9);" aria-label="Scroll to top">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
      </button>
    </Transition>

    <!-- Loading progress bar -->
    <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0" enter-to-class="opacity-100" leave-active-class="transition duration-200" leave-from-class="opacity-100" leave-to-class="opacity-0">
      <div v-if="betStore.loading" class="fixed top-0 left-0 right-0 z-[60] h-0.5 bg-teal-900/30 overflow-hidden">
        <div class="h-full bg-gradient-to-r from-teal-500 to-sky-500 animate-progress-bar" />
      </div>
    </Transition>

    <!-- Initial dashboard loading overlay (first paint only) -->
    <LoadingOverlay
      :show="initialDashboardLoading"
      title="Loading your dashboard…"
      message="Fetching your bets, strategies and stats. This usually takes a few seconds."
    />

    <!-- ═══════════ Change Password Modal ═══════════ -->
    <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0" enter-to-class="opacity-100" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100" leave-to-class="opacity-0">
      <div v-if="showChangePassword" class="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showChangePassword = false; cpError = ''; cpSuccess = ''">
        <div class="glass-card w-full max-w-md mx-4 overflow-hidden">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800/60">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <svg class="w-5 h-5 text-teal-600 dark:text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
              Change Password
            </h3>
            <button @click="showChangePassword = false; cpError = ''; cpSuccess = ''" class="p-1.5 rounded-lg text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>

          <!-- Form -->
          <form @submit.prevent="handleChangePassword" class="p-6 space-y-4">
            <div v-if="cpError" class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">{{ cpError }}</div>
            <div v-if="cpSuccess" class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-400">{{ cpSuccess }}</div>

            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Current Password</label>
              <input v-model="cpCurrentPassword" type="password" required class="input-field" placeholder="Enter current password" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">New Password</label>
              <input v-model="cpNewPassword" type="password" required minlength="8" class="input-field" placeholder="Enter new password" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Confirm New Password</label>
              <input v-model="cpConfirm" type="password" required class="input-field" placeholder="Confirm new password" />
            </div>

            <div class="flex gap-3 pt-2">
              <button type="button" @click="showChangePassword = false; cpError = ''; cpSuccess = ''" class="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800/50 font-medium text-sm transition-colors">Cancel</button>
              <button type="submit" class="flex-1 btn-glow !py-2.5 text-sm">Update Password</button>
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
