<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { apiGet, apiSend } from '../api/client'
import type { ExecutionRead, PreviewItemRead } from '../api/types'

const route = useRoute()
const scanId = ref(String(route.params.scanId || ''))
const items = ref<PreviewItemRead[]>([])
const selected = ref<Set<number>>(new Set())
const loading = ref(false)
const executing = ref(false)
const message = ref('')


function isSelected(id: number) {
  return selected.value.has(id)
}

function toggle(id: number) {
  const next = new Set(selected.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  selected.value = next
}

async function loadItems() {
  if (!scanId.value) {
    items.value = []
    selected.value = new Set()
    message.value = '请先选择扫描批次'
    return
  }

  loading.value = true
  message.value = ''
  try {
    items.value = await apiGet<PreviewItemRead[]>(`/api/scans/${scanId.value}/items`)
    selected.value = new Set(items.value.map((item) => item.id))
  } catch (error) {
    message.value = `加载预览失败：${(error as Error).message}`
  } finally {
    loading.value = false
  }
}

async function executeSelected() {
  if (selected.value.size === 0) {
    message.value = '请选择至少一项'
    return
  }

  if (!confirm(`确认执行 ${selected.value.size} 项真实 115 操作？`)) return

  executing.value = true
  message.value = ''
  try {
    const execution = await apiSend<ExecutionRead>('/api/executions', 'POST', {
      preview_item_ids: Array.from(selected.value),
      fail_fast: false,
    })
    message.value = `执行完成：成功 ${execution.success_count}，失败 ${execution.failed_count}，跳过 ${execution.skipped_count}`
  } catch (error) {
    message.value = `执行失败：${(error as Error).message}`
  } finally {
    executing.value = false
  }
}

onMounted(loadItems)
</script>

<template>
  <section class="preview-page">
    <div class="card">
      <header class="page-header">
        <div>
          <p class="eyebrow">Preview</p>
          <h2>预览确认</h2>
          <p class="hint">扫描批次 ID：{{ scanId || '未指定' }}</p>
        </div>
        <div class="actions">
          <button class="secondary" type="button" :disabled="loading" @click="loadItems">
            {{ loading ? '加载中...' : '加载预览' }}
          </button>
          <button type="button" :disabled="executing" @click="executeSelected">
            {{ executing ? '执行中...' : '执行勾选项' }}
          </button>
        </div>
      </header>

      <p v-if="message" class="message">{{ message }}</p>
      <p v-if="!loading && items.length === 0" class="empty">暂无预览项。</p>
      <table v-else>
        <thead>
          <tr>
            <th>选择</th>
            <th>原路径</th>
            <th>新路径</th>
            <th>媒体类型</th>
            <th>冲突</th>
            <th>动作</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>
              <input type="checkbox" :checked="isSelected(item.id)" @change="toggle(item.id)" />
            </td>
            <td>{{ item.original_path }}</td>
            <td>{{ item.new_path }}</td>
            <td>{{ item.media_type }}</td>
            <td>{{ item.conflict_status }}</td>
            <td>{{ item.final_action }}</td>
            <td>{{ item.status }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.preview-page {
  display: grid;
  gap: 18px;
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
.empty {
  color: #64748b;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.message {
  margin: 12px 0;
  color: #0f766e;
  font-weight: 600;
}

td input {
  width: auto;
}

@media (max-width: 900px) {
  .page-header {
    display: grid;
  }
}
</style>
