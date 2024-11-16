<template>
  <div class="floating-controls" :class="{ collapsed: isCollapsed }">
    <!-- 折叠按钮 -->
    <button class="toggle-btn" @click="toggleCollapse">
      {{ isCollapsed ? 'Expand' : 'Collapse' }}
    </button>

    <!-- 翻页控件 -->
    <div class="pagination-panel" v-if="!isCollapsed">
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

    <!-- 字体大小调整控件 -->
    <div class="font-panel" v-if="!isCollapsed">
      <div class="size-bar">
        <label for="fontSize">正文大小：</label>
        <input type="range" id="fontSize" v-model.number="fontSize" min="10" max="50" step="1" />
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
          max="80"
          step="1"
        />
        <span>{{ headingFontSize }} px</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, type Ref } from 'vue';

const emit = defineEmits(['prev-page', 'next-page']);
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
});

const headingFontSize: Ref<number> = defineModel<number>('headingFontSize', { required: true });
const fontSize: Ref<number> = defineModel<number>('fontSize', { required: true });
const isCollapsed = ref<boolean>(false); // 控制折叠状态

const prevPage = () => {
  emit('prev-page');
};

const nextPage = () => {
  emit('next-page');
};

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value; // 切换折叠状态
};
</script>

<style scoped>
/*TODO 没居中*/
.floating-controls {
  position: fixed;
  bottom: 20px;
  right: 20px;
  /* transform: translate(20px, 20px); */
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 10px;
  box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 15px;
  width: auto;
  height: auto;
  transition: transform 0.3s ease; /* 添加动画效果 */
}

.floating-controls.collapsed {
  /* transform: translate(1600%, 900%);折叠时移到右边 */
  bottom: 20px;
  right: 80px;
}

.toggle-btn {
  position: absolute;
  top: 10px;
  /* left: 50%; */
  transform: translateX(0%);
  transform: translateY(-100%);
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 5%;
  padding: 8px 16px;
  cursor: pointer;
}

.pagination-panel,
.font-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.pagination-info {
  font-size: 12px;
  margin-bottom: 5px;
}

.progress-bar {
  width: 100%;
  height: 5px;
  background-color: #f0f0f0;
  border-radius: 3px;
  margin-bottom: 5px;
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

.size-bar {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.size-bar input {
  margin: 0 10px;
}
</style>
