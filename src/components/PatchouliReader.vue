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
    @click="handleClick"
    @touchstart="handleTouchStart"
    @touchend="handleTouchEnd"
  >
    <div id="patchouli-reader" ref="patchouliReader">
      <!-- 内容区域 -->
      <div id="patchouli-content" ref="patchouliContent"></div>

      <!-- 浮动控件容器 -->
      <floating-controls
        :current-page="currentPage + 1"
        :total-pages="totalPages"
        :progress="displayReadProgress"
        :enable_high_level_paged_engine="flag_high_level_paged_engine"
        :enable_single_page_mode="flag_single_page_mode"
        :enable_pointer_engine="flag_use_pointer_engine"
        v-model:fontSize="fontSize"
        v-model:headingFontSize="headingFontSize"
        @prev-page="prevPage"
        @next-page="nextPage"
        @switch-paged_mode="switchPagedMode"
        @switch-view-mode="switchViewMode"
        @switch-paged_engine="switchPagedEngine"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import {
  onMounted,
  onBeforeUnmount,
  ref,
  computed,
  nextTick,
  watch,
  provide,
  inject,
  onDeactivated,
} from 'vue'
import FloatingControls from '@/components/FloatingControls.vue'

const globalTestDivCounter = ref(0)
const rawDOMtree = ref<HTMLElement>()
const rawElements = ref<HTMLElement[]>() // 原始html内容 被展平了已经
// let rawElements: undefined | HTMLElement[] = undefined; // 原始html内容 这里面不知道为什么开启高级切分器后有可能进屎
const pages = ref<HTMLElement[][]>([]) // 页面的元素数组，每页元素为 HTMLElement 数组
const currentPage = ref(0)
const maxHeight = ref(600) // 单页最大高度
const readerWidth = ref(0)
const last_reader_width = ref(0)
const fontSize = ref(16) // 正文字体大小（默认16px）
const headingFontSize = ref(24) // 各级标题的字体大小（默认24px）
const shadowRoot = ref<ShadowRoot>() // Shadow DOM 根元素
const hiddenContainer = ref<HTMLElement>()
const readProgress = ref(0) // 阅读进度
const patchouliContent = ref<HTMLElement>()
const readerContainer = ref<HTMLElement>()
const patchouliReader = ref<HTMLElement>()
const cacheContainer = ref<HTMLElement>()

const touchStartX = ref(0)
const touchEndX = ref(0)
const touchStartTime = ref<number | null>(null) // 记录触摸开始时间
const LONG_PRESS_THRESHOLD = ref(500) // 长按阈值（毫秒）
const resizeObserver = ref<ResizeObserver>()
const totalPages = computed(() => pages.value.length)
const displayReadProgress = computed(() => readProgress.value * 100)

// 高阶分页支持
const flag_high_level_paged_engine = ref(true)
//TODO 依赖于深拷贝运行 但是不启用目前也没有去掉深拷贝（安全性）
const flag_single_page_mode = ref(false)
// TODO 未全部完成 单页流式阅读器
// 启用激进分页模式 目前一直开着
const flag_aggressive_paging_engine = ref(false)
// 激进分页模式的阈值 小于这个就进行激进分页
const aggressive_paging_threshold = 0.95 // 默认值为 0.9
// 分页模式的阈值 小于这个就进行分页
const paging_threshold = 0.95 // 默认值为 0.9
const flag_flatten_DOM = ref(true)
// 依赖展平dom树的方法来实现渲染
// TODO doing 应当实现一个不依赖dom展平的分页器 PointerEngine正在开发
const flag_use_pointer_engine = ref(false)

const flag_auto_next = ref(true)
// 允许自动切换章节

const onReaderClick = ref(false)
provide('PatchouliReader_onReaderClick', onReaderClick)

const flag_auto_prev = ref(false)
// const prevChapter = inject<() => void>('prevChapter')
// const nextChapter = inject<() => void>('nextChapter')
// const flag_auto_prev = inject<Ref<boolean>>('flag_auto_prev')
// 需要在父级实现

const handleResize = () => {
  if (patchouliReader.value) {
    readerWidth.value = patchouliReader.value.offsetWidth
    last_reader_width.value = readerWidth.value
    maxHeight.value = patchouliReader.value.offsetHeight
  }
}

// 点击翻页处理函数
const handleClick = (event: MouseEvent) => {
  if (!patchouliReader.value) return // 如果组件未挂载，直接返回

  // 检查是否存在选中的文本
  const selection = window.getSelection()
  if (selection && selection.toString().length > 0) {
    return // 如果有选中文本，则忽略点击事件
  }

  // 获取组件的位置和大小
  const rect = patchouliReader.value.getBoundingClientRect()

  // 获取点击位置相对于组件的坐标
  const clickXInComponent = event.clientX - rect.left
  // console.log('clickX:', event.clientX)
  // console.log('clickXInComponent:', clickXInComponent)

  const edgeWidth = rect.width * 0.2 // 边缘区域为组件宽度的 20%

  // 判断点击位置是否在左侧边缘区域
  if (clickXInComponent < edgeWidth) {
    prevPage() // 点击左侧20%区域
  }
  // 判断点击位置是否在右侧边缘区域
  else if (clickXInComponent > rect.width - edgeWidth) {
    nextPage() // 点击右侧20%区域
  }
  // 如果点击位置在中间部分
  else {
    onReaderClick.value = true // 非边缘区域点击
  }
}
const handleWheel = (event: WheelEvent) => {
  if (flag_single_page_mode.value !== true) {
    //鼠标滚轮事件
    if (event.deltaY > 0) {
      // 向下滚动
      nextPage()
    } else if (event.deltaY < 0) {
      // 向上滚动
      prevPage()
    }
  } else {
    // 单页模式下转为计算阅读进度
    const scrollTop = window.scrollY // 当前页面顶部滚动位置
    const scrollHeight = document.documentElement.scrollHeight // 整个文档高度
    const clientHeight = document.documentElement.clientHeight // 可视区域高度

    // 确保不会出现分母为 0 的情况
    readProgress.value =
      scrollHeight > clientHeight ? Math.min(scrollTop / (scrollHeight - clientHeight), 1) : 1
  }
}

// 触摸滑动开始处理函数
const handleTouchStart = (event: TouchEvent) => {
  touchStartX.value = event.touches[0].clientX
  touchStartTime.value = Date.now() // 记录触摸开始时间
}

// 触摸滑动结束处理函数
const handleTouchEnd = (event: TouchEvent) => {
  touchEndX.value = event.changedTouches[0].clientX
  const touchEndTime = Date.now() // 记录触摸结束时间

  const duration = touchEndTime - (touchStartTime.value ?? touchEndTime)

  if (duration >= LONG_PRESS_THRESHOLD.value) {
    handleLongPress() // 长按事件
  } else {
    handleSwipe() // 滑动或点击事件
  }

  // 清理状态
  touchStartX.value = 0
  touchEndX.value = 0
  touchStartTime.value = 0
}

