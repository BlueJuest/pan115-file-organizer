<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { apiSend } from '../api/client'
import type { SubmissionPreviewResponse, SubmissionPublishResponse } from '../api/types'

const QUALITY_OPTIONS = ['2160p', '1080p', '720p', '480p']
const SOURCE_OPTIONS = ['WEB-DL/WEBRip', 'ISO', 'REMUX', 'DVD', 'DVDRip', 'BDRip/BluRayEncode']
const SUBTITLE_OPTIONS = ['简中', '繁中', '简日双语', '繁体双语', '简英双语', '繁英双语']
const MEDIA_TYPE_OPTIONS = [
  { label: '自动', value: 'auto' },
  { label: '电影', value: 'movie' },
  { label: '剧集', value: 'tv' },
]

const form = reactive({
  share_url: '',
  media_type: 'auto',
  qualities: ['1080p'],
  video_sources: ['WEB-DL/WEBRip'],
  subtitles: ['简中'],
  custom_content: '',
})

const preview = ref<SubmissionPreviewResponse | null>(null)
const loading = ref(false)
const publishing = ref(false)
const message = ref('')

const payload = computed(() => ({
  share_url: form.share_url,
  media_type: form.media_type,
  quality: form.qualities.join(' / '),
  video_source: form.video_sources.join(' / '),
  subtitles: form.subtitles.join(' / '),
  custom_content: form.custom_content,
}))

function toggleOption(target: string[], value: string) {
  const index = target.indexOf(value)
  if (index >= 0) {
    target.splice(index, 1)
  } else {
    target.push(value)
  }
}

async function generatePreview() {
  loading.value = true
  message.value = ''
  preview.value = null
  try {
    preview.value = await apiSend<SubmissionPreviewResponse>('/api/submissions/preview', 'POST', payload.value)
    message.value = '预览已生成，请确认原图和频道文本后推送。'
  } catch (error) {
    message.value = `生成失败：${(error as Error).message}`
  } finally {
    loading.value = false
  }
}

async function publish() {
  if (!preview.value) return
  publishing.value = true
  message.value = ''
  try {
    const result = await apiSend<SubmissionPublishResponse>('/api/submissions/publish', 'POST', {
      image_url: preview.value.image_url,
      caption: preview.value.caption,
    })
    message.value = result.telegram_message_id
      ? `${result.message}，消息 ID：${result.telegram_message_id}`
      : result.message
  } catch (error) {
    message.value = `推送失败：${(error as Error).message}`
  } finally {
    publishing.value = false
  }
}
</script>

