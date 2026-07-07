<template>
  <div class="keywords-page">
    <h1>关键词组管理</h1>
    <p class="desc">配置检索关键词组，支持 AND/OR 逻辑</p>
    <div class="placeholder">
      <p>通过 config.yaml 或前端管理界面编辑关键词组。</p>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.keywords-page { padding: 8px 0; }
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
