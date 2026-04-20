<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getAdminStats, getAdminUsers, getAdminIngestionLogs, toggleUserActive, unlockUser } from '../services/api'

const emit = defineEmits<{ (e: 'navigate', page: string): void }>()

// ─── State ───────────────────────────────────────────────────────────────────
const activeTab = ref<'overview' | 'users' | 'logs'>('overview')
const loading = ref(false)
const error = ref('')

// Overview
const stats = ref<any>(null)

// Users
const users = ref<any[]>([])
const usersTotal = ref(0)
const usersPage = ref(1)
const usersSearch = ref('')
const usersSort = ref('created_at')
const usersSortOrder = ref('desc')
const usersPerPage = 25

// Ingestion logs
const logs = ref<any[]>([])
const logsTotal = ref(0)
const logsPage = ref(1)
const logsStatusFilter = ref('')
const expandedLogId = ref<number | null>(null)

// ─── Loaders ─────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    stats.value = await getAdminStats()
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to load stats'
  }
}

async function loadUsers() {
  loading.value = true
  try {
    const data = await getAdminUsers({
      page: usersPage.value,
      per_page: usersPerPage,
      search: usersSearch.value || undefined,
      sort: usersSort.value,
      order: usersSortOrder.value,
    })
    users.value = data.users
    usersTotal.value = data.total
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to load users'
  } finally {
    loading.value = false
  }
}

async function loadLogs() {
  loading.value = true
  try {
    const data = await getAdminIngestionLogs({
      page: logsPage.value,
      per_page: 50,
      status: logsStatusFilter.value || undefined,
    })
    logs.value = data.logs
    logsTotal.value = data.total
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to load logs'
  } finally {
    loading.value = false
  }
}

// ─── Actions ─────────────────────────────────────────────────────────────────
async function handleToggleActive(userId: number) {
  try {
    const result = await toggleUserActive(userId)
    const u = users.value.find((u: any) => u.id === userId)
    if (u) u.is_active = result.is_active
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Action failed'
  }
}

async function handleUnlock(userId: number) {
  try {
    await unlockUser(userId)
    const u = users.value.find((u: any) => u.id === userId)
    if (u) {
      u.locked_until = null
      u.failed_login_attempts = 0
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Action failed'
  }
}

function sortUsers(col: string) {
  if (usersSort.value === col) {
    usersSortOrder.value = usersSortOrder.value === 'desc' ? 'asc' : 'desc'
  } else {
    usersSort.value = col
    usersSortOrder.value = 'desc'
  }
  usersPage.value = 1
  loadUsers()
}

let searchTimeout: ReturnType<typeof setTimeout>
function onSearchInput() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    usersPage.value = 1
    loadUsers()
  }, 300)
}

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const usersTotalPages = computed(() => Math.ceil(usersTotal.value / usersPerPage))
const logsTotalPages = computed(() => Math.ceil(logsTotal.value / 50))

