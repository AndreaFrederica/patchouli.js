<script setup lang="ts">
import PatchouliReader from './components/PatchouliReader.vue'
</script>

<template>
  <!-- 只渲染 PatchouliReader 组件 -->
  <PatchouliReader />
</template>

<style scoped>
/* 确保根元素（html 和 body）占满整个视口 */
html,
body {
  width: 100vw;
  height: 100%;
  margin: 0;
  padding: 0;
}
/* Vue 根元素 #app 占满整个页面 */
</style>