// 滑动处理函数
const handleSwipe = () => {
  if (touchStartX.value === 0 || touchEndX.value === 0) return

  const swipeDistance = touchEndX.value - touchStartX.value
  const swipeThreshold = 100 // 设置滑动的阈值

  if (swipeDistance > swipeThreshold) {
    prevPage() // 右滑（向右滑动）
  } else if (swipeDistance < -swipeThreshold) {
    nextPage() // 左滑（向左滑动）
  }
}

// 长按处理函数
const handleLongPress = () => {
  console.log('长按事件触发')
  // 在此处理长按事件逻辑
}

const getParentTextContent = (element: HTMLElement): string => {
  let directText = ''
  Array.from(element.childNodes).forEach((child) => {
    if (child instanceof Text) {
      directText += child.nodeValue?.trim() || ''
    }
  })
  return directText
}

const hasOnlyRubyChild = (node: HTMLElement): boolean => {
  return Array.from(node.childNodes).every(
    (childNode) => childNode.nodeType === Node.ELEMENT_NODE && childNode.nodeName === 'RUBY',
  )
}

const flattenDOM = (
  node: HTMLElement,
  flattenCompletely: boolean,
  parentClassPath = '',
): HTMLElement[] => {
  const elements: HTMLElement[] = []
  if (flag_flatten_DOM.value === false || flag_single_page_mode.value) {
    elements.push(node)
    return elements
  } else {
    node.childNodes.forEach((child) => {
      if (child.nodeType === Node.ELEMENT_NODE) {
        const element = child as HTMLElement

        // 如果当前元素是 <ruby> 元素，直接保留
        if (element.nodeName === 'RUBY') {
          elements.push(element)
          return
        }

        // 如果没有子元素，跳过展平，直接保留该元素
        if (!element.childNodes.length) {
          elements.push(element)
          return
        }

        // 如果子元素只有 <ruby> 元素，保留 <ruby> 元素及其结构
        // const hasOnlyRubyChild = Array.from(element.childNodes).every(
        //   (childNode) => childNode.nodeName === 'RUBY',
        // )
        if (hasOnlyRubyChild(element)) {
          elements.push(element)
          return
        }

        if (flattenCompletely) {
          // 处理完全展平逻辑
          const currentClass = (node as HTMLElement).className || ''
          const sanitizedClass = currentClass
            .replace(/[^a-zA-Z0-9_-]/g, '-')
            .replace(/^-+|-+$/g, '')

          const classPath = parentClassPath
            ? `${parentClassPath}__${sanitizedClass}`
            : sanitizedClass

          if (classPath) {
            element.className = `${element.className} parent-${classPath}`
          }

          const clonedElement = element.cloneNode(false) as HTMLElement // 浅克隆移除子节点
          clonedElement.innerText = getParentTextContent(element)
          elements.push(clonedElement)
          elements.push(...flattenDOM(element, flattenCompletely, classPath))
        } else {
          // 保留嵌套关系，仅添加母节点本身
          elements.push(element)
        }
      }
    })
  }
  return elements
}
const cloneElementStyleAndClass = (element: HTMLElement): HTMLElement => {
  // 创建一个新的元素（与原始元素相同的标签类型）
  const cloned = document.createElement(element.tagName) as HTMLElement

  // 复制原始元素的所有类
  cloned.className = element.className

  // 复制原始元素的内联样式
  cloned.style.cssText = element.style.cssText

  // 移除 id 属性，避免重复
  cloned.removeAttribute('id')

  return cloned
}
// 示例
// const original = document.querySelector("p") as HTMLParagraphElement;
// original && document.body.appendChild(cloneElementWithStyleAndClass(original)!);
const waitForResourceSync = (htmlElement: HTMLElement, timeout = 5000) => {
  // 检查是否传入有效的 HTMLElement
  if (!htmlElement || !(htmlElement instanceof HTMLElement)) {
    console.error('传入的对象不是有效的 HTML 元素')
    return 'error'
  }

  // 检查是否为图片元素
  if (htmlElement.tagName.toLowerCase() !== 'img') {
    return 'success'
  }

  let flag = false // 标志变量，表示资源加载状态
  let result = 'timeout' // 默认返回超时
  const startTime = Date.now() // 记录开始时间

  const wrappedWaitForResource = async () => {
    if ((htmlElement as HTMLImageElement).complete) {
      console.log('图片已经加载完成')
      result = 'success' // 图片已经加载完成
      flag = true
      return
    }

    try {
      await new Promise<void>((resolve, reject) => {
        htmlElement.onload = () => {
          console.log('图片加载成功')
          resolve()
        }
        htmlElement.onerror = () => {
          console.error('图片加载失败')
          reject(new Error('图片加载失败'))
        }
      })
      result = 'success' // 图片加载成功
    } catch (err) {
      console.error(err)
      result = 'error' // 图片加载失败
    } finally {
      flag = true // 标记操作完成
    }
  }

  // 调用异步函数
  wrappedWaitForResource()

  // 阻塞当前线程，轮询 flag 状态，并进行延迟
  const delay = performance.now() // 记录延迟起始时间
  while (!flag && Date.now() - startTime < timeout) {
    // 添加微小延迟，防止完全占用主线程
    while (performance.now() - delay < 1) {} // 延迟 20ms，减轻 CPU 负担
  }

  // 如果超时，返回超时状态
  if (!flag) {
    console.warn('资源加载超时')
  }

  return result // 返回最终状态
}

const hasOnlyText = (element: HTMLElement) =>
  element.childNodes.length === 1 && element.childNodes[0].nodeType === Node.TEXT_NODE

// 最简单的高阶切分算法 没考虑div套娃 需要更多高级切分算法做补充
const getParagraphs_Simple = (
  element: HTMLElement,
  pointer_div: HTMLElement | undefined = undefined,
): [HTMLElement, HTMLElement] | undefined => {
  const part1 = cloneElementStyleAndClass(element)
  const part2 = cloneElementStyleAndClass(element)
  if (!hasOnlyText(element) || element.tagName.toLowerCase() === 'img') {
    return undefined
  }
  let container: undefined | HTMLElement = undefined
  // 获取原始文本内容
  const text = element.innerText
  if (pointer_div === undefined) {
    container = hiddenContainer.value as HTMLElement
  } else {
    container = pointer_div
  }
  // 将 part1 添加到隐藏容器中
  container.appendChild(part1)
  // 设置 part1 的内容，并进行分页检测
  let part1Text = ''
  for (const char of text) {
    part1Text += char // 向 part1 添加字符
    part1.innerText = part1Text // 设置 part1 的文本内容

    // 检查是否超过分页阈值
    if (
      (hiddenContainer.value as HTMLElement).scrollHeight / maxHeight.value >=
      aggressive_paging_threshold
    ) {
      // 超过阈值，分页结束
      //TODO 不知道为什么这边不打补丁会发电
      if (flag_use_pointer_engine.value) container.removeChild(part1)
      break
    }
  }
  if (part1Text.length <= 5) return
  // 将剩余的文本交给 part2
  part1Text = part1Text.substring(0, part1Text.length - 1)
  part1.innerText = part1Text
  const remainingText = text.slice(part1Text.length)
  part2.innerText = remainingText

  // 注入最高级别的CSS，确保缩进取消
  part2.style.padding = '0'
  part2.style.margin = '0'
  part2.style.textIndent = '0' // 确保取消缩进
  part2.style.whiteSpace = 'normal' // 确保文本按照正常格式显示

  return [part1, part2] // 返回两个分页部分
}

