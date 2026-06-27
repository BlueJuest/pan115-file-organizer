<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import { apiGet, apiSend } from '../api/client'
import type { SettingsRead } from '../api/types'

type SettingsForm = Omit<SettingsRead, 'id' | 'pan115_cookie_masked' | 'tmdb_api_key_masked'> & {
  pan115_cookie: string
  tmdb_api_key: string
}

interface TestResult {
  ok: boolean
  message: string
}

const form = reactive<SettingsForm>({
  pan115_cookie: '',
  tmdb_api_key: '',
  tmdb_language: 'zh-CN',
  default_source_dir: '0',
  default_target_dir: '0',
  default_recycle_dir: '0',
  allow_delete_old_files: false,
  recursive_scan: true,
})

const masked = reactive({
  pan115_cookie: '',
  tmdb_api_key: '',
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
    form.tmdb_language = settings.tmdb_language
    form.default_source_dir = settings.default_source_dir
    form.default_target_dir = settings.default_target_dir
    form.default_recycle_dir = settings.default_recycle_dir
    form.allow_delete_old_files = settings.allow_delete_old_files
    form.recursive_scan = settings.recursive_scan
  } catch (error) {
    message.value = `加载配置失败：${(error as Error).message}`
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  message.value = ''
  try {
    const payload = { ...form }
    const settings = await apiSend<SettingsRead>('/api/settings', 'PUT', payload)
    masked.pan115_cookie = settings.pan115_cookie_masked
    masked.tmdb_api_key = settings.tmdb_api_key_masked
    form.pan115_cookie = ''
    form.tmdb_api_key = ''
    message.value = '配置已保存'
  } catch (error) {
    message.value = `保存配置失败：${(error as Error).message}`
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
    message.value = `测试连接失败：${(error as Error).message}`
  }
}

onMounted(loadSettings)
</script>

<template>
  <section class="card settings-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Settings</p>
        <h2>系统配置</h2>
        <p class="hint">维护 115、TMDB 与默认目录参数。留空密钥输入框可保留现有密钥。</p>
      </div>
      <button class="secondary" type="button" :disabled="loading" @click="loadSettings">重新加载</button>
    </header>

    <div class="risk-panel">
      <strong>真实操作模式</strong>
      <p>保存 115 Cookie 后，扫描、改名、移动和删除会作用于真实 115 网盘。请确认 Cookie 来源可信。</p>
    </div>

    <form class="form-grid" @submit.prevent="saveSettings">
      <label class="form-row">
        <span>115 Cookie</span>
        <input v-model="form.pan115_cookie" type="password" placeholder="输入新的 115 Cookie" autocomplete="off" />
        <small>当前：{{ masked.pan115_cookie || '未配置' }}</small>
      </label>

      <label class="form-row">
        <span>TMDB API Key</span>
        <input v-model="form.tmdb_api_key" type="password" placeholder="输入新的 TMDB API Key" autocomplete="off" />
        <small>当前：{{ masked.tmdb_api_key || '未配置' }}</small>
      </label>

      <label class="form-row">
        <span>TMDB 语言</span>
        <input v-model="form.tmdb_language" placeholder="zh-CN" />
      </label>

      <div class="directory-grid">
        <label class="form-row">
          <span>默认源目录 ID</span>
          <input v-model="form.default_source_dir" placeholder="0" />
        </label>
        <label class="form-row">
          <span>默认目标目录 ID</span>
          <input v-model="form.default_target_dir" placeholder="0" />
        </label>
        <label class="form-row">
          <span>默认回收目录 ID</span>
          <input v-model="form.default_recycle_dir" placeholder="0" />
        </label>
      </div>

      <label class="check-row">
        <input v-model="form.allow_delete_old_files" type="checkbox" />
        <span>允许删除旧文件</span>
      </label>

      <label class="check-row">
        <input v-model="form.recursive_scan" type="checkbox" />
        <span>递归扫描目录</span>
      </label>

      <div class="actions">
        <button type="submit" :disabled="saving">{{ saving ? '保存中...' : '保存配置' }}</button>
        <button class="secondary" type="button" @click="testConnection('115')">测试 115 连接</button>
        <button class="secondary" type="button" @click="testConnection('tmdb')">测试 TMDB 连接</button>
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
