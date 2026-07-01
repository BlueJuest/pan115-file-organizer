import { createRouter, createWebHistory } from 'vue-router'

import { getCurrentUser } from '../api/auth'
import Dashboard from '../pages/Dashboard.vue'
import Login from '../pages/Login.vue'
import Preview from '../pages/Preview.vue'
import QualityProfiles from '../pages/QualityProfiles.vue'
import RenameRules from '../pages/RenameRules.vue'
import Rollback from '../pages/Rollback.vue'
import Scan from '../pages/Scan.vue'
import Settings from '../pages/Settings.vue'
import Submission from '../pages/Submission.vue'
import TaskLogs from '../pages/TaskLogs.vue'
import TelegramPushLogs from '../pages/TelegramPushLogs.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login, meta: { public: true } },
    { path: '/', component: Dashboard },
    { path: '/settings', component: Settings },
    { path: '/rules', component: RenameRules },
    { path: '/quality', component: QualityProfiles },
    { path: '/scan', component: Scan },
    { path: '/preview/:scanId?', component: Preview },
    { path: '/submission', component: Submission },
    { path: '/telegram-push-logs', component: TelegramPushLogs },
    { path: '/logs', component: TaskLogs },
    { path: '/rollback', component: Rollback },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  try {
    await getCurrentUser()
    return true
  } catch {
    return '/login'
  }
})

export default router