const getPages = (elements?: HTMLElement[]): HTMLElement[][] => {
  if (elements === undefined) return []

  if (flag_single_page_mode.value) {
    console.log('使用流式阅读器')
    // 单页流式阅读器
    return pagedEngineFlowing(elements, <HTMLElement>hiddenContainer.value)
  } else if (flag_high_level_paged_engine.value) {
    console.log('使用高阶分页引擎')
    if (flag_use_pointer_engine.value) {
      console.log('使用Pointer版本高阶分页引擎')
      return pagedEnginePointerHighLevel(
        elements,
        <HTMLElement>hiddenContainer.value,
        maxHeight,
        paging_threshold,
      )
    } else {
      console.log('使用SourceGen版本高阶分页引擎')
      return pagedEngineSourceGenHighLevel(elements, <HTMLElement>hiddenContainer.value)
    }
  } else {
    console.log('使用低阶分页引擎')
    if (flag_use_pointer_engine.value) {
      console.log('使用Pointer版本低阶分页引擎')
      return pagedEnginePointerLowLevel(elements, <HTMLElement>hiddenContainer.value)
    } else {
      console.log('使用SourceGen版本低阶分页引擎')
      return pagedEngineSourceGenLowLevel(elements, <HTMLElement>hiddenContainer.value)
    }
  }
}

const pagedEngineFlowing = (
  elements: HTMLElement[],
  tester_container: HTMLElement,
): HTMLElement[][] => {
  const pages: HTMLElement[][] = []
  const currentPage: HTMLElement[] = []
  elements.forEach((element) => {
    currentPage.push(element)
  })
  pages.push(currentPage)
  tester_container.innerHTML = ''
  return pages
}

const pagedEngineSourceGenHighLevel = (
  elements: HTMLElement[],
  tester_container: HTMLElement,
): HTMLElement[][] => {
  const pages: HTMLElement[][] = []
  let currentPage: HTMLElement[] = []
  let flag_high_level_paged = false
  let i = 0
  let end = elements.length
  while (i < end) {
    // if (flag_high_level_paged) i--; // i++最先计算 发生插入后需要用这个修正？
    tester_container.appendChild(elements[i].cloneNode(true)) // 类型断言为 HTMLElement
    const image_load_status = waitForResourceSync(elements[i], 10) // 等待图片加载
    // 没有图片或加载成功为 success 失败为 error 或者timeout 这里需要优化 避免循环查找
    let now_hight = tester_container.scrollHeight
    if (image_load_status !== 'success') {
      console.warn('图片加载出现异常')
      now_hight = maxHeight.value // 强行结束这一页
    }
    if (now_hight <= maxHeight.value * paging_threshold) {
      // 能塞得进去 往这一页里面塞东西
      currentPage.push(elements[i])
      i++
    } else {
      // 碰撞测试失败 塞不进去 开始高级分页 或者结束一页
      tester_container.removeChild(tester_container.lastChild as HTMLElement) // 清理失败节点 给高级分页流出空间
      let result = undefined // 性能优化 避免重复调用高级分页算法
      if (flag_high_level_paged === false) result = getParagraphs_Simple(elements[i])
      // console.log(flag_high_level_paged !== true && result !== undefined);
      if (result !== undefined) {
        // 可以进行高级分页
        flag_high_level_paged = true
        currentPage.push(<HTMLElement>result[0].cloneNode(true))
        elements.splice(i + 1, 0, <HTMLElement>result[1].cloneNode(true))
        i++
        end++
      } else {
        // 结束一页 高级分页失败了也会回退到这里
        let flag_img = false
        if (currentPage.length === 0) {
          // 高级分页引擎也无法处理的东西 比如说图片
          currentPage.push(elements[i])
          flag_img = true
          i++
        }
        if (tester_container.scrollHeight !== 0 || flag_img === true) {
          pages.push(currentPage)
        } else {
          console.log('存在空页 已剔除')
        }
        currentPage = []
        tester_container.innerHTML = ''
        flag_high_level_paged = false
      }
    }
  }
  if (currentPage.length > 0) {
    // 最后一页
    pages.push(currentPage)
  }
  tester_container.innerHTML = ''
  return pages
}

const pagedEngineSourceGenLowLevel = (
  elements: HTMLElement[],
  tester_container: HTMLElement,
): HTMLElement[][] => {
  const pages: HTMLElement[][] = []
  let currentPage: HTMLElement[] = []
  elements.forEach((element) => {
    tester_container.appendChild(element.cloneNode(true))
    const elementHeight = tester_container.scrollHeight
    if (elementHeight > maxHeight.value * paging_threshold) {
      pages.push(currentPage)
      tester_container.innerHTML = ''
      tester_container.appendChild(element.cloneNode(true))
      currentPage = [element]
    } else {
      currentPage.push(element)
    }
  })
  if (currentPage.length > 0) {
    // 最后一页
    pages.push(currentPage)
  }
  tester_container.innerHTML = ''
  return pages
}

const nodeIsLeaf = (node: HTMLElement): boolean => {
  const isTextOrAllowedNode = (child: Node): boolean => {
    // 检测子节点是否为文本节点或特定允许的节点类型
    return (
      child.nodeType === Node.TEXT_NODE ||
      (child.nodeType === Node.ELEMENT_NODE &&
        (child.nodeName === 'IMG' || (child as HTMLElement).className === 'duokan-image-single'))
    )
  }

  // 检测当前节点是否为叶子节点
  if (node.childNodes.length === 1 && isTextOrAllowedNode(node.childNodes[0])) {
    // 单个文本节点或允许的类型
    return true
  } else if (node.nodeName === 'IMG') {
    // 图片节点
    return true
  } else if (node.className === 'duokan-image-single') {
    // 多看图片节点
    return true
  } else if (hasOnlyRubyChild(node)) {
    // 带注音的文本
    return true
  } else if (Array.from(node.childNodes).every(isTextOrAllowedNode)) {
    // 只包含允许的节点类型
    return true
  } else if (node.nodeName === 'BR') {
    // 单独的 BR 标签也视为叶子节点
    return true
  } else if (node.nodeName === 'P') {
    return true
  } else {
    return false
  }
}

