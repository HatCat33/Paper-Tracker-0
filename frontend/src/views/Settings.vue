<template>
  <div class="settings-page">
    <h1>设置</h1>
    <div class="settings-section">
      <h2>邮件配置</h2>
      <ConfigSwitch label="启用邮件推送" :value="false" />
      <p class="hint">SMTP 配置通过 GitHub Secrets 管理，请设置 EMAIL_USER / EMAIL_PASSWORD 等环境变量</p>
    </div>
    <div class="settings-section">
      <h2>LLM 摘要</h2>
      <ConfigSwitch label="启用 LLM 双语摘要" :value="false" />
      <p class="hint">需配置 LLM_API_KEY 环境变量，支持 DeepSeek / OpenAI / SiliconFlow</p>
    </div>
    <div class="settings-section">
      <h2>语义过滤</h2>
      <ConfigSwitch label="启用语义相似度过滤" :value="false" />
      <p class="hint">阈值范围 0~1，越高越严格，默认 0.5</p>
    </div>
    <div class="settings-section">
      <h2>Semantic Scholar</h2>
      <ConfigSwitch label="启用引用量拉取" :value="false" />
    </div>
  </div>
</template>

<script setup>
import ConfigSwitch from "../components/ConfigSwitch.vue";
</script>

<style scoped>
.settings-page { padding: 8px 0; }
.settings-section {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.settings-section h2 {
  font-size: 16px;
  margin-bottom: 12px;
}
.hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
}
</style>
