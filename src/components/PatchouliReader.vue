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
        v-model:fontSize="fontSize"
        :current-page="currentPage + 1"
        :total-pages="totalPages"
        :progress="progress"
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
import { defineComponent, onMounted, onBeforeUnmount, ref, computed } from 'vue'
import FloatingControls from '@/components/FloatingControls.vue'

export default defineComponent({
  name: 'PatchouliReader',
  components: {
    FloatingControls, // 注册浮动控件组件
  },
  setup() {
    const rawElements = ref<HTMLElement[] | null>(null) // 原始html内容
    const pages = ref<HTMLElement[][]>([]) // 页面的元素数组，每页元素为 HTMLElement 数组
    const currentPage = ref(0)
    const maxHeight = ref(600) // 单页最大高度
    const readerWidth = ref(0)
    const fontSize = ref(16) // 正文字体大小（默认16px）
    const headingFontSize = ref(24) // 各级标题的字体大小（默认24px）
    const shadowRoot = ref<ShadowRoot | null>(null) // Shadow DOM 根元素
    const hiddenContainer = ref<HTMLElement | null>(null)
    const readProgress = ref(0) // 阅读进度
    const patchouliContent = ref<HTMLElement | null>(null)

    const totalPages = computed(() => pages.value.length)
    const progress = computed(() => ((currentPage.value + 1) / totalPages.value) * 100)

    const handleResize = () => {
      readerWidth.value = window.innerWidth
      maxHeight.value = window.innerHeight
      showPage() // 页面重新布局
    }

    const flattenDOM = (node: Node): HTMLElement[] => {
      let elements: HTMLElement[] = []
      node.childNodes.forEach((child) => {
        if (child.nodeType === Node.ELEMENT_NODE) {
          elements.push(child as HTMLElement)
          elements = elements.concat(flattenDOM(child))
        }
      })
      return elements
    }

    const getPages = (elements: HTMLElement[]): HTMLElement[][] => {
      const pages: HTMLElement[][] = []
      let currentPage: HTMLElement[] = []
      elements.forEach((element) => {
        ;(hiddenContainer.value as HTMLElement).appendChild(element.cloneNode(true)) // 类型断言为 HTMLElement
        const elementHeight = (hiddenContainer.value as HTMLElement).scrollHeight
        if (elementHeight > maxHeight.value) {
          pages.push(currentPage)
          ;(hiddenContainer.value as HTMLElement).innerHTML = ''
          ;(hiddenContainer.value as HTMLElement).appendChild(element.cloneNode(true))
          currentPage = [element]
        } else {
          currentPage.push(element)
        }
      })
      if (currentPage.length > 0) {
        pages.push(currentPage)
        ;(hiddenContainer.value as HTMLElement).innerHTML = ''
      }
      return pages
    }

    const renderPage = (pageIndex: number) => {
      const contentContainer = shadowRoot.value?.querySelector('#content-container') as HTMLElement
      contentContainer.innerHTML = ''
      pages.value[pageIndex].forEach((element) => {
        contentContainer.appendChild(element.cloneNode(true))
      })
      readProgress.value = pageIndex / (totalPages.value - 1)
    }
    const prevPage = () => {
      if (currentPage.value > 0) {
        currentPage.value--
        renderPage(currentPage.value)
      }
    }

    const nextPage = () => {
      if (currentPage.value < totalPages.value - 1) {
        currentPage.value++
        renderPage(currentPage.value)
      }
    }

    const adjustFontSize = () => {
      if (!shadowRoot.value) return

      // 查找已注入的样式
      let style = shadowRoot.value.querySelector('.font-size-styles')

      if (!style) {
        // 如果样式没有注入，则创建并注入样式
        style = document.createElement('style')
        style.className = 'font-size-styles' // 给样式添加一个唯一的 class
        shadowRoot.value.appendChild(style)
      }

      // 更新样式内容
      style.textContent = `
    div {
      font-size: ${fontSize.value}px !important;
    }
    div h1, div h2, div h3, div h4, div h5, div h6 {
      font-size: ${headingFontSize.value}px !important;
    }
  `
    }

    const updateFontSize = (value: number) => {
      fontSize.value = value
      showPage() // 页面更新
    }

    const updateHeadingFontSize = (value: number) => {
      headingFontSize.value = value
      showPage() // 页面更新
    }

    const showPage = (pageIndex: number | null = null) => {
      adjustFontSize()
      pages.value = getPages(rawElements.value as HTMLElement[])
      if (pageIndex === null) {
        const temp =Math.floor(totalPages.value * readProgress.value)
        // console.log("will to",temp,"max",totalPages.value)
        if(temp >= (totalPages.value - 1)){
          // console.log("too high")
          currentPage.value = (totalPages.value - 1)
        } else if(temp < 0){
          currentPage.value = 0
        }else{
        currentPage.value = temp
        }
      } else {
        currentPage.value = pageIndex
      }
      // console.log(currentPage.value)
      renderPage(currentPage.value)
    }

    const loadContent = async () => {
      try {
        const response = await fetch('content.html')
        const text = await response.text()

        const parser = new DOMParser()
        const doc = parser.parseFromString(text, 'text/html')

        const patchouliContainer = patchouliContent.value as HTMLElement
        shadowRoot.value = patchouliContainer.attachShadow({ mode: 'open' })

        const title = doc.querySelector('title')?.innerText
        if (title) {
          document.title = title
        }

        hiddenContainer.value = document.createElement('div')
        hiddenContainer.value.style.position = 'absolute'
        hiddenContainer.value.style.visibility = 'hidden'
        hiddenContainer.value.style.height = 'auto'
        hiddenContainer.value.style.width = `${readerWidth.value * 0.9}px`

        shadowRoot.value.appendChild(hiddenContainer.value)
        const contentContainer = document.createElement('div')
        contentContainer.id = 'content-container'
        contentContainer.style.width = `${readerWidth.value}px`
        shadowRoot.value.appendChild(contentContainer)

        const linkTags = doc.querySelectorAll('link[rel="stylesheet"]')
        linkTags.forEach((link) => {
          const htmlLink = link as HTMLLinkElement
          if (!shadowRoot.value?.querySelector(`link[href="${htmlLink.href}"]`)) {
            const newLink = document.createElement('link')
            newLink.rel = 'stylesheet'
            newLink.href = htmlLink.href
            shadowRoot.value?.appendChild(newLink)
          }
        })

        const styleTags = doc.querySelectorAll('style')
        styleTags.forEach((style) => {
          const styleElement = document.createElement('style')
          styleElement.innerHTML = style.innerHTML
          shadowRoot.value?.appendChild(styleElement)
        })

        const bodyContent = doc.querySelector('body')?.innerHTML || ''
        contentContainer.innerHTML = bodyContent
        rawElements.value = flattenDOM(contentContainer)
        showPage(0) //! 显示首页
      } catch (error) {
        console.error('加载内容失败:', error)
      }
    }

    // 生命周期钩子
    onMounted(() => {
      readerWidth.value = window.innerWidth
      maxHeight.value = window.innerHeight
      loadContent()
      window.addEventListener('resize', handleResize)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize)
    })

    return {
      rawElements,
      currentPage,
      totalPages,
      progress,
      fontSize,
      headingFontSize,
      prevPage,
      nextPage,
      updateFontSize,
      updateHeadingFontSize,
      showPage,
      patchouliContent,
    }
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
</style>
