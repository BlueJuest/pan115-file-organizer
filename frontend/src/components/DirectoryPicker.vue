<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { apiGet } from '../api/client'

interface DirectoryItem {
  id: string
  name: string
  path: string
  parent_id: string
  is_dir: boolean
}

const props = defineProps<{
  label: string
  modelValue: string
  placeholder?: string
  valueMode?: 'id' | 'path'
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const open = ref(false)
const loading = ref(false)
const error = ref('')
const currentId = ref('0')
const currentPath = ref('/')
const items = ref<DirectoryItem[]>([])
const trail = ref<Array<{ id: string; path: string; name: string }>>([{ id: '0', path: '/', name: 'Root' }])

async function loadDirectory(id = '0', path = '/') {
  loading.value = true
  error.value = ''
  try {
    items.value = await apiGet<DirectoryItem[]>(`/api/directories?parent_id=${encodeURIComponent(id)}`)
    currentId.value = id
    currentPath.value = path || '/'
  } catch (caught) {
    error.value = (caught as Error).message
  } finally {
    loading.value = false
  }
}

async function enterDirectory(item: DirectoryItem) {
  const path = item.path || joinPath(currentPath.value, item.name)
  trail.value.push({ id: item.id, path, name: item.name })
  await loadDirectory(item.id, path)
}

async function jumpTo(index: number) {
  trail.value = trail.value.slice(0, index + 1)
  const target = trail.value[index]
  await loadDirectory(target.id, target.path)
}

function chooseCurrent() {
  emit('update:modelValue', props.valueMode === 'path' ? currentPath.value : currentId.value)
  open.value = false
}

function chooseItem(item: DirectoryItem) {
  emit('update:modelValue', props.valueMode === 'path' ? item.path || joinPath(currentPath.value, item.name) : item.id)
  open.value = false
}

function joinPath(parent: string, name: string) {
  const base = parent === '/' ? '' : parent.replace(/\/$/, '')
  return `${base}/${name}`
}

onMounted(() => loadDirectory())
</script>

<template>
  <div class="directory-picker">
    <label class="form-row">
      <span>{{ label }}</span>
      <div class="picker-input">
        <input :value="modelValue" :placeholder="placeholder || '0'" @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)" />
        <button class="secondary" type="button" @click="open = !open">Browse</button>
      </div>
    </label>

    <div v-if="open" class="picker-panel">
      <div class="crumbs">
        <button v-for="(crumb, index) in trail" :key="crumb.id + index" type="button" class="crumb" @click="jumpTo(index)">
          {{ crumb.name }}
        </button>
      </div>

      <div class="panel-actions">
        <span class="current-path">{{ currentPath }}</span>
        <button type="button" @click="chooseCurrent">Select</button>
      </div>

      <p v-if="loading" class="picker-status">Loading...</p>
      <p v-else-if="error" class="picker-error">{{ error }}</p>
      <p v-else-if="items.length === 0" class="picker-status">No subdirectories</p>
      <div v-else class="directory-list">
        <div v-for="item in items" :key="item.id" class="directory-row">
          <button type="button" class="directory-name" @click="enterDirectory(item)">{{ item.name }}</button>
          <button class="secondary" type="button" @click="chooseItem(item)">Use</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.directory-picker {
  display: grid;
  gap: 8px;
}

.picker-input {
  display: flex;
  gap: 8px;
}

.picker-input input {
  min-width: 0;
}

.picker-panel {
  display: grid;
  gap: 10px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 12px;
  background: #f8fafc;
}

.crumbs,
.panel-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.crumb {
  padding: 6px 8px;
}

.current-path {
  flex: 1;
  min-width: 160px;
  color: #475569;
  overflow-wrap: anywhere;
}

.directory-list {
  display: grid;
  gap: 6px;
}

.directory-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
}

.directory-name {
  flex: 1;
  padding: 0;
  border: 0;
  background: transparent;
  color: #0f172a;
  text-align: left;
}

.picker-status {
  margin: 0;
  color: #64748b;
}

.picker-error {
  margin: 0;
  color: #b91c1c;
}

@media (max-width: 700px) {
  .picker-input {
    flex-direction: column;
  }
}
</style>
