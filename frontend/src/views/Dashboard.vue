<template>
  <div class="dashboard">
    <h1>Dashboard</h1>
    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-value">--</span>
        <span class="stat-label">上次运行</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">--</span>
        <span class="stat-label">今日论文</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">--</span>
        <span class="stat-label">已见总数</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">--</span>
        <span class="stat-label">本地库</span>
      </div>
    </div>
    <div class="features-section">
      <h2>启用的功能</h2>
      <div class="features-grid">
        <StatusBadge v-for="f in enabled" :key="f" :label="f" :active="true" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import StatusBadge from "../components/StatusBadge.vue";

const enabled = ref(["期刊过滤", "站点生成"]);
</script>

<style scoped>
.dashboard {
  padding: 8px 0;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}
.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px 16px;
  text-align: center;
}
.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: var(--accent);
}
.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}
.features-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
</style>