const pagedEnginePointerLowLevel = (
  elements: HTMLElement[],
  tester_container: HTMLElement,
): HTMLElement[][] => {
  const pages: HTMLElement[][] = []
  const currentPage: HTMLElement[] = []
  const pointer_div: [undefined | HTMLElement] = [undefined]

  elements.forEach((element) => {
    pagedEnginePointerLowLevelCore(
      element,
      tester_container,
      pages,
      currentPage,
      undefined,
      pointer_div,
    )
  })

  // 如果有剩余的元素未处理完，将其作为最后一页
  if ((pointer_div[0] as HTMLElement).hasChildNodes) {
    pages.push([(pointer_div[0] as HTMLElement).cloneNode(true) as HTMLElement])
  }
  tester_container.innerHTML = ''
  return pages
}

const pagedEnginePointerLowLevelCore = (
  element: HTMLElement,
  tester_container: HTMLElement,
  pages_list: HTMLElement[][],
  current_page: HTMLElement[],
  div_template: HTMLElement | undefined,
  pointer_div: [HTMLElement | undefined],
): void => {
  let next_div_template: HTMLElement | undefined = undefined
  if (nodeIsLeaf(element)) {
    if (current_page.length === 0 && pointer_div[0] === undefined) {
      // 第一次调用时获取新的操作指针
      const neo_pointer = (div_template as HTMLElement).cloneNode(true)
      tester_container.appendChild(neo_pointer)
      pointer_div[0] = <HTMLElement>neo_pointer
    }
    ;(pointer_div[0] as HTMLElement).appendChild(element.cloneNode(true))

    if (tester_container.scrollHeight <= maxHeight.value * paging_threshold) {
      // 什么都不做
    } else {
      ;(pointer_div[0] as HTMLElement).removeChild(
        (pointer_div[0] as HTMLElement).lastChild as HTMLElement,
      )
      current_page.push((pointer_div[0] as HTMLElement).cloneNode(true) as HTMLElement)
      pages_list.push(cloneHTMLElementList(current_page)) // 保存当前页
      current_page.length = 0 // 清空当前页，保留引用
      tester_container.innerHTML = '' // 清空测试容器
      // 获取新的操作指针
      const neo_pointer = (div_template as HTMLElement).cloneNode(true)
      tester_container.appendChild(neo_pointer)
      pointer_div[0] = <HTMLElement>neo_pointer
      neo_pointer.appendChild(element)
      // current_page.push(<HTMLElement>neo_pointer) // 开始新页
    }
  } else {
    if (div_template === undefined) {
      //? 此元素是根元素 初始化div模板
      next_div_template = cloneElementStyleAndClass(element)
    } else {
      // 不是根节点
      const last_template = div_template.cloneNode(true)
      next_div_template = last_template.appendChild(cloneElementStyleAndClass(element))
    }
    Array.from(element.childNodes).forEach((node) => {
      if (node instanceof HTMLElement) {
        pagedEnginePointerLowLevelCore(
          node,
          tester_container,
          pages_list,
          current_page,
          next_div_template,
          pointer_div,
        )
      }
    })
  }
}

const pagedEnginePointerHighLevel = (
  elements: HTMLElement[],
  tester_container: HTMLElement,
  maxHeight: { value: number },
  paging_threshold: number,
): HTMLElement[][] => {
  const pages: HTMLElement[][] = []
  const currentPage: HTMLElement[] = []

  // 包装一个对象来保存 part2
  const savedPart2Container = { part2: undefined as HTMLElement | undefined }
  const pointer_div: [undefined | HTMLElement] = [undefined]

  elements.forEach((element) => {
    pagedEnginePointerHighLevelCore(
      element,
      tester_container,
      pages,
      currentPage,
      maxHeight,
      paging_threshold,
      savedPart2Container, // 传递包装的 savedPart2
      undefined,
      pointer_div,
    )
  })

  // 如果最后有剩余的内容，保存到 pages
  if ((pointer_div[0] as HTMLElement).hasChildNodes) {
    pages.push([(pointer_div[0] as HTMLElement).cloneNode(true) as HTMLElement])
  }

  tester_container.innerHTML = '' // 清理测试容器
  return pages
}

const pagedEnginePointerHighLevelCore = (
  element: HTMLElement,
  tester_container: HTMLElement,
  pages_list: HTMLElement[][],
  current_page: HTMLElement[],
  maxHeight: { value: number },
  paging_threshold: number,
  savedPart2Container: { part2: HTMLElement | undefined }, // 保存 part2 的对象
  div_template: HTMLElement | undefined,
  pointer_div: [HTMLElement | undefined],
): void => {
  // 如果 savedPart2 存在，优先处理它
  while (savedPart2Container.part2 !== undefined) {
    // console.log('存在part2 ')
    pagedEnginePointerHighLevelCoreProcessElement(
      savedPart2Container.part2,
      tester_container,
      pages_list,
      current_page,
      maxHeight,
      paging_threshold,
      savedPart2Container,
      div_template,
      pointer_div,
    )
  }
  // 正常分页处理
  // console.log('正常处理 ')
  pagedEnginePointerHighLevelCoreProcessElement(
    element,
    tester_container,
    pages_list,
    current_page,
    maxHeight,
    paging_threshold,
    savedPart2Container,
    div_template,
    pointer_div,
  )
}

