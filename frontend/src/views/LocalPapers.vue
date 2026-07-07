<template>
  <div class="local-papers-page">
    <h1>本地论文库</h1>
    <p class="desc">管理 .bib 文件（支持 ScholarRead / Zotero 导出），用于个性化推荐</p>
    <div class="placeholder">
      <p>将 .bib 文件放入 data/ 目录即可。</p>
      <p>推荐功能默认关闭，需在 config.yaml 中启用。</p>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.local-papers-page { padding: 8px 0; }
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
