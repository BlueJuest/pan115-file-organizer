<script setup lang="ts">
import { ref } from 'vue'

import { apiSend } from '../api/client'

interface RollbackPlanItemRead {
  operation_log_id: number
  file_id: string
  current_path: string
  rollback_path: string
  reversible: boolean
}

interface RollbackPlanRead {
  execution_batch_id: number
  items: RollbackPlanItemRead[]
}

interface RollbackRead {
  id?: number
  success_count?: number
  failed_count?: number
  status?: string
}

const executionId = ref('')
const items = ref<RollbackPlanItemRead[]>([])
const planning = ref(false)
const rollingBack = ref(false)
const message = ref('')

async function buildPlan() {
  if (!executionId.value) {
    message.value = '请输入执行 ID'
    return
  }

  planning.value = true
  message.value = ''
  try {
    const result = await apiSend<RollbackPlanRead>(`/api/executions/${executionId.value}/rollback-plan`, 'POST')
    items.value = result.items
    message.value = `已生成 ${items.value.length} 条回滚计划`
  } catch (error) {
    message.value = `生成回滚计划失败：${(error as Error).message}`
  } finally {
    planning.value = false
  }
}

async function executeRollback() {
  if (!executionId.value) {
    message.value = '请输入执行 ID'
    return
  }

  if (!confirm(`确认回滚 ${items.value.length} 项？`)) return

  rollingBack.value = true
  message.value = ''
  try {
    const rollback = await apiSend<RollbackRead>(`/api/rollbacks/${executionId.value}`, 'POST')
    const success = rollback.success_count ?? 0
    const failed = rollback.failed_count ?? 0
    message.value = `回滚完成：成功 ${success}，失败 ${failed}`
  } catch (error) {
    message.value = `回滚失败：${(error as Error).message}`
  } finally {
    rollingBack.value = false
  }
}
</script>

<template>
  <section class="rollback-page">
    <div class="card">
      <header class="page-header">
        <div>
          <p class="eyebrow">Rollback</p>
          <h2>回滚记录</h2>
          <p class="hint">输入执行 ID，生成回滚计划并执行可逆操作。</p>
        </div>
      </header>

      <div class="risk-panel">
        <strong>回滚边界</strong>
        <p>只回滚本工具记录过的可逆操作。真实删除不会进入回滚计划。</p>
      </div>

      <form class="toolbar" @submit.prevent="buildPlan">
        <label class="form-row">
          <span>执行 ID</span>
          <input v-model="executionId" required placeholder="例如：1" />
        </label>
        <button type="submit" :disabled="planning">{{ planning ? '生成中...' : '生成回滚计划' }}</button>
        <button class="secondary" type="button" :disabled="rollingBack" @click="executeRollback">
          {{ rollingBack ? '回滚中...' : '执行回滚' }}
        </button>
      </form>

      <p v-if="message" class="message">{{ message }}</p>
      <p v-if="!planning && items.length === 0" class="empty">暂无回滚计划。</p>
      <table v-else>
        <thead>
          <tr>
            <th>文件</th>
            <th>当前路径</th>
            <th>回滚路径</th>
            <th>可回滚</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.operation_log_id">
            <td>{{ item.file_id }}</td>
            <td>{{ item.current_path }}</td>
            <td>{{ item.rollback_path }}</td>
            <td>{{ item.reversible ? '是' : '否' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.rollback-page {
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
  letter-spacing: 0.08em;
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

