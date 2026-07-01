<template>
  <main class="login-page">
    <section class="login-panel">
      <div class="login-brand">
        <span class="brand-badge"></span>
        <div>
          <h1>115 Manage</h1>
          <p>后台管理登录</p>
        </div>
      </div>

      <form class="login-card" @submit.prevent="submitLogin">
        <label>
          <span>用户名</span>
          <input v-model="username" name="username" autocomplete="username" placeholder="请输入用户名" />
        </label>
        <label>
          <span>密码</span>
          <input
            v-model="password"
            name="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            type="password"
          />
        </label>
        <p v-if="error" class="login-error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '登录中...' : '立即登录' }}</button>
      </form>
    </section>

    <aside class="login-notice">
      <h2>通知</h2>
      <p>真实 115 操作前请先生成预览，确认无误后再执行。</p>
      <p>后台仅开放单管理员登录，请妥善保管环境变量中的账号和密码。</p>
    </aside>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { login } from '../api/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submitLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(username.value, password.value)
    await router.push('/')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>
