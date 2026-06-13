<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { apiSend } from '../api/client'

interface ScanRead {
  id: number
}

const router = useRouter()
const form = reactive({
  source_dir: 'src',
  target_dir: '/电影',
  media_type: 'movie',
  recursive: false,
})
const scanning = ref(false)
const message = ref('')

async function startScan() {
  scanning.value = true
  message.value = ''
  try {
    const scan = await apiSend<ScanRead>('/api/scans', 'POST', form)
    message.value = `扫描完成：批次 ${scan.id}`
    await router.push(`/preview/${scan.id}`)
  } catch (error) {
    message.value = `扫描失败：${(error as Error).message}`
  } finally {
    scanning.value = false
  }
}
</script>

<template>
  <section class="card scan-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Scan</p>
        <h2>目录扫描</h2>
        <p class="hint">选择源目录和目标目录，生成可确认的整理预览。</p>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="startScan">
      <div class="two-columns">
        <label class="form-row">
          <span>源目录</span>
          <input v-model="form.source_dir" required placeholder="src" />
        </label>
        <label class="form-row">
          <span>目标目录</span>
          <input v-model="form.target_dir" required placeholder="/电影" />
        </label>
      </div>

      <div class="two-columns">
        <label class="form-row">
          <span>媒体类型</span>
          <select v-model="form.media_type">
            <option value="movie">movie</option>
            <option value="tv">tv</option>
            <option value="anime">anime</option>
          </select>
        </label>
        <label class="check-row">
          <input v-model="form.recursive" type="checkbox" />
          <span>递归扫描子目录</span>
        </label>
      </div>

      <div class="actions">
        <button type="submit" :disabled="scanning">{{ scanning ? '扫描中...' : '开始扫描并生成预览' }}</button>
      </div>
      <p v-if="message" class="message">{{ message }}</p>
    </form>
  </section>
</template>

<style scoped>
.scan-page {
  display: grid;
  gap: 20px;
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

.hint {
  color: #64748b;
}

.two-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.check-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 24px;
}

.check-row input {
  width: auto;
}

.actions {
  display: flex;
  gap: 10px;
}

.message {
  margin: 0;
  color: #0f766e;
  font-weight: 600;
}

@media (max-width: 900px) {
  .two-columns {
    grid-template-columns: 1fr;
  }
}
</style>
