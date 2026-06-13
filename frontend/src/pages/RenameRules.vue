<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { apiGet, apiSend } from '../api/client'
import type { RenameRuleRead } from '../api/types'

type RuleForm = Omit<RenameRuleRead, 'id' | 'sample_output' | 'hit_count'>

interface RuleTestResult {
  matched: boolean
  fields: Record<string, string>
  output?: string
  error: string
}

const rules = ref<RenameRuleRead[]>([])
const selectedId = ref<number | null>(null)
const loading = ref(false)
const saving = ref(false)
const message = ref('')
const testResult = ref<RuleTestResult | null>(null)

const form = reactive<RuleForm>({
  name: '',
  media_type: 'movie',
  pattern: '',
  template: '',
  priority: 100,
  enabled: true,
  sample_input: '',
})

const selectedRule = computed(() => rules.value.find((rule) => rule.id === selectedId.value))

function resetForm() {
  selectedId.value = null
  Object.assign(form, {
    name: '',
    media_type: 'movie',
    pattern: '',
    template: '',
    priority: 100,
    enabled: true,
    sample_input: '',
  })
  testResult.value = null
}

function editRule(rule: RenameRuleRead) {
  selectedId.value = rule.id
  Object.assign(form, {
    name: rule.name,
    media_type: rule.media_type,
    pattern: rule.pattern,
    template: rule.template,
    priority: rule.priority,
    enabled: rule.enabled,
    sample_input: rule.sample_input,
  })
  testResult.value = null
}

async function loadRules() {
  loading.value = true
  message.value = ''
  try {
    rules.value = await apiGet<RenameRuleRead[]>('/api/rules')
  } catch (error) {
    message.value = `加载规则失败：${(error as Error).message}`
  } finally {
    loading.value = false
  }
}

async function saveRule() {
  saving.value = true
  message.value = ''
  try {
    const url = selectedId.value === null ? '/api/rules' : `/api/rules/${selectedId.value}`
    const method = selectedId.value === null ? 'POST' : 'PUT'
    const saved = await apiSend<RenameRuleRead>(url, method, form)
    message.value = `规则「${saved.name}」已保存`
    await loadRules()
    editRule(saved)
  } catch (error) {
    message.value = `保存规则失败：${(error as Error).message}`
  } finally {
    saving.value = false
  }
}

async function testRule() {
  testResult.value = null
  message.value = ''
  try {
    testResult.value = await apiSend<RuleTestResult>('/api/rules/test', 'POST', {
      media_type: form.media_type,
      pattern: form.pattern,
      template: form.template,
      priority: form.priority,
      enabled: form.enabled,
      sample_input: form.sample_input,
    })
  } catch (error) {
    message.value = `测试规则失败：${(error as Error).message}`
  }
}

onMounted(loadRules)
</script>

<template>
  <section class="rules-page">
    <div class="card list-card">
      <header class="page-header">
        <div>
          <p class="eyebrow">Rename Rules</p>
          <h2>重命名规则</h2>
        </div>
        <button type="button" @click="resetForm">新增规则</button>
      </header>

      <p v-if="loading">规则加载中...</p>
      <p v-else-if="rules.length === 0" class="empty">还没有规则，请先新增一条。</p>
      <table v-else>
        <thead>
          <tr>
            <th>优先级</th>
            <th>名称</th>
            <th>媒体类型</th>
            <th>状态</th>
            <th>命中</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rule in rules" :key="rule.id" :class="{ selected: rule.id === selectedId }">
            <td>{{ rule.priority }}</td>
            <td>{{ rule.name }}</td>
            <td>{{ rule.media_type }}</td>
            <td>{{ rule.enabled ? '启用' : '停用' }}</td>
            <td>{{ rule.hit_count }}</td>
            <td><button class="secondary" type="button" @click="editRule(rule)">编辑</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <form class="card form-grid editor-card" @submit.prevent="saveRule">
      <header>
        <h3>{{ selectedRule ? `编辑：${selectedRule.name}` : '新增规则' }}</h3>
        <p class="hint">使用正则命名捕获字段，并在模板中用 {field} 输出目标路径。</p>
      </header>

      <div class="two-columns">
        <label class="form-row">
          <span>规则名称</span>
          <input v-model="form.name" required placeholder="movie-year" />
        </label>
        <label class="form-row">
          <span>媒体类型</span>
          <select v-model="form.media_type">
            <option value="movie">movie</option>
            <option value="tv">tv</option>
            <option value="anime">anime</option>
          </select>
        </label>
      </div>

      <label class="form-row">
        <span>匹配正则</span>
        <textarea v-model="form.pattern" required rows="3" placeholder="(?P&lt;title&gt;.+?)[ ._-]+(?P&lt;year&gt;20\d{2})" />
      </label>

      <label class="form-row">
        <span>输出模板</span>
        <textarea v-model="form.template" required rows="3" placeholder="/电影/{title} ({year})/{title} ({year}).{ext}" />
      </label>

      <div class="two-columns">
        <label class="form-row">
          <span>优先级</span>
          <input v-model.number="form.priority" type="number" />
        </label>
        <label class="check-row">
          <input v-model="form.enabled" type="checkbox" />
          <span>启用规则</span>
        </label>
      </div>

      <label class="form-row">
        <span>测试样例</span>
        <input v-model="form.sample_input" placeholder="流浪地球 2019 2160p WEB-DL.mkv" />
      </label>

      <div class="actions">
        <button type="submit" :disabled="saving">{{ saving ? '保存中...' : '保存规则' }}</button>
        <button class="secondary" type="button" @click="testRule">测试规则</button>
      </div>

      <div v-if="testResult" class="test-result">
        <strong>{{ testResult.matched ? '已匹配' : '未匹配' }}</strong>
        <p v-if="testResult.output">输出：{{ testResult.output }}</p>
        <p v-if="testResult.error">错误：{{ testResult.error }}</p>
        <pre>{{ testResult.fields }}</pre>
      </div>
      <p v-if="message" class="message">{{ message }}</p>
    </form>
  </section>
</template>

<style scoped>
.rules-page {
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

.selected {
  background: #eff6ff;
}

.test-result {
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 12px;
  background: #eff6ff;
}

.test-result pre {
  margin-bottom: 0;
  white-space: pre-wrap;
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
