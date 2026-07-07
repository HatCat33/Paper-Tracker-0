<template>
  <span class="status-badge" :class="{ active: active }">{{ label }}</span>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  active: { type: Boolean, default: false },
});
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  background: #e9ecef;
  color: #6c757d;
}
.status-badge.active {
  background: var(--accent-light);
  color: #ffffff;
}
</style>
