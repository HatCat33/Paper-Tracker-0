<template>
  <div class="history-page">
    <h1>历史日报</h1>
    <p class="desc">查看过往的论文日报记录</p>
    <div class="placeholder">
      <p>日报页面生成在 docs/ 目录下，部署后可通过 GitHub Pages 访问。</p>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.history-page { padding: 8px 0; }
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
