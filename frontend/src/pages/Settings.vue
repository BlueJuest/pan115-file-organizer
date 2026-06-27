<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import { apiGet, apiSend } from '../api/client'
import DirectoryPicker from '../components/DirectoryPicker.vue'
import type { SettingsRead } from '../api/types'

type SettingsForm = Omit<SettingsRead, 'id' | 'pan115_cookie_masked' | 'tmdb_api_key_masked' | 'telegram_bot_token_masked'> & {
  pan115_cookie: string
  tmdb_api_key: string
  telegram_bot_token: string
}

interface TestResult {
  ok: boolean
  message: string
}

const form = reactive<SettingsForm>({
  pan115_cookie: '',
  tmdb_api_key: '',
  telegram_bot_token: '',
  tmdb_language: 'zh-CN',
  telegram_channel_id: '',
  default_share_user: '',
  default_source_dir: '0',
  default_target_dir: '0',
  default_recycle_dir: '0',
  allow_delete_old_files: false,
  recursive_scan: true,
})

const masked = reactive({
  pan115_cookie: '',
  tmdb_api_key: '',
  telegram_bot_token: '',
})

const loading = ref(false)
const saving = ref(false)
const message = ref('')

async function loadSettings() {
  loading.value = true
  message.value = ''
  try {
    const settings = await apiGet<SettingsRead>('/api/settings')
    masked.pan115_cookie = settings.pan115_cookie_masked
    masked.tmdb_api_key = settings.tmdb_api_key_masked
    masked.telegram_bot_token = settings.telegram_bot_token_masked
    form.telegram_channel_id = settings.telegram_channel_id
    form.default_share_user = settings.default_share_user
    form.tmdb_language = settings.tmdb_language
    form.default_source_dir = settings.default_source_dir
    form.default_target_dir = settings.default_target_dir
    form.default_recycle_dir = settings.default_recycle_dir
    form.allow_delete_old_files = settings.allow_delete_old_files
    form.recursive_scan = settings.recursive_scan
  } catch (error) {
    message.value = `Failed to load settings: ${(error as Error).message}`
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  message.value = ''
  try {
    const payload = {
      pan115_cookie: form.pan115_cookie,
      tmdb_api_key: form.tmdb_api_key,
      tmdb_language: form.tmdb_language,
      telegram_bot_token: form.telegram_bot_token,
      telegram_channel_id: form.telegram_channel_id,
      default_share_user: form.default_share_user,
      default_source_dir: form.default_source_dir,
      default_target_dir: form.default_target_dir,
      default_recycle_dir: form.default_recycle_dir,
      allow_delete_old_files: form.allow_delete_old_files,
      recursive_scan: form.recursive_scan,
    }
    const settings = await apiSend<SettingsRead>('/api/settings', 'PUT', payload)
    masked.pan115_cookie = settings.pan115_cookie_masked
    masked.tmdb_api_key = settings.tmdb_api_key_masked
    masked.telegram_bot_token = settings.telegram_bot_token_masked
    form.pan115_cookie = ''
    form.tmdb_api_key = ''
    form.telegram_bot_token = ''
    message.value = 'Settings saved'
  } catch (error) {
    message.value = `Failed to save settings: ${(error as Error).message}`
  } finally {
    saving.value = false
  }
}

async function testConnection(kind: '115' | 'tmdb') {
  message.value = ''
  const url = kind === '115' ? '/api/settings/test-115' : '/api/settings/test-tmdb'
  try {
    const result = await apiSend<TestResult>(url, 'POST')
    message.value = result.message
  } catch (error) {
    message.value = `Connection test failed: ${(error as Error).message}`
  }
}

onMounted(loadSettings)
</script>

<template>
  <section class="card settings-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Settings</p>
        <h2>System settings</h2>
        <p class="hint">Manage 115, TMDB, and default directory values. Empty secret fields keep the current saved value.</p>
      </div>
      <button class="secondary" type="button" :disabled="loading" @click="loadSettings">Reload</button>
    </header>

    <div class="risk-panel">
      <strong>Real operation mode</strong>
      <p>After saving a 115 Cookie, scans and confirmed operations read from your real 115 drive. Preview remains required before changes run.</p>
    </div>

    <form class="form-grid" @submit.prevent="saveSettings">
      <label class="form-row">
        <span>115 Cookie</span>
        <input v-model="form.pan115_cookie" type="password" placeholder="Enter a new 115 Cookie" autocomplete="off" />
        <small>Current: {{ masked.pan115_cookie || 'Not configured' }}</small>
      </label>

      <label class="form-row">
        <span>TMDB API Key</span>
        <input v-model="form.tmdb_api_key" type="password" placeholder="Enter a new TMDB API Key" autocomplete="off" />
        <small>Current: {{ masked.tmdb_api_key || 'Not configured' }}</small>
      </label>

      <label class="form-row">
        <span>TMDB language</span>
        <input v-model="form.tmdb_language" placeholder="zh-CN" />
      </label>

      <div class="directory-grid">
        <label class="form-row">
          <span>Telegram bot token</span>
          <input v-model="form.telegram_bot_token" type="password" placeholder="Enter a new bot token" autocomplete="off" />
          <small>Current: {{ masked.telegram_bot_token || 'Not configured' }}</small>
        </label>
        <label class="form-row">
          <span>Telegram channel ID</span>
          <input v-model="form.telegram_channel_id" placeholder="@channel or -100..." />
        </label>
        <label class="form-row">
          <span>Default share user</span>
          <input v-model="form.default_share_user" placeholder="Uploader name" />
        </label>
      </div>

      <div class="directory-grid">
        <DirectoryPicker v-model="form.default_source_dir" label="Default source directory" placeholder="0" value-mode="id" />
        <DirectoryPicker v-model="form.default_target_dir" label="Default target directory" placeholder="0" value-mode="id" />
        <DirectoryPicker v-model="form.default_recycle_dir" label="Default recycle directory" placeholder="0" value-mode="id" />
      </div>

      <label class="check-row">
        <input v-model="form.allow_delete_old_files" type="checkbox" />
        <span>Allow deleting old files</span>
      </label>

      <label class="check-row">
        <input v-model="form.recursive_scan" type="checkbox" />
        <span>Scan directories recursively by default</span>
      </label>

      <div class="actions">
        <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save settings' }}</button>
        <button class="secondary" type="button" @click="testConnection('115')">Test 115</button>
        <button class="secondary" type="button" @click="testConnection('tmdb')">Test TMDB</button>
      </div>

      <p v-if="message" class="message">{{ message }}</p>
    </form>
  </section>
</template>

<style scoped>
.settings-page {
  display: grid;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-header h2 {
  margin: 0;
}

.eyebrow {
  margin: 0 0 4px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hint,
small {
  color: #64748b;
}

.directory-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.check-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.check-row input {
  width: auto;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.message {
  margin: 0;
  color: #0f766e;
  font-weight: 600;
}

@media (max-width: 900px) {
  .directory-grid {
    grid-template-columns: 1fr;
  }
}
</style>
