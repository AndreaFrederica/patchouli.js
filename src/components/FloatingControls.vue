<template>
  <div class="floating-controls">
    <!-- 翻页控件 -->
    <div class="pagination-panel">
      <div class="pagination-info">
        <span>Page {{ currentPage }} of {{ totalPages }}</span>
      </div>
      <div class="progress-bar">
        <div class="progress" :style="{ width: progress + '%' }"></div>
      </div>
      <div class="page-buttons">
        <button @click="prevPage" :disabled="currentPage === 0">Previous</button>
        <button @click="nextPage" :disabled="currentPage === totalPages">Next</button>
      </div>
    </div>

    <div class="font-panel">
      <!-- 字体大小调整控件 -->
      <div class="size-bar">
        <label for="fontSize">正文大小：</label>
        <input type="range" id="fontSize" v-model.number="fontSize" min="10" max="30" step="1" />
        <span>{{ fontSize }} px</span>
      </div>

      <!-- 标题大小调整控件 -->
      <div class="size-bar">
        <label for="headingFontSize">标题大小：</label>
        <input
          type="range"
          id="headingFontSize"
          v-model.number="headingFontSize"
          min="20"
          max="40"
          step="1"
        />
        <span>{{ headingFontSize }} px</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { type Ref } from 'vue'

const emit = defineEmits(['prev-page', 'next-page'])
defineProps({
  currentPage: {
    type: Number,
    required: true,
  },
  totalPages: {
    type: Number,
    required: true,
  },
  progress: {
    type: Number,
    required: true,
  },
})
const headingFontSize: Ref<number> = defineModel<number>('headingFontSize', { required: true })
const fontSize: Ref<number> = defineModel<number>('fontSize', { required: true })

const prevPage = () => {
  emit('prev-page')
}
const nextPage = () => {
  emit('next-page')
}
</script>

<style scoped>
/*TODO 没居中*/
.floating-controls {
  position: fixed;
  top: 50%; /* 垂直居中 */
  left: 50%; /* 水平居中 */
  transform: translate(-50%, 20%); /* 将元素移动回居中的位置 */
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 10px; /* 压缩内边距 */
  box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  display: flex; /* 使用 flex 布局 */
  flex-direction: row; /* 横排 */
  align-items: flex-start; /* 垂直顶部对齐 */
  gap: 15px; /* 控件之间的水平间距 */
  width: auto; /* 压缩组件宽度 */
  height: auto; /* 自动适应高度 */
}

/* 翻页控件样式 */
.pagination-panel {
  display: flex;
  flex-direction: column; /* 翻页控件内部保持竖排 */
  align-items: center;
  margin-bottom: 0;
}

/* 字体调整面板 */
.font-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 0;
  height: 100%; /* 确保有足够的空间进行居中 */
  flex-grow: 1; /* 使 font-panel 填充剩余空间 */
}


.pagination-info {
  font-size: 12px; /* 压缩字体大小 */
  margin-bottom: 5px;
}

.progress-bar {
  width: 100%;
  height: 5px;
  background-color: #f0f0f0;
  border-radius: 3px;
  margin-bottom: 5px; /* 压缩进度条下的间距 */
}

.progress {
  height: 100%;
  background-color: #4caf50;
  border-radius: 3px;
  transition: width 0.3s;
}

.page-buttons button {
  padding: 5px 10px;
  margin: 0 5px;
  font-size: 14px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 3px;
}
</style>
