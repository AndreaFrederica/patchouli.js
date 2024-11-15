<!-- FloatingControls.vue -->
<template>
  <div class="floating-controls">
    <!-- 翻页控件 -->
    <div class="pagination-panel">
      <div class="pagination-info">
        <span>Page {{ currentPage + 1 }} of {{ totalPages }}</span>
      </div>
      <div class="progress-bar">
        <div class="progress" :style="{ width: progress + '%' }"></div>
      </div>
      <div class="page-buttons">
        <button @click="prevPage" :disabled="currentPage === 0">Previous</button>
        <button @click="nextPage" :disabled="currentPage === totalPages - 1">Next</button>
      </div>
    </div>

    <!-- 字体大小调整控件 -->
    <div>
      <label for="fontSize">正文大小：</label>
      <input type="range" id="fontSize" v-model="fontSize" min="10" max="30" step="1" />
      <span>{{ fontSize }} px</span>
    </div>
    <div>
      <label for="headingFontSize">标题大小：</label>
      <input
        type="range"
        id="headingFontSize"
        v-model="headingFontSize"
        min="20"
        max="40"
        step="1"
      />
      <span>{{ headingFontSize }} px</span>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue'

export default defineComponent({
  name: 'FloatingControls',
  props: {
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
    fontSize: {
      type: Number,
      required: true,
    },
    headingFontSize: {
      type: Number,
      required: true,
    },
  },
  emits: ['prev-page', 'next-page', 'update:fontSize', 'update:headingFontSize'],
  methods: {
    prevPage() {
      this.$emit('prev-page')
    },
    nextPage() {
      this.$emit('next-page')
    },
    updateFontSize(value: number) {
      this.$emit('update:fontSize', value)
    },
    updateHeadingFontSize(value: number) {
      this.$emit('update:headingFontSize', value)
    },
  },
})
</script>

<style scoped>
.floating-controls {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  width: 250px;
}

.pagination-panel {
  margin-bottom: 15px;
}

.pagination-info {
  font-size: 14px;
  margin-bottom: 5px;
}

.progress-bar {
  width: 100%;
  height: 5px;
  background-color: #f0f0f0;
  border-radius: 3px;
  margin-bottom: 10px;
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