<template>
  <section class="submission-page">
    <div class="card submission-form-card">
      <header class="page-header">
        <div>
          <p class="eyebrow">Submission</p>
          <h2>投稿生成</h2>
          <p class="hint">输入 115 分享链接，自动识别媒体信息并生成 Telegram 频道文本。</p>
        </div>
      </header>

      <form class="form-grid" @submit.prevent="generatePreview">
        <label class="form-row">
          <span>115 分享链接</span>
          <input v-model="form.share_url" required placeholder="https://115.com/s/xxxx?password=xxxx" />
        </label>

        <fieldset class="option-group">
          <legend>类型</legend>
          <button
            v-for="option in MEDIA_TYPE_OPTIONS"
            :key="option.value"
            type="button"
            :class="['choice', { active: form.media_type === option.value }]"
            @click="form.media_type = option.value"
          >
            {{ option.label }}
          </button>
        </fieldset>

        <fieldset class="option-group">
          <legend>画质</legend>
          <button
            v-for="option in QUALITY_OPTIONS"
            :key="option"
            type="button"
            :class="['choice', { active: form.qualities.includes(option) }]"
            @click="toggleOption(form.qualities, option)"
          >
            {{ option }}
          </button>
        </fieldset>

        <fieldset class="option-group">
          <legend>视频源</legend>
          <button
            v-for="option in SOURCE_OPTIONS"
            :key="option"
            type="button"
            :class="['choice', { active: form.video_sources.includes(option) }]"
            @click="toggleOption(form.video_sources, option)"
          >
            {{ option }}
          </button>
        </fieldset>

        <fieldset class="option-group">
          <legend>字幕</legend>
          <button
            v-for="option in SUBTITLE_OPTIONS"
            :key="option"
            type="button"
            :class="['choice', { active: form.subtitles.includes(option) }]"
            @click="toggleOption(form.subtitles, option)"
          >
            {{ option }}
          </button>
        </fieldset>

        <label class="form-row">
          <span>自定义内容</span>
          <textarea v-model="form.custom_content" rows="3" placeholder="1080P WEB-DL DDP5.1 内封简中 [Team]" />
        </label>

        <div class="actions">
          <button type="submit" :disabled="loading">{{ loading ? '生成中...' : '生成预览' }}</button>
          <button class="secondary" type="button" :disabled="!preview || publishing" @click="publish">
            {{ publishing ? '推送中...' : '推送到 Telegram' }}
          </button>
        </div>

        <p v-if="message" class="message">{{ message }}</p>
      </form>
    </div>

    <div class="card preview-card">
      <header class="preview-header">
        <div>
          <p class="eyebrow">Preview</p>
          <h2>预览确认</h2>
        </div>
        <span v-if="preview" class="status-pill">{{ preview.media.media_type === 'movie' ? '电影' : '剧集' }}</span>
      </header>

      <div v-if="preview" class="preview-content">
        <img v-if="preview.image_url" class="submission-image" :src="preview.image_url" alt="频道推送原图预览" />
        <p v-else class="empty-preview">TMDB 没有可用剧照或海报。</p>
        <textarea class="caption-preview" readonly rows="14" :value="preview.caption" />
        <dl class="meta-list">
          <div>
            <dt>目录名</dt>
            <dd>{{ preview.folder_name }}</dd>
          </div>
          <div>
            <dt>TMDB</dt>
            <dd>{{ preview.media.tmdb_id }} · {{ preview.media.title }}</dd>
          </div>
          <div>
            <dt>分享人</dt>
            <dd>{{ preview.share_user }}</dd>
          </div>
          <div>
            <dt>大小</dt>
            <dd>{{ preview.size_text }}</dd>
          </div>
        </dl>
      </div>

      <p v-else class="empty-preview">生成后会在这里显示频道推送原图和 Telegram 文本。</p>
    </div>
  </section>
</template>

<style scoped>
.submission-page {
  display: grid;
  grid-template-columns: minmax(320px, 520px) minmax(360px, 1fr);
  gap: 18px;
  align-items: start;
}

.submission-form-card,
.preview-card {
  display: grid;
  gap: 18px;
}

.page-header,
.preview-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-header h2,
.preview-header h2 {
  margin: 0;
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--blue);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hint,
.empty-preview {
  color: var(--muted);
}

.option-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
}

.option-group legend {
  padding: 0 6px;
  color: var(--muted);
  font-size: 13px;
}

.choice {
  border: 1px solid #334155;
  background: #0f172a;
  color: var(--text);
}

.choice.active {
  border-color: #38bdf8;
  background: #2563eb;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.message {
  margin: 0;
  color: var(--green);
  font-weight: 600;
}

.preview-content {
  display: grid;
  gap: 16px;
}

.submission-image {
  width: min(100%, 720px);
  max-height: 420px;
  object-fit: contain;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: #0f172a;
}

.caption-preview {
  min-height: 280px;
  resize: vertical;
  white-space: pre-wrap;
}

.meta-list {
  display: grid;
  gap: 10px;
  margin: 0;
}

.meta-list div {
  display: grid;
  gap: 4px;
}

.meta-list dt {
  color: var(--muted);
  font-size: 12px;
}

.meta-list dd {
  margin: 0;
}

@media (max-width: 1100px) {
  .submission-page {
    grid-template-columns: 1fr;
  }
}
</style>