// 处理元素的具体分页逻辑
const pagedEnginePointerHighLevelCoreProcessElement = (
  element: HTMLElement,
  tester_container: HTMLElement,
  pages_list: HTMLElement[][],
  current_page: HTMLElement[],
  maxHeight: { value: number },
  paging_threshold: number,
  savedPart2Container: { part2: HTMLElement | undefined },
  div_template: HTMLElement | undefined,
  pointer_div: [HTMLElement | undefined],
): void => {
  let next_div_template: HTMLElement | undefined = undefined
  if (nodeIsLeaf(element)) {
    let flag_high_level_paged = false
    if (current_page.length === 0 && pointer_div[0] === undefined) {
      // 第一次调用时获取新的操作指针
      const neo_pointer = (div_template as HTMLElement).cloneNode(true)
      tester_container.appendChild(neo_pointer)
      pointer_div[0] = <HTMLElement>neo_pointer
    }

    ;(pointer_div[0] as HTMLElement).appendChild(element.cloneNode(true))

    const image_load_status = waitForResourceSync(element, 10) // 检测资源加载状态
    let now_height = tester_container.scrollHeight

    if (image_load_status !== 'success') {
      console.warn('资源加载异常')
      now_height = maxHeight.value // 强行结束当前页
    }

    if (now_height <= maxHeight.value * paging_threshold) {
      // 当前元素可以加入当前页
      // 什么都不做
      if (savedPart2Container.part2 !== undefined) {
        // 标记Part2处理完成
        savedPart2Container.part2 = undefined
      }
    } else {
      // 当前元素无法加入当前页
      ;(pointer_div[0] as HTMLElement).removeChild(
        (pointer_div[0] as HTMLElement).lastChild as HTMLElement,
      )
      let result = undefined // 性能优化 避免重复调用高级分页算法
      if (flag_high_level_paged === false) result = getParagraphs_Simple(element, pointer_div[0])
      if (result !== undefined) {
        // 高级分页成功
        flag_high_level_paged = true
        const [part1, part2] = result

        // 先处理 part1，保存 part2
        ;(pointer_div[0] as HTMLElement).appendChild(part1)

        current_page.push((pointer_div[0] as HTMLElement).cloneNode(true) as HTMLElement)
        pages_list.push(cloneHTMLElementList(current_page)) // 保存当前页

        // 获取新的操作指针
        current_page.length = 0
        tester_container.innerHTML = ''
        flag_high_level_paged = false
        // 获取新的操作指针
        const neo_pointer = (div_template as HTMLElement).cloneNode(true)
        tester_container.appendChild(neo_pointer)
        pointer_div[0] = <HTMLElement>neo_pointer
        // 将 part2 保存到 container 中，便于后续处理
        savedPart2Container.part2 = part2.cloneNode(true) as HTMLElement
      } else {
        // 结束一页 高级分页失败了也会回退到这里
        savedPart2Container.part2 = undefined

        // let flag_img = false
        // if ((pointer_div[0] as HTMLElement).classList === undefined) {
        //   // 高级分页引擎也无法处理的东西 比如说图片
        //   current_page.push((pointer_div[0] as HTMLElement).cloneNode(true) as HTMLElement)
        //   flag_img = true
        // }
        // if (tester_container.scrollHeight !== 0 || flag_img === true) {
        //   pages_list.push(cloneHTMLElementList(current_page))
        // } else {
        //   console.log('存在空页 已剔除')
        // }

        current_page.push((pointer_div[0] as HTMLElement).cloneNode(true) as HTMLElement)
        pages_list.push(cloneHTMLElementList(current_page)) // 保存当前页

        // 获取新的操作指针
        current_page.length = 0
        tester_container.innerHTML = ''
        flag_high_level_paged = false
        // 获取新的操作指针
        const neo_pointer = (div_template as HTMLElement).cloneNode(true)
        tester_container.appendChild(neo_pointer)
        pointer_div[0] = <HTMLElement>neo_pointer
        // neo_pointer.appendChild(element)
        savedPart2Container.part2 = <HTMLElement>element.cloneNode(true)
      }
    }
  } else {
    console.log(element)
    if (div_template === undefined) {
      //? 此元素是根元素 初始化div模板
      next_div_template = cloneElementStyleAndClass(element)
    } else {
      // 不是根节点
      const last_template = div_template.cloneNode(true)
      next_div_template = last_template.appendChild(cloneElementStyleAndClass(element))
    }
    Array.from(element.childNodes).forEach((node) => {
      if (node instanceof HTMLElement) {
        // 继续遍历子元素
        pagedEnginePointerHighLevelCore(
          node,
          tester_container,
          pages_list,
          current_page,
          maxHeight,
          paging_threshold,
          savedPart2Container, // 传递 container 包装的 savedPart2
          next_div_template,
          pointer_div,
        )
      }
    })
  }
}

const renderPage = (pageIndex: number) => {
  const contentContainer = <HTMLElement>readerContainer.value
  contentContainer.innerHTML = ''
  if (pages.value === undefined) return
  const subPage = pages.value[pageIndex]
  if (subPage === undefined) return
  subPage.forEach((element) => {
    contentContainer.appendChild(element.cloneNode(true))
  })
  if (flag_single_page_mode.value !== true) {
    readProgress.value = pageIndex / (totalPages.value - 1)
  }
  contentContainer.style.visibility = 'visible'
}

const prevPage = () => {
  if (currentPage.value > 0) {
    currentPage.value--
    renderPage(currentPage.value)
  } else if (currentPage.value === 0 && flag_auto_next.value) {
    console.log('自动切换到上一章节')
    flag_auto_prev.value = true
    prevChapter()
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value - 1) {
    // 继续翻页，渲染当前页
    currentPage.value++
    renderPage(currentPage.value)
  } else if (currentPage.value === totalPages.value - 1) {
    // 自动切换章节（仅在自动切换标志为 true 时）
    if (flag_auto_next.value) {
      console.log('自动切换到下一章节')
      nextChapter()
    }
  }
}

const switchPagedMode = () => {
  flag_high_level_paged_engine.value = !flag_high_level_paged_engine.value
}

const switchPagedEngine = () => {
  flag_use_pointer_engine.value = !flag_use_pointer_engine.value
}

