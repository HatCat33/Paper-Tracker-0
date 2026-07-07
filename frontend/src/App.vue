<template>
  <div id="app" :class="{ dark: isDark }">
    <NavBar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref } from "vue";
import NavBar from "./components/NavBar.vue";

const isDark = ref(false);
</script>

<style scoped>
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 16px;
}
</style>
