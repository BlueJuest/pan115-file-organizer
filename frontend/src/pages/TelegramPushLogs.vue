<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { apiGet, apiSend } from '../api/client'
import type { SubmissionPublishResponse, TelegramPushLogList, TelegramPushLogRead } from '../api/types'

const filters = reactive({
  status: '',
  keyword: '',
  channel_id: '',
  start_at: '',
  end_at: '',
})

const logs = ref<TelegramPushLogRead[]>([])
const total = ref(0)
const loading = ref(false)
const message = ref('')
const selected = ref<TelegramPushLogRead | null>(null)

const statusText: Record<string, string> = {
  success: '成功',
  failed: '失败',
  pending: '处理中',
}

const query = computed(() => {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  return params.toString()
})

async function loadLogs() {
  loading.value = true
  message.value = ''
  try {
    const suffix = query.value ? `?${query.value}` : ''
    const result = await apiGet<TelegramPushLogList>(`/api/telegram-push-logs${suffix}`)
    logs.value = result.items
    total.value = result.total
  } catch (error) {
    message.value = `加载推送记录失败：${(error as Error).message}`
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.status = ''
  filters.keyword = ''
  filters.channel_id = ''
  filters.start_at = ''
  filters.end_at = ''
  void loadLogs()
}

async function copyCaption(log: TelegramPushLogRead) {
  await navigator.clipboard.writeText(log.caption)
  message.value = '推送文案已复制'
}

async function resend(log: TelegramPushLogRead) {
  if (!window.confirm('确定要按历史内容重新推送吗？')) return
  loading.value = true
  message.value = ''
  try {
    const result = await apiSend<SubmissionPublishResponse>(`/api/telegram-push-logs/${log.id}/resend`, 'POST')
    message.value = result.telegram_message_id
      ? `${result.message}，消息 ID：${result.telegram_message_id}`
      : result.message
    await loadLogs()
  } catch (error) {
    message.value = `重新推送失败：${(error as Error).message}`
  } finally {
    loading.value = false
  }
}

async function remove(log: TelegramPushLogRead) {
  if (!window.confirm('只会删除本地记录，不会删除 Telegram 频道消息。确定删除吗？')) return
  loading.value = true
  message.value = ''
  try {
    await apiSend(`/api/telegram-push-logs/${log.id}`, 'DELETE')
    message.value = '本地推送记录已删除'
    if (selected.value?.id === log.id) selected.value = null
    await loadLogs()
  } catch (error) {
    message.value = `删除失败：${(error as Error).message}`
  } finally {
    loading.value = false
  }
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

onMounted(loadLogs)
</script>

<template>
  <section class="telegram-log-page">
    <div class="card">
      <header class="page-header">
        <div>
          <p class="eyebrow">Telegram 推送</p>
          <h2>推送记录</h2>
          <p class="hint">查看每次 Telegram 推送的内容、状态和失败原因，并可按历史内容重新推送。</p>
        </div>
        <button type="button" :disabled="loading" @click="loadLogs">刷新</button>
      </header>

      <form class="filters" @submit.prevent="loadLogs">
        <label class="form-row">
          <span>状态</span>
          <select v-model="filters.status">
            <option value="">全部</option>
            <option value="success">成功</option>
            <option value="failed">失败</option>
            <option value="pending">处理中</option>
          </select>
        </label>
        <label class="form-row">
          <span>关键词</span>
          <input v-model="filters.keyword" placeholder="标题、正文、链接或错误" />
        </label>
        <label class="form-row">
          <span>频道 ID</span>
          <input v-model="filters.channel_id" placeholder="@channel 或 -100..." />
        </label>
        <label class="form-row">
          <span>开始时间</span>
          <input v-model="filters.start_at" type="datetime-local" />
        </label>
        <label class="form-row">
          <span>结束时间</span>
          <input v-model="filters.end_at" type="datetime-local" />
        </label>
        <div class="filter-actions">
          <button type="submit" :disabled="loading">筛选</button>
          <button class="secondary" type="button" :disabled="loading" @click="resetFilters">重置</button>
        </div>
      </form>

      <p v-if="message" class="message">{{ message }}</p>
      <p class="summary">共 {{ total }} 条记录</p>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>时间</th>
              <th>标题</th>
              <th>频道</th>
              <th>状态</th>
              <th>消息 ID</th>
              <th>失败原因</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.id">
              <td>{{ formatDate(log.created_at) }}</td>
              <td>{{ log.title || '未识别标题' }}</td>
              <td>{{ log.telegram_channel_id || '-' }}</td>
              <td>
                <span :class="['status-badge', log.status]">{{ statusText[log.status] || log.status }}</span>
              </td>
              <td>{{ log.telegram_message_id || '-' }}</td>
              <td class="error-cell">{{ log.error_message || '-' }}</td>
              <td>
                <div class="row-actions">
                  <button class="secondary" type="button" @click="selected = log">详情</button>
                  <button class="secondary" type="button" @click="copyCaption(log)">复制</button>
                  <button type="button" @click="resend(log)">重推</button>
                  <button class="danger" type="button" @click="remove(log)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="!loading && logs.length === 0" class="empty">暂无推送记录。</p>
    </div>

    <div v-if="selected" class="modal-backdrop" @click.self="selected = null">
      <article class="modal-card">
        <header class="modal-header">
          <div>
            <p class="eyebrow">记录详情</p>
            <h3>{{ selected.title || `记录 #${selected.id}` }}</h3>
          </div>
          <button class="secondary" type="button" @click="selected = null">关闭</button>
        </header>
        <dl class="detail-list">
          <div><dt>状态</dt><dd>{{ statusText[selected.status] || selected.status }}</dd></div>
          <div><dt>频道 ID</dt><dd>{{ selected.telegram_channel_id || '-' }}</dd></div>
          <div><dt>消息 ID</dt><dd>{{ selected.telegram_message_id || '-' }}</dd></div>
          <div><dt>图片地址</dt><dd>{{ selected.image_url || '-' }}</dd></div>
          <div><dt>分享链接</dt><dd>{{ selected.share_url || '-' }}</dd></div>
          <div><dt>来源记录</dt><dd>{{ selected.resent_from_id || '-' }}</dd></div>
          <div><dt>失败原因</dt><dd>{{ selected.error_message || '-' }}</dd></div>
        </dl>
        <label class="form-row">
          <span>推送文案</span>
          <textarea readonly rows="12" :value="selected.caption" />
        </label>
        <label class="form-row">
          <span>Telegram 返回摘要</span>
          <textarea readonly rows="3" :value="selected.response_payload || '-'" />
        </label>
      </article>
    </div>
  </section>
</template>

<style scoped>
.telegram-log-page {
  display: grid;
  gap: 18px;
}

.page-header,
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-header h2,
.modal-header h3 {
  margin: 0;
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--blue);
  font-size: 12px;
  font-weight: 700;
}

.hint,
.summary,
.empty {
  color: var(--muted);
}

.filters {
  display: grid;
  grid-template-columns: repeat(5, minmax(140px, 1fr)) auto;
  gap: 12px;
  align-items: end;
  margin: 18px 0 12px;
}

.filter-actions,
.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.message {
  color: var(--green);
  font-weight: 700;
}

.table-wrap {
  overflow-x: auto;
}

.status-badge {
  display: inline-flex;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 12px;
  font-weight: 700;
}

.status-badge.success {
  background: var(--green-soft);
  color: var(--green);
}

.status-badge.failed {
  background: var(--red-soft);
  color: var(--red);
}

.status-badge.pending {
  background: var(--blue-soft);
  color: var(--blue);
}

.error-cell {
  max-width: 260px;
  color: var(--red);
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgb(15 23 42 / 50%);
  z-index: 20;
}

.modal-card {
  display: grid;
  gap: 16px;
  width: min(920px, 100%);
  max-height: calc(100vh - 48px);
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  padding: 18px;
}

.detail-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 18px;
  margin: 0;
}

.detail-list dt {
  color: var(--muted);
  font-size: 12px;
}

.detail-list dd {
  margin: 4px 0 0;
  word-break: break-all;
}

@media (max-width: 1100px) {
  .filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .filters,
  .detail-list {
    grid-template-columns: 1fr;
  }
}
</style>

