<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { apiGet, apiSend } from '../api/client'

interface QualityProfileRead {
  id: number
  name: string
  resolution_weight: number
  source_weight: number
  video_codec_weight: number
  audio_codec_weight: number
  size_weight: number
  subtitle_weight: number
  min_upgrade_delta: number
  default_old_file_action: string
  resolution_order: string
  source_order: string
  video_codec_order: string
  audio_codec_order: string
}

type ProfileForm = Omit<QualityProfileRead, 'id'>

const profiles = ref<QualityProfileRead[]>([])
const selectedId = ref<number | null>(null)
const loading = ref(false)
const saving = ref(false)
const message = ref('')

const form = reactive<ProfileForm>({
  name: '默认洗版策略',
  resolution_weight: 45,
  source_weight: 20,
  video_codec_weight: 15,
  audio_codec_weight: 10,
  size_weight: 5,
  subtitle_weight: 5,
  min_upgrade_delta: 12,
  default_old_file_action: 'move_to_recycle',
  resolution_order: '2160p,1080p,720p',
  source_order: 'BluRay,WEB-DL,WEBRip,HDTV',
  video_codec_order: 'H.265,HEVC,H.264,AVC',
  audio_codec_order: 'TrueHD,DTS-HD,DDP,DD,AAC',
})

const selectedProfile = computed(() => profiles.value.find((profile) => profile.id === selectedId.value))

function resetForm() {
  selectedId.value = null
  Object.assign(form, {
    name: '默认洗版策略',
    resolution_weight: 45,
    source_weight: 20,
    video_codec_weight: 15,
    audio_codec_weight: 10,
    size_weight: 5,
    subtitle_weight: 5,
    min_upgrade_delta: 12,
    default_old_file_action: 'move_to_recycle',
    resolution_order: '2160p,1080p,720p',
    source_order: 'BluRay,WEB-DL,WEBRip,HDTV',
    video_codec_order: 'H.265,HEVC,H.264,AVC',
    audio_codec_order: 'TrueHD,DTS-HD,DDP,DD,AAC',
  })
}

function editProfile(profile: QualityProfileRead) {
  selectedId.value = profile.id
  Object.assign(form, {
    name: profile.name,
    resolution_weight: profile.resolution_weight,
    source_weight: profile.source_weight,
    video_codec_weight: profile.video_codec_weight,
    audio_codec_weight: profile.audio_codec_weight,
    size_weight: profile.size_weight,
    subtitle_weight: profile.subtitle_weight,
    min_upgrade_delta: profile.min_upgrade_delta,
    default_old_file_action: profile.default_old_file_action,
    resolution_order: profile.resolution_order,
    source_order: profile.source_order,
    video_codec_order: profile.video_codec_order,
    audio_codec_order: profile.audio_codec_order,
  })
}

async function loadProfiles() {
  loading.value = true
  message.value = ''
  try {
    profiles.value = await apiGet<QualityProfileRead[]>('/api/quality-profiles')
  } catch (error) {
    message.value = `加载洗版策略失败：${(error as Error).message}`
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  message.value = ''
  try {
    const url = selectedId.value === null ? '/api/quality-profiles' : `/api/quality-profiles/${selectedId.value}`
    const method = selectedId.value === null ? 'POST' : 'PUT'
    const saved = await apiSend<QualityProfileRead>(url, method, form)
    message.value = `策略「${saved.name}」已保存`
    await loadProfiles()
    editProfile(saved)
  } catch (error) {
    message.value = `保存洗版策略失败：${(error as Error).message}`
  } finally {
    saving.value = false
  }
}

onMounted(loadProfiles)
</script>

<template>
  <section class="profiles-page">
    <div class="card list-card">
      <header class="page-header">
        <div>
          <p class="eyebrow">Quality Profiles</p>
          <h2>洗版策略</h2>
        </div>
        <button type="button" @click="resetForm">新增策略</button>
      </header>

      <p v-if="loading">策略加载中...</p>
      <p v-else-if="profiles.length === 0" class="empty">还没有洗版策略，请先新增一条。</p>
      <table v-else>
        <thead>
          <tr>
            <th>名称</th>
            <th>分辨率</th>
            <th>片源</th>
            <th>编码</th>
            <th>升级阈值</th>
            <th>旧文件处理</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="profile in profiles" :key="profile.id" :class="{ selected: profile.id === selectedId }">
            <td>{{ profile.name }}</td>
            <td>{{ profile.resolution_weight }}</td>
            <td>{{ profile.source_weight }}</td>
            <td>{{ profile.video_codec_weight }}</td>
            <td>{{ profile.min_upgrade_delta }}</td>
            <td>{{ profile.default_old_file_action }}</td>
            <td><button class="secondary" type="button" @click="editProfile(profile)">编辑</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <form class="card form-grid editor-card" @submit.prevent="saveProfile">
      <header>
        <h3>{{ selectedProfile ? `编辑：${selectedProfile.name}` : '新增策略' }}</h3>
        <p class="hint">权重用于判断同媒体新旧文件质量差异，升级阈值越高越保守。</p>
      </header>

      <label class="form-row">
        <span>策略名称</span>
        <input v-model="form.name" required />
      </label>

      <div class="weight-grid">
        <label class="form-row">
          <span>分辨率权重</span>
          <input v-model.number="form.resolution_weight" type="number" />
        </label>
        <label class="form-row">
          <span>片源权重</span>
          <input v-model.number="form.source_weight" type="number" />
        </label>
        <label class="form-row">
          <span>视频编码权重</span>
          <input v-model.number="form.video_codec_weight" type="number" />
        </label>
        <label class="form-row">
          <span>音频编码权重</span>
          <input v-model.number="form.audio_codec_weight" type="number" />
        </label>
        <label class="form-row">
          <span>体积权重</span>
          <input v-model.number="form.size_weight" type="number" />
        </label>
        <label class="form-row">
          <span>字幕权重</span>
          <input v-model.number="form.subtitle_weight" type="number" />
        </label>
      </div>

      <div class="two-columns">
        <label class="form-row">
          <span>最小升级差值</span>
          <input v-model.number="form.min_upgrade_delta" type="number" />
        </label>
        <label class="form-row">
          <span>旧文件默认处理</span>
          <select v-model="form.default_old_file_action">
            <option value="move_to_recycle">move_to_recycle</option>
            <option value="delete">delete</option>
            <option value="keep">keep</option>
          </select>
        </label>
      </div>

      <label class="form-row">
        <span>分辨率排序</span>
        <input v-model="form.resolution_order" />
      </label>
      <label class="form-row">
        <span>片源排序</span>
        <input v-model="form.source_order" />
      </label>
      <label class="form-row">
        <span>视频编码排序</span>
        <input v-model="form.video_codec_order" />
      </label>
      <label class="form-row">
        <span>音频编码排序</span>
        <input v-model="form.audio_codec_order" />
      </label>

      <div class="actions">
        <button type="submit" :disabled="saving">{{ saving ? '保存中...' : '保存策略' }}</button>
      </div>
      <p v-if="message" class="message">{{ message }}</p>
    </form>
  </section>
</template>

<style scoped>
.profiles-page {
  display: grid;
  gap: 18px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header h2,
.editor-card h3 {
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

.weight-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.two-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.actions {
  display: flex;
  gap: 10px;
}

.selected {
  background: #eff6ff;
}

.message {
  margin: 0;
  color: #0f766e;
  font-weight: 600;
}

@media (max-width: 900px) {
  .weight-grid,
  .two-columns {
    grid-template-columns: 1fr;
  }
}
</style>
