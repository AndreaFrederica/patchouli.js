<template>
  <div class="about-widget">
    <img class="about-icon" :src="iconSrc" alt="icon" />
    <div class="about-text">
      <h4>Patchouli.js</h4>
      <p>
        Patchouli.js 是一个基于 Vue 编写的 HTML 文档阅读器，支持单页和分页显示。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const iconSrc = "logo.png"; // 这里是图标的路径，替换为实际图标路径
</script>

<style scoped>
.about-widget {
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 10px;
  border-radius: 8px;
  /* box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2); */
  width: 100%;
  max-width: 300px;
}

.about-icon {
  width: 50px;
  height: 50px;
  object-fit: contain;
}

.about-text {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.about-text h4 {
  margin: 0;
  font-size: 18px;
  font-weight: bold;
}

.about-text p {
  font-size: 14px;
  margin-top: 5px;
  line-height: 1.4;
  color: #555;
}
</style>
