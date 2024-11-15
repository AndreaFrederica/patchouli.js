<template>
  <div ref="app" id="reader-app">
    <!-- 内容区域 -->
    <div id="content-container"></div>

    <!-- 浮动控件容器 -->
    <div class="floating-controls">
      <!-- 翻页控件 -->
      <pagination-panel
        :current-page="currentPage + 1"
        :total-pages="totalPages"
        :progress="progress"
        @prev-page="prevPage"
        @next-page="nextPage"
      />

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
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'

export default defineComponent({
  name: 'PatchouliReader',
  data() {
    return {
      pages: [] as HTMLElement[][], // 页面的元素数组，每页元素为 HTMLElement 数组
      currentPage: 0,
      maxHeight: 600, // 单页最大高度
      fontSize: 16, // 正文字体大小（默认16px）
      headingFontSize: 24, // 各级标题的字体大小（默认24px）
      shadowRoot: null as ShadowRoot | null, // Shadow DOM 根元素
    }
  },
  computed: {
    totalPages(): number {
      return this.pages.length
    },
    progress(): number {
      return ((this.currentPage + 1) / this.totalPages) * 100
    },
  },
  methods: {
    flattenDOM(node: Node): HTMLElement[] {
      let elements: HTMLElement[] = []
      node.childNodes.forEach((child) => {
        if (child.nodeType === Node.ELEMENT_NODE) {
          elements.push(child as HTMLElement)
          elements = elements.concat(this.flattenDOM(child))
        }
      })
      return elements
    },
    getPages(elements: HTMLElement[]): HTMLElement[][] {
      const pages: HTMLElement[][] = []
      const hiddenContainer = document.createElement('div')
      hiddenContainer.style.position = 'absolute'
      hiddenContainer.style.visibility = 'hidden'
      hiddenContainer.style.height = 'auto'

      this.shadowRoot?.appendChild(hiddenContainer)

      let currentPage: HTMLElement[] = []

      elements.forEach((element) => {
        hiddenContainer.appendChild(element.cloneNode(true))
        const elementHeight = hiddenContainer.scrollHeight

        if (elementHeight > this.maxHeight) {
          pages.push(currentPage)
          hiddenContainer.innerHTML = ''
          hiddenContainer.appendChild(element.cloneNode(true))
          currentPage = [element]
        } else {
          currentPage.push(element)
        }
      })

      if (currentPage.length > 0) {
        pages.push(currentPage)
      }

      this.shadowRoot?.removeChild(hiddenContainer)

      return pages
    },
    renderPage(pageIndex: number) {
      const contentContainer = this.shadowRoot?.querySelector('#content-container') as HTMLElement
      contentContainer.innerHTML = ''

      this.pages[pageIndex].forEach((element) => {
        contentContainer.appendChild(element.cloneNode(true))
      })
    },
    prevPage() {
      if (this.currentPage > 0) {
        this.currentPage--
        this.renderPage(this.currentPage)
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages - 1) {
        this.currentPage++
        this.renderPage(this.currentPage)
      }
    },
    adjustFontSize() {
      const contentContainer = this.shadowRoot?.querySelector('#content') as HTMLElement

      if (!contentContainer) return

      contentContainer.style.fontSize = `${this.fontSize}px`

      // const headings = contentContainer.querySelectorAll('h1, h2, h3, h4, h5, h6')
      // headings.forEach((heading) => {
      //   heading.style.fontSize = `${this.headingFontSize}px`
      // })
    },
    async loadContent() {
      try {
        const response = await fetch('content.html')
        const text = await response.text()

        const parser = new DOMParser()
        const doc = parser.parseFromString(text, 'text/html')

        const appContentContainer = this.$refs.app as HTMLElement
        this.shadowRoot = appContentContainer.attachShadow({ mode: 'open' })

        const title = doc.querySelector('title')?.innerText
        if (title) {
          document.title = title
        }

        const contentContainer = document.createElement('div')
        contentContainer.id = 'content-container'
        this.shadowRoot.appendChild(contentContainer)

        const linkTags = doc.querySelectorAll('link[rel="stylesheet"]')
        linkTags.forEach((link) => {
          const htmlLink = link as HTMLLinkElement // 类型断言，告诉 TypeScript 这个元素是 HTMLLinkElement
          if (!this.shadowRoot?.querySelector(`link[href="${htmlLink.href}"]`)) {
            const newLink = document.createElement('link')
            newLink.rel = 'stylesheet'
            newLink.href = htmlLink.href // 使用正确的类型
            this.shadowRoot?.appendChild(newLink)
          }
        })

        const styleTags = doc.querySelectorAll('style')
        styleTags.forEach((style) => {
          const styleElement = document.createElement('style')
          styleElement.innerHTML = style.innerHTML
          this.shadowRoot?.appendChild(styleElement)
        })

        const bodyContent = doc.querySelector('body')?.innerHTML || ''
        contentContainer.innerHTML = bodyContent

        const allElements = this.flattenDOM(contentContainer)
        this.pages = this.getPages(allElements)
        this.renderPage(this.currentPage)

        this.adjustFontSize()
      } catch (error) {
        console.error('加载内容失败:', error)
      }
    },
  },
  mounted() {
    // onMounted(() => {
    //   const appElement = this.$refs.app as HTMLDivElement // 断言为 HTMLDivElement
    //   this.maxHeight = appElement.offsetHeight
    //   console.log('App height:', this.maxHeight)
    //   this.loadContent()
    // })
    this.$nextTick(() => {
      // 通过 ref 获取 app 元素并获取它的高度
      const appElement = this.$refs.app as HTMLDivElement // 断言为 HTMLDivElement
      // this.maxHeight = appElement.offsetHeight
      //TODO 组件高度有问题 没有正确填满外部
      this.maxHeight = 400
      console.log('App height:', this.maxHeight)
      this.loadContent() // 加载外部内容
    })
  },
})
</script>

<style scoped>
/* 页面的样式 */
html,
body {
  height: 100%; /* 使html和body填满浏览器窗口 */
  margin: 0;
}

#reader-app {
  display: flex;
  flex-direction: column;
  height: 100%; /* 让 #app 占满父容器的高度 */
}

#content-container {
  margin: 0 auto;
  flex-grow: 1;
}

/* 浮动控件容器样式 */
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

/* 翻页控件样式 */
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
  /* 初始进度为 0 */
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
