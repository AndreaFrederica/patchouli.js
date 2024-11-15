<template>
  <div
    style="
      display: flex;
      justify-content: center;
      min-width: 100vw;
      min-height: 100vh;
      width: 100vw;
      height: 100vh;
      align-items: center;
    "
  >
    <div ref="app" id="reader-app">
      <!-- 内容区域 -->
      <div id="patchouli-content" ref="patchouliContent"></div>

      <!-- 浮动控件容器 -->
      <floating-controls
        v-model="fontSize"
        :current-page="currentPage + 1"
        :total-pages="totalPages"
        :progress="progress"
        :fontSize="fontSize"
        :headingFontSize="headingFontSize"
        @prev-page="prevPage"
        @next-page="nextPage"
        @update:fontSize="updateFontSize"
        @update:headingFontSize="updateHeadingFontSize"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onBeforeMount } from 'vue'
import FloatingControls from '@/components/FloatingControls.vue'

export default defineComponent({
  name: 'PatchouliReader',
  components: {
    FloatingControls, // 注册浮动控件组件
  },
  data() {
    return {
      rawElements: null as HTMLElement[] | null, //? 原始html内容 重新渲染时需要使用
      pages: [] as HTMLElement[][], // 页面的元素数组，每页元素为 HTMLElement 数组
      currentPage: 0,
      maxHeight: 600, // 单页最大高度
      readerWidth: 0,
      fontSize: 16, // 正文字体大小（默认16px）
      headingFontSize: 24, // 各级标题的字体大小（默认24px）
      shadowRoot: null as ShadowRoot | null, // Shadow DOM 根元素
      hiddenContainer: null as HTMLElement | null,
      readProgress: 0, //?阅读进度
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
  setup() {},
  methods: {
    // 监听窗口大小变化的函数
    handleResize() {
      this.readerWidth = window.innerWidth
      this.maxHeight = window.innerHeight
      // 在这里调用你需要执行的逻辑
      // console.log('窗口大小变化:', this.readerWidth, this.maxHeight)
      this.showPage()
    },
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
      let currentPage: HTMLElement[] = []
      elements.forEach((element) => {
        ;(this.hiddenContainer as HTMLElement).appendChild(element.cloneNode(true)) // 类型断言为 HTMLElement
        const elementHeight = (this.hiddenContainer as HTMLElement).scrollHeight
        if (elementHeight > this.maxHeight) {
          pages.push(currentPage)
          this.hiddenContainer.innerHTML = ''
          this.hiddenContainer.appendChild(element.cloneNode(true))
          currentPage = [element]
        } else {
          currentPage.push(element)
        }
      })
      if (currentPage.length > 0) {
        pages.push(currentPage)
        this.hiddenContainer.innerHTML = ''
      }
      return pages
    },
    renderPage(pageIndex: number) {
      const contentContainer = this.shadowRoot?.querySelector('#content-container') as HTMLElement
      contentContainer.innerHTML = ''

      this.pages[pageIndex].forEach((element) => {
        contentContainer.appendChild(element.cloneNode(true))
      })
      // 更新当前页码
      // console.log(pageIndex)
      this.readProgress = pageIndex / (this.totalPages - 1)
      // console.log('阅读进度：', this.readProgress)
      this.$emit('update:currentPage', pageIndex)
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
      if (!this.shadowRoot) return

      // 获取所有 div 元素并调整字体大小
      const divElements = this.shadowRoot.querySelectorAll('div') as NodeListOf<HTMLElement>
      divElements.forEach((div) => {
        // 调整正文的字体大小
        div.style.fontSize = `${this.fontSize}px`

        // 获取并调整该 div 内部的标题元素的字体大小
        const headings = div.querySelectorAll('h1, h2, h3, h4, h5, h6') as NodeListOf<HTMLElement>
        headings.forEach((heading) => {
          console.log(this.headingFontSize)
          heading.style.fontSize = `${this.headingFontSize}px`
        })
      })
    },
    updateFontSize(value: number) {
      // console.log(value)
      this.fontSize = value
      // this.adjustFontSize()
      this.showPage(null)
    },
    updateHeadingFontSize(value: number) {
      this.headingFontSize = value
      // this.adjustFontSize()
      // console.log(value)
      this.showPage(null)
    },
    showPage(pageIndex: number | null = null) {
      this.adjustFontSize()
      if (pageIndex === null) {
        this.currentPage = Math.floor(this.totalPages * this.readProgress)
      } else {
        this.currentPage = pageIndex
      }
      this.pages = this.getPages(this.rawElements as HTMLElement[])
      // console.log('发生了分页', this.pages.length)
      this.renderPage(this.currentPage)
    },
    async loadContent() {
      try {
        const response = await fetch('content.html')
        const text = await response.text()

        const parser = new DOMParser()
        const doc = parser.parseFromString(text, 'text/html')

        // const patchouliContainer = document.getElementById('patchouli-content')
        const patchouliContainer = this.$refs.patchouliContent as HTMLElement // 使用 ref 获取相对引用
        this.shadowRoot = patchouliContainer.attachShadow({ mode: 'open' })

        const title = doc.querySelector('title')?.innerText
        if (title) {
          document.title = title
        }

        this.hiddenContainer = document.createElement('div')
        this.hiddenContainer.style.position = 'absolute'
        this.hiddenContainer.style.visibility = 'hidden'
        this.hiddenContainer.style.height = 'auto'
        //! 使用MagicNumber防止溢出
        this.hiddenContainer.style.width = `${this.readerWidth * 0.9}px`

        this.shadowRoot.appendChild(this.hiddenContainer)
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
        this.rawElements = this.flattenDOM(contentContainer)
        this.showPage(0) //! 显示首页
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
      this.maxHeight = appElement.offsetHeight
      this.readerWidth = appElement.offsetWidth
      //TODO 组件高度有问题 没有正确填满外部
      // this.maxHeight = 400
      console.log('App height:', this.maxHeight)
      console.log('App width:', this.readerWidth)
      this.loadContent() // 加载外部内容
    })
    window.addEventListener('resize', this.handleResize)
    onBeforeMount(() => {
      window.removeEventListener('resize', this.handleResize)
    })
  },
})
</script>

<style scoped>
/* 页面的样式 */
#reader-app {
  display: flex; /* 使用 flexbox 布局 */
  flex-direction: column; /* 垂直排列子元素 */
  height: 100%; /* 让 #reader-app 占满父容器的高度 */
  width: 90%; /* 让 #reader-app 占满父容器的宽度 */

  /* justify-content: center; 垂直居中 */
  align-items: center; /* 水平居中 */
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
