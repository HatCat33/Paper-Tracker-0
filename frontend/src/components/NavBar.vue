<template>
  <nav class="navbar">
    <div class="nav-container">
      <router-link to="/" class="nav-brand">Paper Tracker</router-link>
      <button class="hamburger" @click="menuOpen = !menuOpen" aria-label="菜单">
        <span></span><span></span><span></span>
      </button>
      <div class="nav-links" :class="{ open: menuOpen }">
        <router-link to="/" @click="menuOpen = false">Dashboard</router-link>
        <router-link to="/keywords" @click="menuOpen = false">关键词</router-link>
        <router-link to="/journals" @click="menuOpen = false">期刊</router-link>
        <router-link to="/settings" @click="menuOpen = false">设置</router-link>
        <router-link to="/local-papers" @click="menuOpen = false">论文库</router-link>
        <router-link to="/history" @click="menuOpen = false">历史</router-link>
        <router-link to="/logs" @click="menuOpen = false">日志</router-link>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from "vue";

const menuOpen = ref(false);
</script>

<style scoped>
.navbar {
  background: var(--card-bg);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
  display: flex;
  align-items: center;
  height: 56px;
  justify-content: space-between;
}
.nav-brand {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
  text-decoration: none;
}
.nav-links {
  display: flex;
  gap: 4px;
}
.nav-links a {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  color: var(--text);
  text-decoration: none;
  transition: background 0.15s;
}
.nav-links a:hover,
.nav-links a.router-link-exact-active {
  background: var(--accent-light);
  color: #ffffff;
}
.hamburger {
  display: none;
  flex-direction: column;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
}
.hamburger span {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--text);
  border-radius: 1px;
}

/* Mobile */
@media (max-width: 768px) {
  .hamburger { display: flex; }
  .nav-links {
    display: none;
    position: absolute;
    top: 56px;
    left: 0;
    right: 0;
    background: var(--card-bg);
    flex-direction: column;
    padding: 8px;
    border-bottom: 1px solid var(--border);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
  .nav-links.open { display: flex; }
}
</style>
