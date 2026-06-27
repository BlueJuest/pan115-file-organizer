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
    message.value = `Scan complete: batch ${scan.id}`
    await router.push(`/preview/${scan.id}`)
  } catch (error) {
    message.value = `Scan failed: ${(error as Error).message}`
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
        <h2>Directory scan</h2>
        <p class="hint">Choose source and target directories, then generate a preview before any real 115 operation.</p>
      </div>
    </header>

    <form class="form-grid" @submit.prevent="startScan">
      <div class="two-columns">
        <DirectoryPicker v-model="form.source_dir" label="Source directory" placeholder="0" value-mode="id" />
        <DirectoryPicker v-model="form.target_dir" label="Target directory" placeholder="/Movies" value-mode="path" />
      </div>

      <div class="two-columns">
        <label class="form-row">
          <span>Media type</span>
          <select v-model="form.media_type">
            <option value="movie">movie</option>
            <option value="tv">tv</option>
            <option value="anime">anime</option>
          </select>
        </label>
        <label class="check-row">
          <input v-model="form.recursive" type="checkbox" />
          <span>Scan subdirectories recursively</span>
        </label>
      </div>

      <div class="actions">
        <button type="submit" :disabled="scanning">{{ scanning ? 'Scanning...' : 'Read 115 directory and generate preview' }}</button>
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
