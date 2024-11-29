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
        <button @click.stop="prevPage" :disabled="currentPage === 1">Previous</button>
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
        <div class="row">
          <button class="mode-btn" @click.stop="onPagedModeClick">
            {{ text_paged_mode_bottom }}
          </button>
          <button class="mode-btn" @click.stop="onEngineModeClick">
            {{ text_engine_mode_bottom }}
          </button>
        </div>
        <div class="row">
          <button class="mode-btn" @click.stop="onViewModeClick">
            {{ text_view_mode_bottom }}
          </button>
        </div>
      </div>

      <!-- About Widget (图标和信息部分) -->
      <br />
      <AboutWidget />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref, watch, type Ref } from 'vue'
import AboutWidget from './AboutWidget.vue'

const onReaderClick = inject('PatchouliReader_onReaderClick')
const emit = defineEmits([
  'prev-page',
  'next-page',
  'switch-view-mode',
  'switch-paged_mode',
  'switch-paged_engine',
])
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
  enable_pointer_engine: {
    type: Boolean,
    required: true,
  },
})

const headingFontSize: Ref<number> = defineModel<number>('headingFontSize', { required: true })
const fontSize: Ref<number> = defineModel<number>('fontSize', { required: true })
const isCollapsed = ref<boolean>(false) // 控制折叠状态

const text_paged_mode_bottom = computed(() =>
  props.enable_high_level_paged_engine === true ? 'HighLevel' : 'LowLevel',
)
const text_view_mode_bottom = computed(() =>
  props.enable_single_page_mode === true ? 'SinglePage' : 'MultiPage',
)

const text_engine_mode_bottom = computed(() =>
  props.enable_pointer_engine === true ? 'Pointer' : 'SourceGen',
)

watch([onReaderClick as Ref<boolean>], () => {
  if ((onReaderClick as Ref<boolean>).value === true) {
    toggleCollapse()
    ;(onReaderClick as Ref<boolean>).value = false
    // console.log("2222",(onReaderClick as Ref<boolean>).value)
    // 清标志位
  }
})

const prevPage = () => {
  emit('prev-page')
}

const nextPage = () => {
  emit('next-page')
}

const onViewModeClick = () => {
  emit('switch-view-mode')
}

const onPagedModeClick = () => {
  emit('switch-paged_mode')
}

const onEngineModeClick = () => {
  emit('switch-paged_engine')
}

const toggleCollapse = () => {
  // console.log("1111")
  // console.log("1111",(onReaderClick as Ref<boolean>).value)
  isCollapsed.value = !isCollapsed.value // 切换折叠状态
}
</script>

<style scoped>
/* 通用样式 */
.floating-controls {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background-color: rgba(255, 255, 255, 0.9); /* 默认浅色背景 */
  border-radius: 8px;
  padding: 10px;
  box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 15px;
  width: 300px;
  height: auto;
  transition:
    transform 0.3s ease,
    background-color 0.3s ease; /* 添加背景色过渡效果 */
}

.floating-controls.collapsed {
  bottom: 20px;
  right: 80px;
}

.toggle-btn {
  position: fixed;
  top: 20px;
  right: 20px;
  background-color: rgba(169, 169, 169, 0.5); /* 灰色且半透明 */
  color: white;
  border: none;
  border-radius: 5px;
  padding: 10px 20px;
  cursor: pointer;
  font-size: 16px;
  z-index: 1001;
  transition:
    background-color 0.3s ease,
    opacity 0.3s ease;
  opacity: 0.7;
}

.toggle-btn:hover {
  background-color: #4caf50; /* 绿色背景 */
  opacity: 1;
}

.toggle-btn:focus {
  outline: none;
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
  background-color: #f0f0f0; /* 浅色进度条背景 */
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
  width: 80px;
}

.mode-buttons {
  display: flex;
  flex-direction: column; /* 按行排列 */
  align-items: center; /* 水平居中 */
  gap: 10px; /* 行间距 */
}

.row {
  display: flex;
  justify-content: center; /* 每行中的按钮水平居中 */
  gap: 10px; /* 按钮之间的间距 */
}

.mode-btn {
  padding: 8px 15px; /* 按钮内边距 */
  font-size: 14px; /* 字体大小 */
  background-color: #499a97; /* 背景色 */
  color: white; /* 文字颜色 */
  border: none; /* 移除边框 */
  border-radius: 5px; /* 圆角 */
  cursor: pointer; /* 鼠标样式 */
  /* transition:
    background-color 0.3s ease,
    transform 0.2s ease; 动效 */
  width: 100px;
}

.mode-btn:hover {
  background-color: #387e7b; /* 鼠标悬停时的背景色 */
  /* transform: scale(1.05); 悬停时稍微放大 */
}

.mode-btn:active {
  background-color: #285e5d; /* 点击时的背景色 */
  /* transform: scale(0.95); 点击时稍微缩小 */
}

@media (max-width: 600px) {
  .mode-buttons {
    flex-direction: column; /* 小屏幕时垂直排列 */
    align-items: center; /* 垂直居中对齐 */
  }

  .mode-btn {
    width: 100%; /* 按钮在小屏幕上占满宽度 */
  }
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

/* 暗模式样式 */
@media (prefers-color-scheme: dark) {
  .floating-controls {
    background-color: rgba(45, 45, 45, 0.9); /* 暗模式背景 */
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.8);
  }

  .toggle-btn {
    background-color: rgba(100, 100, 100, 0.7); /* 按钮浅灰色背景 */
    color: #f0f0f0; /* 按钮文字浅色 */
  }

  .toggle-btn:hover {
    background-color: #3a7f3a; /* 深绿色 */
  }

  .pagination-info {
    color: #f0f0f0; /* 浅色文字 */
  }

  .progress-bar {
    background-color: #303030; /* 暗色进度条背景 */
  }

  .progress {
    background-color: #81c784; /* 浅绿色 */
  }

  .page-buttons button {
    background-color: #357a38; /* 深绿色 */
  }

  .mode-buttons button {
    background-color: #276a68; /* 深蓝绿色 */
  }

  .size-bar label,
  .size-bar span {
    color: #f0f0f0; /* 浅色文字 */
  }
}
</style>
