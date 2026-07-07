<template>
  <label class="config-switch">
    <span class="switch-label">{{ label }}</span>
    <input type="checkbox" :checked="value" @change="$emit('toggle', $event.target.checked)" />
    <span class="switch-slider"></span>
  </label>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: Boolean, default: false },
});

defineEmits(["toggle"]);
</script>

<style scoped>
.config-switch {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px 0;
}
.switch-label {
  font-size: 14px;
  font-weight: 500;
  flex: 1;
}
.config-switch input {
  display: none;
}
.switch-slider {
  position: relative;
  width: 44px;
  height: 24px;
  background: #ced4da;
  border-radius: 12px;
  transition: background 0.2s;
}
.switch-slider::after {
  content: "";
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: #ffffff;
  border-radius: 50%;
  transition: transform 0.2s;
}
.config-switch input:checked + .switch-slider {
  background: var(--accent);
}
.config-switch input:checked + .switch-slider::after {
  transform: translateX(20px);
}
</style>
