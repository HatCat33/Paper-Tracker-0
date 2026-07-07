<template>
  <div class="paper-card">
    <h3 class="paper-title">
      <a :href="paper.url || '#'" target="_blank" rel="noopener">{{ paper.title || "Untitled" }}</a>
    </h3>
    <p class="paper-authors">{{ authors }}</p>
    <p class="paper-abstract">{{ truncatedAbstract }}</p>
    <div class="paper-badges">
      <span v-for="cat in paper.categories?.slice(0, 3)" :key="cat" class="badge badge-cat">{{ cat }}</span>
      <span v-if="paper.matched_journal" class="badge badge-journal">{{ paper.matched_journal }}</span>
      <span v-if="paper.citation_count" class="badge badge-cite">Cited: {{ paper.citation_count }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  paper: { type: Object, required: true },
});

const authors = computed(() => {
  const list = props.paper.authors || [];
  const names = list.slice(0, 5).join(", ");
  return list.length > 5 ? `${names} et al.` : names;
});

const truncatedAbstract = computed(() => {
  const text = props.paper.abstract || "";
  return text.length > 250 ? text.slice(0, 250) + "..." : text;
});
</script>

<style scoped>
.paper-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  transition: box-shadow 0.2s;
}
.paper-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.paper-title {
  font-size: 16px;
  margin: 0 0 6px;
}
.paper-title a {
  color: var(--text);
  text-decoration: none;
}
.paper-title a:hover {
  color: var(--accent);
}
.paper-authors {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.paper-abstract {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.paper-badges {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}
.badge-cat {
  background: #e8f4f8;
  color: #0c6787;
}
.badge-journal {
  background: #fff3cd;
  color: #856404;
}
.badge-cite {
  background: #e8e8e8;
  color: #333;
}
</style>
