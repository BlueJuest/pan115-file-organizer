import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../pages/Dashboard.vue'
import Preview from '../pages/Preview.vue'
import QualityProfiles from '../pages/QualityProfiles.vue'
import RenameRules from '../pages/RenameRules.vue'
import Rollback from '../pages/Rollback.vue'
import Scan from '../pages/Scan.vue'
import Settings from '../pages/Settings.vue'
import Submission from '../pages/Submission.vue'
import TaskLogs from '../pages/TaskLogs.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard },
    { path: '/settings', component: Settings },
    { path: '/rules', component: RenameRules },
    { path: '/quality', component: QualityProfiles },
    { path: '/scan', component: Scan },
    { path: '/preview/:scanId?', component: Preview },
    { path: '/submission', component: Submission },
    { path: '/logs', component: TaskLogs },
    { path: '/rollback', component: Rollback },
  ],
})