// ─── Init ────────────────────────────────────────────────────────────────────
onMounted(async () => {
  await loadStats()
  await loadUsers()
  await loadLogs()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-[#0b0f1a] text-gray-800 dark:text-gray-200">
    <!-- Top bar -->
    <nav class="sticky top-0 z-50 bg-white/80 dark:bg-[#0b0f1a]/80 backdrop-blur-2xl border-b border-gray-200 dark:border-gray-800/40">
      <div class="px-4 sm:px-6">
        <div class="flex h-14 items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background: linear-gradient(135deg, #ef4444, #f97316);">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900 dark:text-white leading-tight">Admin <span class="text-rose-500">Dashboard</span></h1>
              <p class="text-[10px] text-gray-400 dark:text-gray-500 font-medium font-mono -mt-0.5">Platform Management</p>
            </div>
          </div>
          <button @click="emit('navigate', 'dashboard')" class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">
            ← Back to Dashboard
          </button>
        </div>
      </div>
    </nav>

    <!-- Error banner -->
    <div v-if="error" class="mx-4 sm:mx-6 mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400 flex items-center justify-between">
      {{ error }}
      <button @click="error = ''" class="ml-2 text-rose-300 hover:text-rose-200">✕</button>
    </div>

    <!-- Tab nav -->
    <div class="px-4 sm:px-6 pt-4">
      <div class="inline-flex rounded-xl bg-white dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 p-1 gap-1">
        <button v-for="tab in (['overview', 'users', 'logs'] as const)" :key="tab"
          @click="activeTab = tab"
          :class="[
            'px-4 py-2 text-sm font-medium rounded-lg transition-all',
            activeTab === tab
              ? 'bg-gradient-to-r from-rose-500 to-orange-500 text-white shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
          ]">
          {{ tab === 'overview' ? '📊 Overview' : tab === 'users' ? '👥 Users' : '📋 Ingestion Logs' }}
        </button>
      </div>
    </div>

    <main class="px-4 sm:px-6 py-6">
      <!-- ═══════ Overview Tab ═══════ -->
      <div v-if="activeTab === 'overview' && stats" class="space-y-6">
        <!-- Stat cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="glass-card p-4">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Users</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ stats.total_users }}</p>
            <p class="text-xs text-teal-500 mt-1">+{{ stats.new_users_7d }} this week</p>
          </div>
          <div class="glass-card p-4">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Active Subscribers</p>
            <p class="text-2xl font-bold text-emerald-500 mt-1">{{ stats.active_subscribers }}</p>
            <p class="text-xs text-gray-400 mt-1">{{ stats.total_users ? ((stats.active_subscribers / stats.total_users) * 100).toFixed(0) : 0 }}% conversion</p>
          </div>
          <div class="glass-card p-4">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Bets</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ stats.total_bets?.toLocaleString() }}</p>
            <p class="text-xs text-gray-400 mt-1">across all users</p>
          </div>
          <div class="glass-card p-4">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Failed Uploads</p>
            <p class="text-2xl font-bold" :class="stats.failed_ingestions > 0 ? 'text-rose-500' : 'text-gray-900 dark:text-white'">{{ stats.failed_ingestions }}</p>
            <p class="text-xs text-gray-400 mt-1">of {{ stats.total_ingestions }} total</p>
          </div>
        </div>

        <!-- Second row -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="glass-card p-4">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">New Users (30 days)</p>
            <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ stats.new_users_30d }}</p>
          </div>
          <div class="glass-card p-4">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Subscription Breakdown</p>
            <div class="space-y-2">
              <div v-for="(count, status) in stats.subscription_breakdown" :key="status" class="flex items-center justify-between">
                <span class="text-sm capitalize" :class="{
                  'text-emerald-400': status === 'active',
                  'text-gray-400': status === 'inactive',
                  'text-amber-400': status === 'cancelled',
                  'text-rose-400': status === 'expired',
                }">{{ status || 'inactive' }}</span>
                <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══════ Users Tab ═══════ -->
      <div v-if="activeTab === 'users'" class="space-y-4">
        <!-- Search bar -->
        <div class="flex items-center gap-3">
          <div class="relative flex-1 max-w-md">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            <input v-model="usersSearch" @input="onSearchInput" type="text" placeholder="Search by email or name..."
              class="w-full pl-10 pr-4 py-2 rounded-xl bg-white dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500/50" />
          </div>
          <span class="text-sm text-gray-400">{{ usersTotal }} users</span>
        </div>

        <!-- Users table -->
        <div class="glass-card overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-800/60 text-left">
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200" @click="sortUsers('email')">
                    Email {{ usersSort === 'email' ? (usersSortOrder === 'desc' ? '↓' : '↑') : '' }}
                  </th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Name</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200" @click="sortUsers('subscription_status')">
                    Subscription {{ usersSort === 'subscription_status' ? (usersSortOrder === 'desc' ? '↓' : '↑') : '' }}
                  </th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200 text-right" @click="sortUsers('bet_count')">
                    Bets {{ usersSort === 'bet_count' ? (usersSortOrder === 'desc' ? '↓' : '↑') : '' }}
                  </th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200" @click="sortUsers('created_at')">
                    Joined {{ usersSort === 'created_at' ? (usersSortOrder === 'desc' ? '↓' : '↑') : '' }}
                  </th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Status</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id" class="border-b border-gray-100 dark:border-gray-800/30 hover:bg-gray-50 dark:hover:bg-gray-800/20 transition-colors">
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                      <span v-if="u.is_admin" class="text-[10px] px-1.5 py-0.5 rounded-full bg-rose-500/20 text-rose-400 font-semibold">ADMIN</span>
                      <span class="font-medium text-gray-900 dark:text-white">{{ u.email }}</span>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-gray-500 dark:text-gray-400">{{ u.display_name || '—' }}</td>
                  <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold" :class="{
                      'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': u.subscription_status === 'active',
                      'bg-gray-500/10 text-gray-400 border border-gray-500/20': u.subscription_status === 'inactive',
                      'bg-amber-500/10 text-amber-400 border border-amber-500/20': u.subscription_status === 'cancelled',
                      'bg-rose-500/10 text-rose-400 border border-rose-500/20': u.subscription_status === 'expired',
                    }">{{ u.subscription_status }}</span>
                    <span v-if="u.subscription_plan" class="ml-1 text-xs text-gray-400">{{ u.subscription_plan }}</span>
                  </td>
                  <td class="px-4 py-3 text-right font-mono text-gray-900 dark:text-white">{{ u.bet_count.toLocaleString() }}</td>
                  <td class="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs">{{ formatDate(u.created_at) }}</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-1.5">
                      <span v-if="!u.is_active" class="text-xs px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400">Disabled</span>
                      <span v-if="u.locked_until" class="text-xs px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">Locked</span>
                      <span v-if="u.is_active && !u.locked_until" class="text-xs px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">Active</span>
                    </div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-1">
                      <button v-if="!u.is_admin" @click="handleToggleActive(u.id)"
                        :title="u.is_active ? 'Disable user' : 'Enable user'"
                        class="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">
                        <svg v-if="u.is_active" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>
                        <svg v-else class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      </button>
                      <button v-if="u.locked_until" @click="handleUnlock(u.id)" title="Unlock account"
                        class="p-1.5 rounded-lg text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 transition-colors">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" /></svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- Pagination -->
          <div v-if="usersTotalPages > 1" class="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-800/40">
            <button @click="usersPage = Math.max(1, usersPage - 1); loadUsers()" :disabled="usersPage <= 1"
              class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">← Prev</button>
            <span class="text-sm text-gray-400">Page {{ usersPage }} of {{ usersTotalPages }}</span>
            <button @click="usersPage = Math.min(usersTotalPages, usersPage + 1); loadUsers()" :disabled="usersPage >= usersTotalPages"
              class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">Next →</button>
          </div>
        </div>
      </div>

      <!-- ═══════ Ingestion Logs Tab ═══════ -->
      <div v-if="activeTab === 'logs'" class="space-y-4">
        <!-- Filter -->
        <div class="flex items-center gap-3">
          <select v-model="logsStatusFilter" @change="logsPage = 1; loadLogs()"
            class="px-3 py-2 rounded-xl bg-white dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30">
            <option value="">All statuses</option>
            <option value="success">✅ Success</option>
            <option value="partial">⚠️ Partial (warnings)</option>
            <option value="error">❌ Error</option>
          </select>
          <span class="text-sm text-gray-400">{{ logsTotal }} records</span>
        </div>

        <!-- Logs table -->
        <div class="glass-card overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-800/60 text-left">
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Time</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">User</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">File</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Status</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400 text-right">Rows</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400 text-right">Inserted</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400 text-right">Updated</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400 text-right">Skipped</th>
                  <th class="px-4 py-3 font-medium text-gray-500 dark:text-gray-400"></th>
                </tr>
              </thead>
              <tbody>
                <template v-for="log in logs" :key="log.id">
                  <tr class="border-b border-gray-100 dark:border-gray-800/30 hover:bg-gray-50 dark:hover:bg-gray-800/20 transition-colors cursor-pointer"
                    @click="expandedLogId = expandedLogId === log.id ? null : log.id">
                    <td class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">{{ formatDate(log.created_at) }}</td>
                    <td class="px-4 py-3">
                      <div class="text-gray-900 dark:text-white text-xs">{{ log.user_display_name || log.user_email }}</div>
                      <div class="text-[10px] text-gray-400">{{ log.user_email }}</div>
                    </td>
                    <td class="px-4 py-3 text-gray-500 dark:text-gray-400 max-w-[200px] truncate" :title="log.filename">{{ log.filename }}</td>
                    <td class="px-4 py-3">
                      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold" :class="{
                        'bg-emerald-500/10 text-emerald-400': log.status === 'success',
                        'bg-amber-500/10 text-amber-400': log.status === 'partial',
                        'bg-rose-500/10 text-rose-400': log.status === 'error',
                      }">{{ log.status === 'success' ? '✅' : log.status === 'partial' ? '⚠️' : '❌' }} {{ log.status }}</span>
                    </td>
                    <td class="px-4 py-3 text-right font-mono">{{ log.rows_total?.toLocaleString() }}</td>
                    <td class="px-4 py-3 text-right font-mono text-emerald-400">{{ log.rows_inserted?.toLocaleString() }}</td>
                    <td class="px-4 py-3 text-right font-mono text-sky-400">{{ log.rows_updated?.toLocaleString() }}</td>
                    <td class="px-4 py-3 text-right font-mono text-gray-400">{{ log.rows_skipped?.toLocaleString() }}</td>
                    <td class="px-4 py-3 text-gray-400">
                      <svg class="w-4 h-4 transition-transform" :class="expandedLogId === log.id ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                    </td>
                  </tr>
                  <!-- Expanded detail row -->
                  <tr v-if="expandedLogId === log.id">
                    <td colspan="9" class="px-4 py-3 bg-gray-50 dark:bg-gray-900/30">
                      <div v-if="log.error_message" class="mb-2">
                        <span class="text-xs font-semibold text-rose-400">Error: </span>
                        <span class="text-xs text-rose-300 font-mono">{{ log.error_message }}</span>
                      </div>
                      <div v-if="log.warnings && log.warnings.length">
                        <span class="text-xs font-semibold text-amber-400">Warnings ({{ log.warnings.length }}):</span>
                        <ul class="mt-1 space-y-0.5">
                          <li v-for="(w, i) in log.warnings.slice(0, 20)" :key="i" class="text-xs text-amber-300/80 font-mono pl-3">• {{ w }}</li>
                          <li v-if="log.warnings.length > 20" class="text-xs text-gray-400 pl-3">… and {{ log.warnings.length - 20 }} more</li>
                        </ul>
                      </div>
                      <div v-if="!log.error_message && (!log.warnings || !log.warnings.length)" class="text-xs text-gray-400">No issues — clean upload.</div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
          <!-- Pagination -->
          <div v-if="logsTotalPages > 1" class="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-800/40">
            <button @click="logsPage = Math.max(1, logsPage - 1); loadLogs()" :disabled="logsPage <= 1"
              class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">← Prev</button>
            <span class="text-sm text-gray-400">Page {{ logsPage }} of {{ logsTotalPages }}</span>
            <button @click="logsPage = Math.min(logsTotalPages, logsPage + 1); loadLogs()" :disabled="logsPage >= logsTotalPages"
              class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors">Next →</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