const switchViewMode = () => {
  flag_single_page_mode.value = !flag_single_page_mode.value
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

watch(
  [
    fontSize,
    headingFontSize,
    maxHeight,
    readerWidth,
    flag_high_level_paged_engine,
    flag_single_page_mode,
    flag_use_pointer_engine,
  ],
  () => {
    showPage() // 页面更新
  },
)
// 使用 ResizeObserver 监控元素的尺寸变化
const updateWidth = () => {
  if (patchouliReader.value) {
    readerWidth.value = patchouliReader.value.offsetWidth
    if (last_reader_width.value !== readerWidth.value) {
      console.log('阅读器宽度改变')
    }
    console.log('Element Width:', readerWidth.value)
  }
}
const cloneHTMLElementList = (elements: HTMLElement[]): HTMLElement[] =>
  elements.map((el) => el.cloneNode(true) as HTMLElement)

const showPage = (pageIndex?: number) => {
  console.log('启动预渲染')
  if (hiddenContainer.value === undefined) return
  if (readerContainer.value === undefined) return
  if (cacheContainer.value === undefined) return
  if (rawDOMtree.value === undefined) return
  readerContainer.value.style.visibility = 'hidden'
  adjustFontSize()
  console.log('字体大小注入完成')
  hiddenContainer.value.style.width = `${readerWidth.value}px`
  readerContainer.value.style.width = `${readerWidth.value}px`
  cacheContainer.value.style.width = `${readerWidth.value}px`
  console.log(maxHeight.value, 'px')
  if (flag_single_page_mode.value) {
    pageIndex = 0
    readerContainer.value.style.height = 'auto'
  } else {
    readerContainer.value.style.height = `${maxHeight.value}px`
  }
  if (flag_use_pointer_engine.value) {
    const temp = rawDOMtree.value.cloneNode(true)
    console.log('准备进行分页处理')
    pages.value = getPages([<HTMLElement>temp])
  } else {
    // pages.value = getPages(rawElements.value as HTMLElement[])
    const temp = cloneHTMLElementList(rawElements.value as HTMLElement[])
    console.log('准备进行分页处理')
    pages.value = getPages(temp)
  }

  console.log(`本章节有${totalPages.value}页`)
  // 处理负索引支持
  if (pageIndex !== undefined) {
    if (pageIndex < 0) {
      pageIndex = totalPages.value + pageIndex // 负索引转换
    }
    if (pageIndex < 0 || pageIndex >= totalPages.value) {
      console.error(`页索引 ${pageIndex} 超出范围`)
      return
    }
  }
  if (totalPages.value <= 0) {
    // 检查 readerContainer 是否有效
    if (!readerContainer.value) {
      console.error('容器未初始化')
      return
    }
    console.warn('章节为空')
    // 清空容器内容
    readerContainer.value.innerHTML = ''

    // 创建新的 div 元素
    const noContentDiv = document.createElement('div')
    noContentDiv.textContent = '章节无内容' // 设置文本
    noContentDiv.style.display = 'flex' // 使用 Flex 布局
    noContentDiv.style.justifyContent = 'center' // 水平居中
    noContentDiv.style.alignItems = 'center' // 垂直居中
    noContentDiv.style.height = '100%' // 高度占满容器
    // noContentDiv.style.fontSize = '50px !important' // 设置字体大小 不生效
    noContentDiv.style.color = '#666' // 设置字体颜色
    noContentDiv.style.fontFamily = 'sans-serif'

    // 将新元素添加到容器
    readerContainer.value.appendChild(noContentDiv)
    return
  }

  console.log('分页任务完成')
  if (pageIndex === undefined && flag_single_page_mode.value != true) {
    if (totalPages.value > 1) {
      // 根据 readProgress 计算出 pageIndex
      const calculatedPageIndex = Math.round(readProgress.value * (totalPages.value - 1))
      // 确保 pageIndex 不小于 0，且不大于 totalPages.value - 1
      pageIndex = Math.max(0, Math.min(calculatedPageIndex, totalPages.value - 1))
    } else {
      // 如果总页数小于等于1，则始终在第0页
      pageIndex = 0
    }
  }
  if (pageIndex === undefined) {
    pageIndex = 0
    console.log('在计算页码的时候未覆盖了')
    //TODO 这种情况真的存在吗
  }
  currentPage.value = pageIndex
  // console.log(currentPage.value)
  readerContainer.value.style.visibility = 'visible'
  renderPage(currentPage.value)
}

// 深拷贝函数
const deepClone = <T,>(obj: T): T => {
  // 处理 DOM 元素
  if (obj instanceof Node) {
    return obj.cloneNode(true) as T // 克隆元素及其所有子节点
  }

  // 处理对象
  if (obj && typeof obj === 'object') {
    // 处理数组
    if (Array.isArray(obj)) {
      return obj.map((item) => deepClone(item)) as unknown as T // 对数组中的每个元素进行深拷贝
    }

    // 处理普通对象
    const copy: Record<string, unknown> = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        copy[key] = deepClone(obj[key]) // 对对象的每个属性进行深拷贝
      }
    }
    return copy as T
  }

  // 其他基本类型直接返回
  return obj
}

/**
 * 等待 CSS 应用完成
 * 通过注入并检测CSS元素是否对测试DIV生效的方法来同步css和js引擎
 * @param shadowRoot
 * @param cssRules
 * @param originalSize
 * @param timeout
 * @param interval
 */
