<template>
  <div class="journals-page">
    <h1>期刊白名单</h1>
    <p class="desc">按等级勾选期刊和会议，仅白名单内的论文会出现在日报中</p>
    <div class="placeholder">
      <p>通过 config.yaml 或前端管理界面编辑期刊白名单。</p>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.journals-page { padding: 8px 0; }
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
