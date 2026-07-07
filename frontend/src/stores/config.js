import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useConfigStore = defineStore("config", () => {
  // State
  const config = ref({
    search: { categories: [] },
    freshness: { since_days: 3 },
    journal_filter: { enabled: true, active_levels: [] },
    semantic_filter: { enabled: false, threshold: 0.5 },
    local_recommend: { enabled: false },
    llm_summary: { enabled: false },
    email: { enabled: false },
    site: { enabled: true },
  });

  const isLoading = ref(false);
  const lastFetch = ref(null);

  // Getters
  const enabledFeatures = computed(() => {
    const features = [];
    if (config.value.journal_filter?.enabled) features.push("期刊过滤");
    if (config.value.semantic_filter?.enabled) features.push("语义过滤");
    if (config.value.local_recommend?.enabled) features.push("本地推荐");
    if (config.value.llm_summary?.enabled) features.push("LLM摘要");
    if (config.value.email?.enabled) features.push("邮件推送");
    return features;
  });

  // Actions
  async function fetchConfig() {
    isLoading.value = true;
    try {
      // In GitHub Pages environment, we simulate reading from the deployed JSON
      const response = await fetch("./config.json");
      if (response.ok) {
        config.value = await response.json();
      }
    } catch {
      console.warn("Cannot load config.json, using defaults");
    } finally {
      isLoading.value = false;
      lastFetch.value = new Date();
    }
  }

  function toggleFeature(featurePath, value) {
    const keys = featurePath.split(".");
    let obj = config.value;
    for (let i = 0; i < keys.length - 1; i++) {
      if (!obj[keys[i]]) obj[keys[i]] = {};
      obj = obj[keys[i]];
    }
    obj[keys[keys.length - 1]] = value;
  }

  function updateValue(path, value) {
    toggleFeature(path, value);
  }

  return {
    config,
    isLoading,
    lastFetch,
    enabledFeatures,
    fetchConfig,
    toggleFeature,
    updateValue,
  };
});
