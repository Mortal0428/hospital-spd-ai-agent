<template>
  <div id="spd-root-app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useUserStore } from '@/stores/userStore';

const userStore = useUserStore();

onMounted(() => {
  // 恢复本地记忆的主题
  const savedTheme = localStorage.getItem('spd_theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  userStore.theme = savedTheme as 'light' | 'dark';
});
</script>

<style>
#spd-root-app {
  width: 100%;
  min-height: 100vh;
}
</style>
