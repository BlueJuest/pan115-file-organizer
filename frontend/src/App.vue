<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand-block">
        <span class="brand-mark">115</span>
        <div>
          <h1>115 Manage</h1>
          <p>文件整理工作台</p>
        </div>
      </div>

      <nav class="nav-group" aria-label="主要功能">
        <p class="nav-label">工作台</p>
        <RouterLink to="/">仪表盘</RouterLink>
        <RouterLink to="/scan">目录扫描</RouterLink>
        <RouterLink to="/preview">预览确认</RouterLink>
      </nav>

      <nav class="nav-group" aria-label="整理配置">
        <p class="nav-label">整理配置</p>
        <RouterLink to="/rules">重命名规则</RouterLink>
        <RouterLink to="/quality">洗版策略</RouterLink>
        <RouterLink to="/settings">系统配置</RouterLink>
      </nav>

      <nav class="nav-group" aria-label="工具箱">
        <p class="nav-label">工具箱</p>
        <RouterLink to="/submission">投稿模块</RouterLink>
        <RouterLink to="/telegram-push-logs">TG 推送记录</RouterLink>
        <RouterLink to="/logs">任务日志</RouterLink>
        <RouterLink to="/rollback">回滚记录</RouterLink>
      </nav>

      <div class="sidebar-note">
        <strong>安全模式</strong>
        <span>预览确认后再执行真实 115 操作</span>
      </div>
    </aside>

    <main class="content">
      <header class="top-status">
        <div>
          <p class="eyebrow">115 文件整理</p>
          <strong>扫描、预览、执行、回滚的整理闭环</strong>
        </div>
        <div class="status-group">
          <span class="status-pill">真实扫描</span>
          <span class="status-pill warning">删除需审计</span>
          <span class="status-pill calm">投稿模块</span>
        </div>
      </header>
      <RouterView />
    </main>
  </div>
</template>
