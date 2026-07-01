<script setup lang="ts">
import { ref } from 'vue'

import { apiGet } from '../api/client'

interface OperationLogRead {
  id: number
  file_id: string
  operation_type: string
  before_path: string
  after_path: string
  status: string
  error_message: string
  reversible: boolean
  rolled_back: boolean
}

const executionId = ref('')
const logs = ref<OperationLogRead[]>([])
const loading = ref(false)
const message = ref('')

async function loadLogs() {
  if (!executionId.value) {
    message.value = '请输入执行 ID'
    return
  }

  loading.value = true
  message.value = ''
  try {
    logs.value = await apiGet<OperationLogRead[]>(`/api/executions/${executionId.value}/logs`)
    message.value = `已加载 ${logs.value.length} 条操作日志`
  } catch (error) {
    message.value = `加载日志失败：${(error as Error).message}`
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="logs-page">
    <header class="page-title">
      <div>
        <p class="eyebrow">任务日志</p>
        <h2>操作日志</h2>
        <p class="hint">输入执行 ID，查看本次整理的操作日志。</p>
      </div>
    </header>

    <div class="section-card">
      <header class="section-head">
        <div>
          <h3>执行记录</h3>
          <p class="hint">失败、删除和不可回滚操作需要重点检查。</p>
        </div>
      </header>

      <form class="toolbar" @submit.prevent="loadLogs">
        <label class="form-row">
          <span>执行 ID</span>
          <input v-model="executionId" required placeholder="例如：1" />
        </label>
        <button type="submit" :disabled="loading">{{ loading ? '加载中...' : '加载日志' }}</button>
      </form>

      <p v-if="message" class="message">{{ message }}</p>
      <p v-if="!loading && logs.length === 0" class="empty">暂无操作日志。</p>
      <div v-else class="table-shell">
        <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>操作</th>
            <th>原路径</th>
            <th>新路径</th>
            <th>状态</th>
            <th>可回滚</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id">
            <td>{{ log.id }}</td>
            <td>{{ log.operation_type }}</td>
            <td>{{ log.before_path }}</td>
            <td>{{ log.after_path }}</td>
            <td>{{ log.status }} {{ log.error_message }}</td>
            <td>{{ log.reversible && !log.rolled_back ? '是' : '否' }}</td>
          </tr>
        </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<style scoped>
.logs-page {
  display: grid;
  gap: 18px;
}

.page-header h2 {
  margin: 0;
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--blue);
  font-size: 12px;
  font-weight: 700;
}

.hint,
.empty {
  color: var(--muted);
}

.toolbar {
  display: flex;
  align-items: end;
  gap: 12px;
  margin: 16px 0;
}

.toolbar .form-row {
  min-width: 220px;
}

.message {
  margin: 12px 0;
  color: var(--green);
  font-weight: 600;
}

@media (max-width: 900px) {
  .toolbar {
    display: grid;
  }
}
</style>
