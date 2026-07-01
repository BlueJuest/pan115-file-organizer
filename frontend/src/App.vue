<script setup lang="ts">
import { Clock, DataAnalysis, DocumentChecked, Files, FolderOpened, House, RefreshLeft, Setting, SwitchButton, Tools } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { logout } from './api/auth'

const route = useRoute()
const router = useRouter()

const isLogin = computed(() => route.path === '/login')

const menuItems = [
  { path: '/', label: '控制台', icon: House },
  { path: '/scan', label: '目录扫描', icon: FolderOpened },
  { path: '/preview', label: '预览确认', icon: DocumentChecked },
  { path: '/rules', label: '重命名规则', icon: Tools },
  { path: '/quality', label: '洗版策略', icon: DataAnalysis },
  { path: '/settings', label: '系统设置', icon: Setting },
  { path: '/submission', label: '投稿模块', icon: Files },
  { path: '/telegram-push-logs', label: 'TG 推送记录', icon: Clock },
  { path: '/logs', label: '任务日志', icon: Clock },
  { path: '/rollback', label: '回滚记录', icon: RefreshLeft },
]

async function handleLogout() {
  await logout()
  await router.push('/login')
}
</script>

<template>
  <RouterView v-if="isLogin" />
  <div v-else class="admin-shell">
    <aside class="admin-sidebar">
      <div class="brand-block">
        <span class="brand-dot"></span>
        <div>
          <h1>115 Manage</h1>
          <p>后台管理控制台</p>
        </div>
      </div>

      <div class="nav-group">
        <RouterLink v-for="item in menuItems" :key="item.path" class="nav-link" :to="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </RouterLink>
      </div>

      <div class="sidebar-footer">
        <span class="online-dot"></span>
        <span>连接正常</span>
      </div>
      <button class="logout-link" type="button" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        <span>退出登录</span>
      </button>
      <span class="version-label">v1.0.0</span>
    </aside>

    <main class="admin-content">
      <div class="admin-main">
        <RouterView />
      </div>
    </main>

    <nav class="mobile-dock" aria-label="移动端导航">
      <RouterLink v-for="item in menuItems.slice(0, 5)" :key="item.path" :to="item.path">
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>
  </div>
</template>
