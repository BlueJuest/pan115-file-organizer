<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { apiSend } from '../api/client'
import DirectoryPicker from '../components/DirectoryPicker.vue'

interface ScanRead {
  id: number
}

const router = useRouter()
const form = reactive({
  source_dir: '0',
  target_dir: '/Movies',
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
  <section class="scan-page">
    <header class="page-title">
      <div>
        <p class="eyebrow">目录扫描</p>
        <h2>读取 115 目录</h2>
        <p class="hint">选择来源和目标目录，先生成预览清单，再决定是否执行真实 115 操作。</p>
      </div>
    </header>

    <div class="config-grid">
      <form class="section-card form-grid" @submit.prevent="startScan">
        <div class="two-columns">
          <DirectoryPicker v-model="form.source_dir" label="来源目录" placeholder="0" value-mode="id" />
          <DirectoryPicker v-model="form.target_dir" label="目标目录" placeholder="/Movies" value-mode="path" />
        </div>

        <div class="two-columns">
          <label class="form-row">
            <span>媒体类型</span>
            <select v-model="form.media_type">
              <option value="movie">电影</option>
              <option value="tv">剧集</option>
              <option value="anime">动漫</option>
            </select>
          </label>
          <label class="check-row">
            <input v-model="form.recursive" type="checkbox" />
            <span>递归扫描子目录</span>
          </label>
        </div>

        <div class="actions">
          <button type="submit" :disabled="scanning">{{ scanning ? '扫描中...' : '读取目录并生成预览' }}</button>
        </div>
        <p v-if="message" class="message">{{ message }}</p>
      </form>

      <aside class="section-card notice-panel">
        <strong>扫描说明</strong>
        <p>扫描只生成预览，不会直接执行真实文件变更。确认后再进入预览页操作。</p>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.scan-page {
  display: grid;
  gap: 18px;
}

.check-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 28px;
}

.check-row input {
  width: auto;
}
</style>
