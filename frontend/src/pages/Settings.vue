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
    message.value = `加载配置失败：${(error as Error).message}`
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  message.value = ''
  try {
    const settings = await apiSend<SettingsRead>('/api/settings', 'PUT', {
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
    })
    masked.pan115_cookie = settings.pan115_cookie_masked
    masked.tmdb_api_key = settings.tmdb_api_key_masked
    masked.telegram_bot_token = settings.telegram_bot_token_masked
    form.pan115_cookie = ''
    form.tmdb_api_key = ''
    form.telegram_bot_token = ''
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
    message.value = `连接测试失败：${(error as Error).message}`
  }
}

onMounted(loadSettings)
</script>

<template>
  <section class="settings-page">
    <header class="page-title">
      <div>
        <p class="eyebrow">系统配置</p>
        <h2>系统设置</h2>
        <p class="hint">管理 115、TMDB、Telegram 和默认目录。密钥输入框留空时会保留当前已保存的值。</p>
      </div>
      <button class="secondary" type="button" :disabled="loading" @click="loadSettings">重新加载</button>
    </header>

    <div class="risk-panel">
      <strong>真实操作模式</strong>
      <p>保存 115 Cookie 后，扫描和已确认的操作会读取真实 115 网盘；所有变更仍需先生成预览再确认执行。</p>
    </div>

    <form class="settings-form" @submit.prevent="saveSettings">
      <section class="section-card form-grid">
        <div class="section-head">
          <div>
            <h3>基础连接</h3>
            <p class="hint">配置 115 与 TMDB 访问凭据。</p>
          </div>
        </div>
        <label class="form-row">
          <span>115 Cookie</span>
          <input v-model="form.pan115_cookie" type="password" placeholder="输入新的 115 Cookie" autocomplete="off" />
          <small>当前：{{ masked.pan115_cookie || '未配置' }}</small>
        </label>
        <div class="two-columns">
          <label class="form-row">
            <span>TMDB API Key</span>
            <input v-model="form.tmdb_api_key" type="password" placeholder="输入新的 TMDB API Key" autocomplete="off" />
            <small>当前：{{ masked.tmdb_api_key || '未配置' }}</small>
          </label>
          <label class="form-row">
            <span>TMDB 语言</span>
            <input v-model="form.tmdb_language" placeholder="zh-CN" />
          </label>
        </div>
      </section>

      <section class="section-card form-grid">
        <div class="section-head">
          <div>
            <h3>投稿通知</h3>
            <p class="hint">配置 Telegram 推送和默认展示身份。</p>
          </div>
        </div>
        <div class="directory-grid">
          <label class="form-row">
            <span>Telegram bot token</span>
            <input v-model="form.telegram_bot_token" type="password" placeholder="输入新的 bot token" autocomplete="off" />
            <small>当前：{{ masked.telegram_bot_token || '未配置' }}</small>
          </label>
          <label class="form-row">
            <span>Telegram 频道 ID</span>
            <input v-model="form.telegram_channel_id" placeholder="@channel 或 -100..." />
          </label>
          <label class="form-row">
            <span>默认分享人</span>
            <input v-model="form.default_share_user" placeholder="发布者名称" />
          </label>
        </div>
      </section>

      <section class="section-card form-grid">
        <div class="section-head">
          <div>
            <h3>目录默认值</h3>
            <p class="hint">扫描、整理和回收操作的默认目录。</p>
          </div>
        </div>
        <div class="directory-grid">
          <DirectoryPicker v-model="form.default_source_dir" label="默认来源目录" placeholder="0" value-mode="id" />
          <DirectoryPicker v-model="form.default_target_dir" label="默认目标目录" placeholder="0" value-mode="id" />
          <DirectoryPicker v-model="form.default_recycle_dir" label="默认回收目录" placeholder="0" value-mode="id" />
        </div>
      </section>

      <section class="section-card form-grid">
        <div class="section-head">
          <div>
            <h3>执行策略</h3>
            <p class="hint">控制真实操作和默认扫描深度。</p>
          </div>
        </div>
        <label class="check-row">
          <input v-model="form.allow_delete_old_files" type="checkbox" />
          <span>允许删除旧文件</span>
        </label>
        <label class="check-row">
          <input v-model="form.recursive_scan" type="checkbox" />
          <span>默认递归扫描目录</span>
        </label>
      </section>

      <div class="section-card settings-actions">
        <div class="actions">
          <button type="submit" :disabled="saving">{{ saving ? '保存中...' : '保存配置' }}</button>
          <button class="secondary" type="button" @click="testConnection('115')">测试 115</button>
          <button class="secondary" type="button" @click="testConnection('tmdb')">测试 TMDB</button>
        </div>
        <p v-if="message" class="message">{{ message }}</p>
      </div>
    </form>
  </section>
</template>

<style scoped>
.settings-page,
.settings-form,
.settings-actions {
  display: grid;
  gap: 18px;
}

.check-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.check-row input {
  width: auto;
}
</style>
