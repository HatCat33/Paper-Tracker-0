<template>
  <div class="logs-page">
    <h1>运行日志</h1>
    <p class="desc">GitHub Actions 运行历史</p>
    <div class="placeholder">
      <p>在 GitHub 仓库的 Actions 标签页查看详细运行日志。</p>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.logs-page { padding: 8px 0; }
.desc { color: var(--text-secondary); font-size: 14px; margin-bottom: 16px; }
.placeholder {
  background: var(--card-bg);
  border: 1px dashed var(--border);
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  color: var(--text-secondary);
}
</style>
