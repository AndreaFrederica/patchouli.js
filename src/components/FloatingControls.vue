<template>
  <!-- 折叠按钮 -->
  <button class="toggle-btn" @click.stop="toggleCollapse">
    {{ isCollapsed ? 'Expand' : 'Collapse' }}
  </button>
  <div
    class="floating-controls"
    :class="{ collapsed: isCollapsed }"
    v-if="!isCollapsed"
    @click.stop
  >
    <!-- 翻页控件 -->
    <div class="pagination-panel">
      <div class="pagination-info">
        <span>Page {{ currentPage }} of {{ totalPages }}</span>
      </div>
      <div class="progress-bar">
        <div class="progress" :style="{ width: progress + '%' }"></div>
      </div>
      <div class="page-buttons">
        <button @click.stop="prevPage" :disabled="currentPage === 0">Previous</button>
        <button @click.stop="nextPage" :disabled="currentPage === totalPages">Next</button>
      </div>
    </div>

    <!-- 字体大小调整控件 -->
    <div class="font-panel">
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
    <div>
      <!-- 模式切换按钮 -->
      <div class="mode-buttons">
        <button @click.stop="onPagedModeClick">{{ text_paged_mode_bottom }}</button>
        <button @click.stop="onViewModeClick">{{ text_view_mode_bottom }}</button>
      </div>
      <!-- About Widget (图标和信息部分) -->
      <br />
      <AboutWidget />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref, watch, type Ref } from 'vue';
import AboutWidget from './AboutWidget.vue';

const onReaderClick = inject('PatchouliReader_onReaderClick');
const emit = defineEmits(['prev-page', 'next-page', 'switch-view-mode', 'switch-paged_engine']);
const props = defineProps({
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
  enable_high_level_paged_engine: {
    type: Boolean,
    required: true,
  },
  enable_single_page_mode: {
    type: Boolean,
    required: true,
  },
});

const headingFontSize: Ref<number> = defineModel<number>('headingFontSize', { required: true });
const fontSize: Ref<number> = defineModel<number>('fontSize', { required: true });
const isCollapsed = ref<boolean>(false); // 控制折叠状态

const text_paged_mode_bottom = computed(() =>
  props.enable_high_level_paged_engine === true ? 'HighLevelPagedEngine' : 'LowLevelPagedEngine',
);
const text_view_mode_bottom = computed(() =>
  props.enable_single_page_mode === true ? 'SinglePage' : 'MultiPage',
);

watch([onReaderClick as Ref<boolean>], () => {
  if ((onReaderClick as Ref<boolean>).value === true) {
    toggleCollapse();
    (onReaderClick as Ref<boolean>).value = false;
    // console.log("2222",(onReaderClick as Ref<boolean>).value)
    // 清标志位
  }
});

const prevPage = () => {
  emit('prev-page');
};

const nextPage = () => {
  emit('next-page');
};

const onViewModeClick = () => {
  emit('switch-view-mode');
};

const onPagedModeClick = () => {
  emit('switch-paged_engine');
};

const toggleCollapse = () => {
  // console.log("1111")
  // console.log("1111",(onReaderClick as Ref<boolean>).value)
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

/* 更新后的浮动按钮样式 */
/* 初始按钮样式 */
.toggle-btn {
  position: fixed;
  top: 20px;
  right: 20px;
  background-color: rgba(169, 169, 169, 0.5); /* 灰色且半透明 */
  color: white;
  border: none;
  border-radius: 5px; /* 轻微圆角 */
  padding: 10px 20px;
  cursor: pointer;
  font-size: 16px;
  z-index: 1001; /* 确保按钮在其他元素之上 */
  transition: background-color 0.3s ease, opacity 0.3s ease; /* 添加平滑过渡 */
  opacity: 0.7; /* 初始状态下按钮稍微透明 */
}

/* 鼠标悬停时按钮样式 */
.toggle-btn:hover {
  background-color: #4caf50; /* 绿色背景 */
  opacity: 1; /* 取消透明度 */
}



.toggle-btn:focus {
  outline: none; /* 去除焦点框 */
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

.mode-buttons button {
  padding: 5px 10px;
  margin: 0 5px;
  font-size: 14px;
  background-color: #499a97;
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
