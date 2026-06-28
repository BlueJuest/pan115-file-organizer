<template>
  <section class="dashboard-page">
    <div class="hero-panel card">
      <div>
        <p class="eyebrow">工作台</p>
        <h2>文件整理中枢</h2>
        <p class="hint">从 115 目录扫描开始，先预览确认，再执行真实整理；投稿模块用于生成 Telegram 频道内容。</p>
      </div>
      <RouterLink class="hero-action" to="/scan">开始目录扫描</RouterLink>
    </div>

    <div class="metric-grid">
      <article class="metric-card">
        <span>整理流程</span>
        <strong>4 步</strong>
        <p>扫描、预览、执行、回滚</p>
      </article>
      <article class="metric-card">
        <span>工具箱</span>
        <strong>1 个</strong>
        <p>当前启用投稿模块</p>
      </article>
      <article class="metric-card">
        <span>安全边界</span>
        <strong>预览优先</strong>
        <p>删除和移动前先审计</p>
      </article>
      <article class="metric-card">
        <span>适配</span>
        <strong>移动端</strong>
        <p>窄屏自动堆叠布局</p>
      </article>
    </div>

    <div class="workflow-grid">
      <RouterLink class="workflow-card" to="/scan">
        <span class="status-pill calm">整理</span>
        <h3>目录扫描</h3>
        <p>选择来源目录和目标目录，生成待整理清单。</p>
      </RouterLink>
      <RouterLink class="workflow-card" to="/preview">
        <span class="status-pill">确认</span>
        <h3>预览确认</h3>
        <p>检查原路径、目标路径、冲突状态和最终动作。</p>
      </RouterLink>
      <RouterLink class="workflow-card" to="/submission">
        <span class="status-pill calm">工具箱</span>
        <h3>投稿模块</h3>
        <p>输入 115 分享链接，生成频道图片和 Telegram 文案。</p>
      </RouterLink>
      <RouterLink class="workflow-card" to="/logs">
        <span class="status-pill warning">审计</span>
        <h3>任务日志</h3>
        <p>查看执行日志，定位失败、删除和不可回滚操作。</p>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 18px;
}

.hero-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  background: linear-gradient(135deg, #ffffff 0%, #f2f7ff 100%);
}

.hero-panel h2 {
  margin: 0;
  font-size: 30px;
}

.hero-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  padding: 11px 16px;
  background: var(--blue);
  color: white;
  font-weight: 800;
  text-decoration: none;
  white-space: nowrap;
}

.metric-grid,
.workflow-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card,
.workflow-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  padding: 16px;
  box-shadow: var(--shadow);
}

.metric-card span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.metric-card strong {
  display: block;
  margin-top: 6px;
  font-size: 24px;
}

.metric-card p,
.workflow-card p {
  margin: 6px 0 0;
  color: var(--muted);
}

.workflow-card {
  display: grid;
  gap: 10px;
  color: var(--text);
  text-decoration: none;
}

.workflow-card h3 {
  margin: 0;
}

@media (max-width: 1100px) {
  .metric-grid,
  .workflow-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .hero-panel {
    display: grid;
  }

  .hero-action,
  .metric-grid,
  .workflow-grid {
    grid-template-columns: 1fr;
  }
}
</style>
