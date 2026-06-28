<template>
  <div class="app-shell">
    <aside class="sidebar">
      <h1>115 文件整理</h1>
      <RouterLink to="/">仪表盘</RouterLink>
      <RouterLink to="/settings">系统配置</RouterLink>
      <RouterLink to="/rules">重命名规则</RouterLink>
      <RouterLink to="/quality">洗版策略</RouterLink>
      <RouterLink to="/scan">目录扫描</RouterLink>
      <RouterLink to="/preview">预览确认</RouterLink>
      <RouterLink to="/submission">投稿生成</RouterLink>
      <RouterLink to="/telegram-push-logs">TG 推送记录</RouterLink>
      <RouterLink to="/logs">任务日志</RouterLink>
      <RouterLink to="/rollback">回滚记录</RouterLink>
    </aside>
    <main class="content">
      <header class="top-status">
        <span class="status-pill">真实扫描</span>
        <span class="status-pill">真实执行</span>
        <span class="status-pill">删除需审计</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>