const waitForCSSApplication = (
  shadowRoot: ShadowRoot,
  cssRules: string,
  originalSize = '16px',
  timeout = 3000,
  interval = 50,
): Promise<boolean> => {
  return new Promise((resolve, reject) => {
    // 获取当前计数并分配唯一 ID
    const currentCounter = globalTestDivCounter.value++
    const uniqueId = `__test_div_${currentCounter}__`

    // 检查是否已存在同名元素，避免冲突
    if (shadowRoot.querySelector(`#${uniqueId}`)) {
      reject(new Error(`Element with ID '${uniqueId}' already exists in ShadowRoot.`))
      globalTestDivCounter.value-- // 回收计数
      return
    }

    // 创建测试容器
    const testDiv = document.createElement('div')
    testDiv.id = uniqueId
    testDiv.style.fontSize = originalSize
    testDiv.style.position = 'absolute'
    testDiv.innerText = '__TEST_DIV__'
    testDiv.style.visibility = 'hidden'
    shadowRoot.appendChild(testDiv)

    // 注入 CSS 样式
    const styleElement = document.createElement('style')
    styleElement.textContent = cssRules.replace(/#test-div/g, `#${uniqueId}`)
    shadowRoot.appendChild(styleElement)

    // 开始轮询检测
    const startTime = Date.now()
    const checkFontSize = () => {
      const appliedSize = getComputedStyle(testDiv).fontSize

      if (appliedSize !== originalSize) {
        // 样式已生效
        shadowRoot.removeChild(testDiv)
        shadowRoot.removeChild(styleElement)
        globalTestDivCounter.value-- // 回收计数
        resolve(true)
      } else if (Date.now() - startTime > timeout) {
        // 超时
        shadowRoot.removeChild(testDiv)
        shadowRoot.removeChild(styleElement)
        globalTestDivCounter.value-- // 回收计数
        reject(new Error('CSS application timeout'))
      } else {
        // 继续检测
        setTimeout(checkFontSize, interval)
      }
    }

    checkFontSize()
  })
}

/**
 * 初始化并等待CSS与JS同步
 * @param shadowRoot
 */
const initAndTestCSSApplication = async (shadowRoot: ShadowRoot): Promise<void> => {
  try {
    const cssRules = `
      #test-div {
          font-size: 50px !important;
      }
    `
    //! 通过注入并检测CSS元素是否对测试DIV生效的方法来同步css和js引擎
    await waitForCSSApplication(shadowRoot, cssRules)
    console.log('CSS 已成功应用！')
  } catch (error) {
    console.error('CSS 应用失败：', error)
  }
}

const initReader = async () => {
  if (patchouliContent.value === undefined) return

  // 创建 Shadow DOM
  shadowRoot.value = patchouliContent.value.attachShadow({ mode: 'open' })
  // 注入 CSS 样式，限制图片高度
  const style = document.createElement('style')
  style.id = 'base-css'
  style.textContent = `
    img {
      max-height: 100%; /* 图片最大高度不超过容器 */
      max-width: 100%; /* 图片宽度自适应容器 */
      object-fit: contain; /* 等比缩放 */
      margin: 0 auto;
      display: block;
    }
    illus {
      max-height: 100%; /* 图片最大高度不超过容器 */
      max-width: 100%; /* 图片宽度自适应容器 */
      object-fit: contain; /* 等比缩放 */
    }
    duokan-image-single {
      max-height: 100%; /* 图片最大高度不超过容器 */
      max-width: 100%; /* 图片宽度自适应容器 */
      object-fit: contain; /* 等比缩放 */
    }
  `
  shadowRoot.value.appendChild(style)

  // 创建隐藏容器
  hiddenContainer.value = document.createElement('div')
  hiddenContainer.value.style.position = 'absolute'
  hiddenContainer.value.id = 'taster-container'
  hiddenContainer.value.style.height = 'auto'
  hiddenContainer.value.style.width = `${readerWidth.value}px`
  // hiddenContainer.value.style.width = '100vw'
  shadowRoot.value.appendChild(hiddenContainer.value)

  // 创建内容容器
  readerContainer.value = document.createElement('div')
  readerContainer.value.id = 'content-container'
  readerContainer.value.style.width = `${readerWidth.value}px`
  // readerContainer.value.style.display = 'none'
  // readerContainer.value.style.width = '100vw'
  shadowRoot.value.appendChild(readerContainer.value)

  // 创建缓存容器
  cacheContainer.value = document.createElement('div')
  cacheContainer.value.id = 'cache-container'
  cacheContainer.value.style.width = `${readerWidth.value}px`
  cacheContainer.value.style.display = 'none'
  cacheContainer.value.style.float = 'inherit'
  shadowRoot.value.appendChild(cacheContainer.value)

  // await waitForStyle(shadowRoot.value) //
  await initAndTestCSSApplication(shadowRoot.value)
  //! 通过注入并检测CSS元素是否对测试DIV生效的方法来同步css和js引擎
  // await sleep(500)
  return Promise.resolve()
}

function ensureCompleteHTML(htmlText: string) {
  // 确保输入是字符串
  if (typeof htmlText !== 'string') {
    throw new Error('Input must be a string')
  }

  const hasHtmlTag = /<html[\s\S]*?>/i.test(htmlText)
  const hasHeadTag = /<head[\s\S]*?>/i.test(htmlText)
  const hasBodyTag = /<body[\s\S]*?>/i.test(htmlText)

  // 如果没有 <html> 标签
  if (!hasHtmlTag) {
    // 检查是否包含其他 HTML 标签
    const containsHTMLTags = /<\w+[\s\S]*?>/i.test(htmlText)

    if (containsHTMLTags) {
      // 如果包含其他 HTML 标签，则包裹在 <html> 和 <body> 中
      htmlText = `<!DOCTYPE html><html><head></head><body>${htmlText}</body></html>`
    } else {
      // 如果没有任何标签，直接补全空的 HTML 结构
      htmlText = `<!DOCTYPE html><html><head></head><body>${htmlText}</body></html>`
    }
  } else {
    // 如果有 <html>，但没有 <head>
    if (!hasHeadTag) {
      if (hasBodyTag) {
        // 有 <body> 的情况，在 <body> 前补充 <head>
        htmlText = htmlText.replace(/<body[\s\S]*?>/i, (match) => `<head></head>${match}`)
      } else {
        // 没有 <body> 的情况，在 <html> 后插入 <head> 和 <body>
        htmlText = htmlText.replace(/<html[\s\S]*?>/i, (match) => `${match}<head></head><body>`)
        htmlText += '</body>'
      }
    }

    // 如果没有 <body>，在 </head> 后插入 <body>
    if (!hasBodyTag) {
      htmlText = htmlText.replace(/<\/head>/i, (match) => `${match}<body>`)
      htmlText += '</body>' // 补充 <body> 尾
    }
  }

  // 确保 </html> 在文档的最后
  if (!/<\/html>$/i.test(htmlText)) {
    htmlText += '</html>'
  }

  return htmlText
}

const parseHTML = (text: string) => {
  // 这个东西在目前环境下不太靠谱
  const parser = new DOMParser()
  const doc = parser.parseFromString(text, 'text/html')

  // 检查是否存在解析错误
  if (!doc.querySelector('parsererror')) {
    return doc // 成功解析，返回整个 DOM 树
  }

  // 如果解析失败，使用 innerHTML 方法作为回退
  console.warn('DOMParser failed, falling back to innerHTML.')
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = text

  // 包装成一个类似 DOM 树的文档结构
  const fallbackDoc = document.implementation.createHTMLDocument('')
  // fallbackDoc.body.append(...tempDiv.childNodes); // 将子节点复制到文档中
  fallbackDoc.body.append(...Array.from(tempDiv.childNodes))

  return fallbackDoc // 返回整个回退的 DOM 树
}

const fetchStylesheetSync = (url: string, seen: Set<string> = new Set()): string => {
  if (seen.has(url)) {
    console.warn(`Skipping duplicate stylesheet: ${url}`)
    return ''
  }
  seen.add(url)

  let cssText = ''
  try {
    const xhr = new XMLHttpRequest()
    xhr.open('GET', url, false) // Synchronous request
    xhr.send()

    if (xhr.status >= 200 && xhr.status < 300) {
      cssText = xhr.responseText

      // Resolve nested @import rules
      const importRegex = /@import\s+['"]([^'"]+)['"];/g
      let match: RegExpExecArray | null

      while ((match = importRegex.exec(cssText)) !== null) {
        const importUrl = new URL(match[1], url).href // Resolve relative URLs
        const nestedCSS = fetchStylesheetSync(importUrl, seen)
        cssText = cssText.replace(match[0], nestedCSS) // Replace @import with actual content
      }
    } else {
      console.error(`Failed to fetch stylesheet: ${url}, status: ${xhr.status}`)
    }
  } catch (error) {
    console.error(`Error fetching stylesheet: ${url}`, error)
  }

  return cssText
}

const injectStyles = (doc: Document, shadowRoot: ShadowRoot) => {
  const linkTags = doc.querySelectorAll('link[rel="stylesheet"]')

  // Process each external stylesheet
  for (const link of Array.from(linkTags)) {
    const htmlLink = link as HTMLLinkElement
    if (!shadowRoot.querySelector(`style[data-href="${htmlLink.href}"]`)) {
      const cssText = fetchStylesheetSync(htmlLink.href)
      if (cssText) {
        const styleElement = document.createElement('style')
        styleElement.textContent = cssText
        styleElement.setAttribute('data-href', htmlLink.href)
        shadowRoot.appendChild(styleElement)
      }
    }
  }

  // Process inline <style> tags
  const styleTags = doc.querySelectorAll('style')
  styleTags.forEach((style) => {
    const styleElement = document.createElement('style')
    styleElement.textContent = style.textContent || ''
    shadowRoot.appendChild(styleElement)
  })
}

function waitForImagesToLoad(
  tree: HTMLElement,
  timeoutPerImage = 3000,
  showMessageTime = 3000,
): Promise<void> {
  const imageElements = tree.querySelectorAll('img')
  const imageCount = imageElements.length

  // 计算总超时时间
  const totalTimeout = imageCount * timeoutPerImage

  console.log(`发现 ${imageCount} 张图片，超时时间总计：${totalTimeout} ms`)
  if (totalTimeout >= showMessageTime) {
    const noContentDiv = document.createElement('div')
    noContentDiv.textContent = `正在加载图片\n预计最长加载时间 ${totalTimeout / 1000}S`
    noContentDiv.style.whiteSpace = 'pre-wrap'
    noContentDiv.style.display = 'flex' // 使用 Flex 布局
    noContentDiv.style.flexDirection = 'column' // 垂直排列
    noContentDiv.style.justifyContent = 'center' // 垂直居中
    noContentDiv.style.alignItems = 'center' // 水平居中
    noContentDiv.style.textAlign = 'center' // 文本居中对齐
    noContentDiv.style.height = '100%' // 高度占满容器
    // noContentDiv.style.fontSize = '50px !important' // 设置字体大小 不生效
    noContentDiv.style.color = '#666' // 设置字体颜色
    noContentDiv.style.fontFamily = 'sans-serif'

    // 将新元素添加到容器
    ;(<HTMLElement>readerContainer.value).appendChild(noContentDiv)
  }

  // 创建每张图片的加载或失败 Promise
  const loadPromises = Array.from(imageElements).map((image) => {
    return new Promise<void>((resolve) => {
      if (image.complete) {
        console.log(`图片预加载成功：${image.src}`)
        resolve()
      } else {
        image.onload = () => resolve()
        image.onerror = () => resolve() // 图片加载失败时也继续
      }
    })
  })

  // 等待所有图片加载完成或总超时时间到达
  return Promise.race([
    Promise.all(loadPromises).then(() => undefined),
    new Promise<void>((resolve) => setTimeout(resolve, totalTimeout)),
  ])
}

const loadContent = async (url: string): Promise<void> => {
  try {
    // 获取 HTML 内容
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch content: ${response.status} ${response.statusText}`)
    }
    const text = await response.text()
    // const text = ensureCompleteHTML(props.html)

    // console.log(text)

    // 解析 HTML
    // const parser = new DOMParser()
    // const doc = parser.parseFromString(text, 'text/html')
    // const tempDiv = document.createElement('div');
    // tempDiv.innerHTML = text;
    // const targetDiv = tempDiv.querySelector('div');
    // console.log(targetDiv);
    const doc = parseHTML(text)
    // console.log(doc)

    const images = doc.querySelectorAll('img') // 获取所有 img 元素
    // 创建一个新的容器用于存放处理后的图片
    const newTree = document.createElement('div')
    images.forEach((img) => {
      // 创建一个新的图片元素
      const newImg = document.createElement('img')

      // 设置图片的 src 和大小
      newImg.src = img.src
      newImg.style.width = '150px'
      newImg.style.height = '150px'

      // 添加到新树
      newTree.appendChild(newImg)
    })

    //逆天缓存
    if (cacheContainer.value !== undefined) {
      cacheContainer.value.appendChild(newTree)
    }
    console.log('等待图片预加载')
    await waitForImagesToLoad(newTree, 500)
    console.log('图片预加载任务完成')

    // 更新页面标题
    const title = doc.querySelector('title')?.innerText
    if (title) {
      document.title = title
    }

    // 添加 <link> 样式表
    // const linkTags = doc.querySelectorAll('link[rel="stylesheet"]')
    // linkTags.forEach((link) => {
    //   const htmlLink = link as HTMLLinkElement
    //   if (!shadowRoot.value?.querySelector(`link[href="${htmlLink.href}"]`)) {
    //     const newLink = document.createElement('link')
    //     newLink.rel = 'stylesheet'
    //     newLink.href = htmlLink.href
    //     shadowRoot.value?.appendChild(newLink)
    //   }
    // })
    if (shadowRoot.value) {
      injectStyles(doc, shadowRoot.value)
    }

    // 添加内联样式 <style>
    const styleTags = doc.querySelectorAll('style')
    styleTags.forEach((style) => {
      const styleElement = document.createElement('style')
      styleElement.textContent = style.textContent // 优化为 textContent
      shadowRoot.value?.appendChild(styleElement)
    })

    // 确保阅读容器已初始化
    if (!readerContainer.value) {
      throw new Error('readerContainer 未初始化')
    }

    // 创建一个空白的 div 容器
    const tempContainer = document.createElement('div')

    // 设置内容到空白 div
    const bodyContent = doc.querySelector('body')?.innerHTML || ''
    tempContainer.innerHTML = bodyContent

    // 克隆空白 div 并展平为元素列表
    rawDOMtree.value = tempContainer.cloneNode(true) as HTMLElement
    rawElements.value = flattenDOM(rawDOMtree.value, flag_flatten_DOM.value)
    // console.log(rawElements.value)
    console.log('html加载成功')
    await initAndTestCSSApplication(<ShadowRoot>shadowRoot.value)
    //! 通过注入并检测CSS元素是否对测试DIV生效的方法来同步css和js引擎
    return Promise.resolve()
  } catch (error) {
    console.error('加载内容失败:', error)
    console.error(error)
    return Promise.resolve()
  }
}

// 生命周期钩子
onMounted(async () => {
  await initReader() //! 初始化未受 Vue 托管的 DOM 树
  // await sleep(1500)
  nextTick(() => {
    // 设置尺寸并绑定事件
    if (patchouliReader.value) {
      readerWidth.value = patchouliReader.value.offsetWidth
      last_reader_width.value = readerWidth.value
      maxHeight.value = patchouliReader.value.offsetHeight
    }
    window.addEventListener('resize', handleResize)
    window.addEventListener('wheel', handleWheel)
    resizeObserver.value = new ResizeObserver(updateWidth)
    if (patchouliReader.value) {
      resizeObserver.value.observe(patchouliReader.value)
    }
  })
  // await loadContent('content.html') //! 加载内容
  await loadContent('sample2/text.xhtml') //! 加载内容
  // flag_single_page_mode.value = true
  // showPage(0) //显示首页
  // flag_single_page_mode.value = false
  // // showPage(0) //显示首页
  // await sleep(3000)
  if (flag_auto_prev.value) {
    showPage(-1)
    flag_auto_prev.value = false
  } else {
    showPage(0)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('wheel', handleWheel)
  if (resizeObserver.value !== undefined) resizeObserver.value.disconnect()
})

onDeactivated(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('wheel', handleWheel)
  if (resizeObserver.value !== undefined) resizeObserver.value.disconnect()
})

defineExpose({ patchouliContent })
</script>

<style scoped>
/* 页面的样式 */
#patchouli-reader {
  display: flex; /* 使用 flexbox 布局 */
  flex-direction: column; /* 垂直排列子元素 */
  height: 100%; /* 让 #reader-app 占满父容器的高度 */
  width: 90%; /* 让 #reader-app 占满父容器的宽度 */

  /* justify-content: center; 垂直居中 */
  align-items: center; /* 水平居中 */
}
#patchouli-content {
  display: flex; /* 使用 flexbox 布局 */
  flex-direction: column; /* 垂直排列子元素 */
  height: 100%; /* 让 #reader-app 占满父容器的高度 */
  width: 100%; /* 让 #reader-app 占满父容器的宽度 */

  /* justify-content: center; 垂直居中 */
  align-items: center; /* 水平居中 */
}
</style>
