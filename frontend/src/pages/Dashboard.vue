<template>
  <section class="dashboard-page">
    <header class="page-title console-title">
      <div>
        <p class="eyebrow">控制台</p>
        <h2>控制台</h2>
        <p class="hint">目录扫描、预览确认和执行记录的当前工作状态。</p>
      </div>
      <div class="period-actions">
        <button class="period active" type="button">24h</button>
        <button class="period" type="button">7d</button>
        <button class="period" type="button">30d</button>
      </div>
    </header>

    <div class="stats-grid">
      <article class="stat-card source">
        <span class="percent">10%</span>
        <span class="label">SOURCE</span>
        <div class="stat-row"><strong>1</strong><span>SUC</span></div>
        <div class="stat-row"><strong>0</strong><span>FAIL</span></div>
      </article>
      <article class="stat-card">
        <span class="percent">100%</span>
        <span class="label">PREVIEW</span>
        <div class="stat-row"><strong>4</strong><span>STEP</span></div>
        <div class="stat-row"><strong>0</strong><span>RISK</span></div>
      </article>
      <article class="stat-card">
        <span class="percent">100%</span>
        <span class="label">RULES</span>
        <div class="stat-row"><strong>ON</strong><span>MODE</span></div>
        <div class="stat-row"><strong>0</strong><span>FAIL</span></div>
      </article>
      <article class="stat-card resource">
        <span class="percent">7%</span>
        <span class="label">CPU</span>
        <span class="percent second">65%</span>
        <span class="label">RAM</span>
      </article>
    </div>

    <div class="analysis-grid">
      <article class="section-card analysis-card">
        <div class="section-head">
          <div>
            <h3>活跃时间线</h3>
            <p class="hint">目录扫描 / 预览确认 / 执行记录</p>
          </div>
        </div>
        <div class="timeline-lines">
          <span style="height: 34%"></span>
          <span style="height: 62%"></span>
          <span style="height: 45%"></span>
          <span style="height: 78%"></span>
          <span style="height: 52%"></span>
          <span style="height: 68%"></span>
          <span style="height: 38%"></span>
          <span style="height: 56%"></span>
        </div>
      </article>

      <article class="section-card analysis-card">
        <div class="section-head">
          <div>
            <h3>UA统计分析</h3>
            <p class="hint">近期功能调用与输出结果。</p>
          </div>
          <button class="secondary compact" type="button">手动添加</button>
        </div>
        <div class="ua-list">
          <div><strong>目录扫描</strong><span>播放 / 直连</span><em>8/1</em></div>
          <div><strong>预览确认</strong><span>生成 / 执行</span><em>1/1</em></div>
          <div><strong>投稿模块</strong><span>推送 / 图片</span><em>1/1</em></div>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 18px;
}

.console-title {
  min-height: 44px;
}

.period {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 7px 12px;
  background: #fff;
  color: #4b5563;
  font-size: 13px;
  font-weight: 850;
}

.period.active {
  background: var(--ink);
  color: #fff;
}

.stats-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.stat-card {
  display: grid;
  gap: 8px;
  min-height: 150px;
  padding: 18px;
}

.percent {
  color: var(--ink);
  font-size: 34px;
  font-weight: 950;
  line-height: 1;
}

.percent.second {
  margin-top: 8px;
}

.label {
  color: var(--muted);
  font-size: 12px;
  font-weight: 950;
}

.stat-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.stat-row strong {
  color: var(--ink);
  font-size: 20px;
}

.stat-row span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.analysis-grid {
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.9fr);
}

.analysis-card {
  display: grid;
  gap: 18px;
  min-height: 310px;
}

.timeline-lines {
  display: flex;
  align-items: end;
  gap: 16px;
  height: 220px;
  border-radius: 12px;
  background: linear-gradient(#f1f3f6 1px, transparent 1px) 0 0 / 100% 44px;
  padding: 18px;
}

.timeline-lines span {
  flex: 1;
  border-radius: 999px 999px 4px 4px;
  background: var(--ink);
}

.ua-list {
  display: grid;
  gap: 12px;
}

.ua-list div {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2px 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
  background: #f9fafb;
}

.ua-list strong {
  color: var(--ink);
  font-size: 14px;
}

.ua-list span {
  color: var(--muted);
  font-size: 12px;
}

.ua-list em {
  grid-row: 1 / 3;
  grid-column: 2;
  align-self: center;
  color: var(--ink);
  font-style: normal;
  font-weight: 950;
}
</style>
