<template>
  <div :style="containerStyles">
    <!-- 选项卡头部 -->
    <div class="tab-header">
      <button :class="{ active: currentTab === 'page' }" @click="currentTab = 'page'">文件</button>
      <button :class="{ active: currentTab === 'directory' }" @click="currentTab = 'directory'">
        书籍目录
      </button>
    </div>

    <!-- 内容区域 -->
    <div class="tab-content">
      <!-- 文件模式：显示请求到的 HTML 内容 -->
      <template v-if="currentTab === 'page'">
        <div v-if="loading">Loading...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <!-- 在这里添加 ref -->
        <div v-else v-html="htmlContent" ref="fileContentRef"></div>
      </template>

      <!-- 书籍目录模式：展示书籍目录列表 -->
      <template v-else-if="currentTab === 'directory'">
        <ul class="toc-list">
          <li v-for="item in toc!" :key="item.id">
            <!-- 点击书籍目录项时，触发 handleTocClick 事件 -->
            <a href="#" @click.prevent="handleTocClick(item)">
              {{ item.label }}
            </a>
          </li>
        </ul>
      </template>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, watch, computed, defineProps, defineEmits, nextTick } from 'vue'

// 定义书籍目录项类型（从 toc.ncx 解析得到）
export interface TocEntry {
  id: string
  playOrder: number
  label: string
  content: string
}

// 定义组件 Props
interface Props {
  // 文件模式下需要的 URL
  url?: string
  // 书籍目录模式下需要的书籍目录列表
  toc?: TocEntry[]
  // 控制组件是否可见
  visible: boolean
}

const props = defineProps<Props>()
// 声明一个 ref 用于绑定 HTML 内容区域（例如 v-html 绑定的 div）
const fileContentRef = ref<HTMLElement | null>(null)

// 定义 Emit，用于书籍目录模式选择书籍目录后通知母组件进行处理
const emit = defineEmits<{
  (e: 'tocSelect', contentUrl: string): void
  (e: 'dirSelect', path: string): void
  (e: 'fileSelect', fileName: string): void
}>()

// 内部状态：当前模式，'page' 或 'directory'
// 默认模式这里设为 'page'，也可根据实际需求修改
const currentTab = ref<'page' | 'directory'>('page')

// 容器样式，宽高为母组件 80%，根据 visible 控制显示隐藏
const containerStyles = computed(() => ({
  width: '100%',
  height: '100%',
  display: props.visible ? 'block' : 'none',
  overflow: 'auto',
}))

// ----- 文件模式状态管理 -----
const htmlContent = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

// 请求 HTML 的方法
const fetchHtmlContent = async (url: string) => {
  try {
    loading.value = true
    error.value = null
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`)
    }
    const text = await response.text()
    htmlContent.value = text
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (err: any) {
    error.value = err.message || 'Error fetching content'
    if (error.value !== null) htmlContent.value = error.value
  } finally {
    loading.value = false
  }

  nextTick(() => {
    if (fileContentRef.value !== null) {
      processFileLinks(fileContentRef.value)
    }
  })
}

// 组件挂载后，如果处于文件模式且 url 存在则请求 HTML 内容
onMounted(() => {
  if (currentTab.value === 'page' && props.url) {
    fetchHtmlContent(props.url)
  }
})

// 当 url 发生变化时重新请求内容（仅在文件模式下处理）
watch(
  () => props.url,
  (newUrl, oldUrl) => {
    if (currentTab.value === 'page' && newUrl && newUrl !== oldUrl) {
      fetchHtmlContent(newUrl)
    }
  },
)

// ----- 书籍目录模式处理 -----
// 当点击书籍目录项时，触发内部函数并 emit 'tocSelect' 事件，将目标 URL 通知母组件处理跳转
const handleTocClick = (item: TocEntry) => {
  emit('tocSelect', item.content)
}

/**
 * 处理文件模式下所有 a 标签的点击事件
 * @param container - 包含文件列表 HTML 内容的 DOM 容器
 */
const processFileLinks = (container: HTMLElement): void => {
  console.warn('准备替换Navigate的url')
  // 查询容器内所有带 href 的 a 标签
  const links = container.querySelectorAll<HTMLAnchorElement>('a[href]')
  links.forEach((link) => {
    const href = link.getAttribute('href')
    if (!href) return
    console.warn('url:', href)
    const lowerHref = href.toLowerCase()
    // 判断是否为目录链接：
    // 方案1：如果 href 以 "/" 结尾
    // 方案2：或者 href 中不包含 '.'，且链接文本以 "/" 结尾
    // const isDirectory =
    //   lowerHref.endsWith('/') ||
    //   (!lowerHref.includes('.') && (link.textContent?.trim().endsWith('/') ?? false))
    const isDirectory = link.textContent?.trim().endsWith('/') ?? false

    if (isDirectory) {
      // 目录类型：拦截点击事件，计算正确的目录路径并触发 "dirSelect"
      link.addEventListener('click', (event) => {
        event.preventDefault()
        let path = href
        // 去除前导斜杠（若存在）
        if (path.startsWith('/')) {
          path = path.substring(1)
        }
        console.log('点击了目录', path)
        // 触发目录选择事件，将正确的目录路径传递给母组件
        emit('dirSelect', path)
      })
    } else if (
      lowerHref.endsWith('.epub') ||
      lowerHref.endsWith('.txt') ||
      lowerHref.endsWith('.html') ||
      lowerHref.endsWith('.xhtml')
    ) {
      // 文件类型：拦截点击事件，计算正确的文件名并触发 "fileSelect"
      link.addEventListener('click', (event) => {
        event.preventDefault()
        let fileName = href
        if (fileName.startsWith('/')) {
          fileName = fileName.substring(1)
        }
        // 触发文件选择事件，将正确的文件名传递出去
        console.log('点击了文件', fileName)
        emit('fileSelect', fileName)
      })
    } else {
      // 其他文件被点击
      link.addEventListener('click', (event) => {
        event.preventDefault()
        let fileName = href
        if (fileName.startsWith('/')) {
          fileName = fileName.substring(1)
        }
        // 触发文件选择事件，将正确的文件名传递出去
        console.log('文件类型不支持')
      })
    }
    // 其他情况不做处理
  })
}
</script>

<style scoped>
/* 选项卡头部样式 */
.tab-header {
  display: flex;
  border-bottom: 1px solid #ccc;
  margin-bottom: 0.5em;
  color: var(--text-primary);
}
.tab-header button {
  flex: 1;
  padding: 0.5em;
  border: none;
  color: var(--text-primary);
  background-color: var(--floating-bg);
  cursor: pointer;
  outline: none;
  font-size: 1em;
}
.tab-header button.active {
  /* background-color: #fff; */
  border-bottom: 2px solid #007acc;
  font-weight: bold;
  color: var(--text-primary);
}

/* 内容区域 */
.tab-content {
  padding: 0.5em;
}

/* 书籍目录列表样式 */
.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.toc-list li {
  padding: 0.5em 0;
}
.toc-list a {
  text-decoration: none;
  color: #007acc;
  cursor: pointer;
}

/* 错误提示 */
.error {
  color: red;
}
</style>
