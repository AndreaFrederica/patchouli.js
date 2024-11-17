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
        :progress="progress"
        v-model:fontSize="fontSize"
        v-model:headingFontSize="headingFontSize"
        @prev-page="prevPage"
        @next-page="nextPage"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onBeforeUnmount, ref, computed, nextTick, watch, provide } from 'vue';
import FloatingControls from '@/components/FloatingControls.vue';

const rawElements = ref<HTMLElement[]>(); // 原始html内容
const pages = ref<HTMLElement[][]>([]); // 页面的元素数组，每页元素为 HTMLElement 数组
const currentPage = ref(0);
const maxHeight = ref(600); // 单页最大高度
const readerWidth = ref(0);
const fontSize = ref(16); // 正文字体大小（默认16px）
const headingFontSize = ref(24); // 各级标题的字体大小（默认24px）
const shadowRoot = ref<ShadowRoot>(); // Shadow DOM 根元素
const hiddenContainer = ref<HTMLElement>();
const readProgress = ref(0); // 阅读进度
const patchouliContent = ref<HTMLElement>();
const readerContainer = ref<HTMLElement>();
const patchouliReader = ref<HTMLElement>();

const touchStartX = ref(0);
const touchEndX = ref(0);
const touchStartTime = ref<number | null>(null); // 记录触摸开始时间
const LONG_PRESS_THRESHOLD = ref(500); // 长按阈值（毫秒）

const totalPages = computed(() => pages.value.length);
const progress = computed(() => ((currentPage.value + 1) / totalPages.value) * 100);

// 高阶分页支持
const flag_high_level_paged_engine = ref(false);
//TODO 无法使用 因为其依赖的深拷贝有点问题？ 但是好像又不是这个问题
// 启用激进分页模式
const flag_aggressive_paging_engine = ref(false);
// 激进分页模式的阈值 小于这个就进行激进分页
const aggressive_paging_threshold = 0.9; // 默认值为 0.9

const onReaderClick = ref(false);
provide(/* 注入名 */ 'PatchouliReader_onReaderClick', /* 值 */ onReaderClick);

const handleResize = () => {
  if (patchouliReader.value) {
    readerWidth.value = patchouliReader.value.offsetWidth;
    maxHeight.value = patchouliReader.value.offsetHeight;
  }
};

// 点击翻页处理函数
const handleClick = (event: MouseEvent) => {
  const clickX = event.clientX;
  const screenWidth = window.innerWidth;
  const edgeWidth = screenWidth * 0.2; // 边缘区域为 20%

  if (clickX < edgeWidth) {
    prevPage(); // 点击左侧20%区域
  } else if (clickX > screenWidth - edgeWidth) {
    nextPage(); // 点击右侧20%区域
  } else {
    onReaderClick.value = true; // 非边缘区域点击
  }
};

// 触摸滑动开始处理函数
const handleTouchStart = (event: TouchEvent) => {
  touchStartX.value = event.touches[0].clientX;
  touchStartTime.value = Date.now(); // 记录触摸开始时间
};

// 触摸滑动结束处理函数
const handleTouchEnd = (event: TouchEvent) => {
  touchEndX.value = event.changedTouches[0].clientX;
  const touchEndTime = Date.now(); // 记录触摸结束时间

  const duration = touchEndTime - (touchStartTime.value ?? touchEndTime);

  if (duration >= LONG_PRESS_THRESHOLD.value) {
    handleLongPress(); // 长按事件
  } else {
    handleSwipe(); // 滑动或点击事件
  }

  // 清理状态
  touchStartX.value = 0;
  touchEndX.value = 0;
  touchStartTime.value = 0;
};

// 滑动处理函数
const handleSwipe = () => {
  if (touchStartX.value === 0 || touchEndX.value === 0) return;

  const swipeDistance = touchEndX.value - touchStartX.value;
  const swipeThreshold = 100; // 设置滑动的阈值

  if (swipeDistance > swipeThreshold) {
    prevPage(); // 右滑（向右滑动）
  } else if (swipeDistance < -swipeThreshold) {
    nextPage(); // 左滑（向左滑动）
  }
};

// 长按处理函数
const handleLongPress = () => {
  console.log('长按事件触发');
  // 在此处理长按事件逻辑
};

const flattenDOM = (node: Node): HTMLElement[] => {
  let elements: HTMLElement[] = [];
  node.childNodes.forEach((child) => {
    if (child.nodeType === Node.ELEMENT_NODE) {
      elements.push(child as HTMLElement);
      elements = elements.concat(flattenDOM(child));
    }
  });
  return elements;
};
const cloneElementStyleAndClass = (element: HTMLElement): HTMLElement => {
  // 创建一个新的元素（与原始元素相同的标签类型）
  const cloned = document.createElement(element.tagName) as HTMLElement;

  // 复制原始元素的所有类
  cloned.className = element.className;

  // 复制原始元素的内联样式
  cloned.style.cssText = element.style.cssText;

  // 移除 id 属性，避免重复
  cloned.removeAttribute('id');

  return cloned;
};
// 示例
// const original = document.querySelector("p") as HTMLParagraphElement;
// original && document.body.appendChild(cloneElementWithStyleAndClass(original)!);

// 最简单的高阶切分算法 没考虑div套娃 需要更多高级切分算法做补充
const getParagraphs_Simple = (element: HTMLElement): HTMLElement[] | undefined => {
  const part1 = cloneElementStyleAndClass(element);
  const part2 = cloneElementStyleAndClass(element);

  // 获取原始文本内容
  const text = element.innerText;

  // 清除页面容器中的最后一个重复元素
  const container = hiddenContainer.value as HTMLElement;
  container.removeChild(container.lastChild);

  // 将 part1 添加到隐藏容器中
  container.appendChild(part1);

  // 设置 part1 的内容，并进行分页检测
  let part1Text = '';
  for (const char of text) {
    part1Text += char; // 向 part1 添加字符
    part1.innerText = part1Text; // 设置 part1 的文本内容

    // 检查是否超过分页阈值
    if (container.scrollHeight / maxHeight.value >= aggressive_paging_threshold) {
      // 超过阈值，分页结束
      break;
    }
  }

  if (part1Text.length <= 5) return;

  // 将剩余的文本交给 part2
  const remainingText = text.slice(part1Text.length);
  part2.innerText = remainingText;

  // 注入最高级别的CSS，确保缩进取消
  part2.style.padding = '0';
  part2.style.margin = '0';
  part2.style.textIndent = '0'; // 确保取消缩进
  part2.style.whiteSpace = 'normal'; // 确保文本按照正常格式显示

  return [part1, part2]; // 返回两个分页部分
};

const getPages = (elements?: HTMLElement[]): HTMLElement[][] => {
  const pages: HTMLElement[][] = [];
  let currentPage: HTMLElement[] = [];
  if (elements === undefined) return pages;
  if (flag_high_level_paged_engine.value) {
    let lastElementHeight = 0;

    // 使用普通的 for 循环遍历元素数组
    for (let i = 0; i < elements.length; i++) {
      const element = elements[i];

      // 克隆元素并将其添加到隐藏容器中
      (hiddenContainer.value as HTMLElement).appendChild(element.cloneNode(true));
      const elementHeight = (hiddenContainer.value as HTMLElement).scrollHeight;

      if (elementHeight > maxHeight.value) {
        if (flag_high_level_paged_engine.value) {
          // 启用高阶分页
          if (flag_aggressive_paging_engine.value) {
            // 启用激进分页模式
            if (lastElementHeight / maxHeight.value < aggressive_paging_threshold) {
              // 对激进分页模式进行处理
              const result = getParagraphs_Simple(element);
              if (result) {
                const [part1, part2] = result;
                currentPage.push(part1);
                elements.splice(i + 1, 0, part2); // 插入 part2 继续处理
                pages.push(currentPage);
                (hiddenContainer.value as HTMLElement).innerHTML = '';
                (hiddenContainer.value as HTMLElement).appendChild(part2.cloneNode(true));
                currentPage = [];
                lastElementHeight = elementHeight;
              } else {
                // 如果 getParagraphs_Simple 返回 undefined，回退到普通处理
                pages.push(currentPage);
                (hiddenContainer.value as HTMLElement).innerHTML = '';
                (hiddenContainer.value as HTMLElement).appendChild(element.cloneNode(true));
                currentPage = [];
                lastElementHeight = elementHeight;
              }
            } else {
              // 降级 按默认逻辑分页
              pages.push(currentPage);
              (hiddenContainer.value as HTMLElement).innerHTML = '';
              (hiddenContainer.value as HTMLElement).appendChild(element.cloneNode(true));
              currentPage = [];
              lastElementHeight = elementHeight;
            }
          } else {
            // 只对单段落超长页面处理
            if (currentPage.length == 1) {
              const result = getParagraphs_Simple(element);
              if (result) {
                const [part1, part2] = result;
                currentPage.push(part1);
                elements.splice(i + 1, 0, part2); // 插入 part2 继续处理
                pages.push(currentPage);
                (hiddenContainer.value as HTMLElement).innerHTML = '';
                (hiddenContainer.value as HTMLElement).appendChild(part2.cloneNode(true));
                currentPage = [];
                lastElementHeight = 0;
              } else {
                // 如果 getParagraphs_Simple 返回 undefined，回退到普通处理
                pages.push(currentPage);
                (hiddenContainer.value as HTMLElement).innerHTML = '';
                (hiddenContainer.value as HTMLElement).appendChild(element.cloneNode(true));
                currentPage = [];
                lastElementHeight = 0;
              }
            } else {
              //不是对应情况，按默认逻辑分页
              pages.push(currentPage);
              (hiddenContainer.value as HTMLElement).innerHTML = '';
              (hiddenContainer.value as HTMLElement).appendChild(element.cloneNode(true));
              currentPage = [];
              lastElementHeight = 0;
            }
          }
        } else {
          // 没有启用高阶分页，按默认逻辑分页
          pages.push(currentPage);
          (hiddenContainer.value as HTMLElement).innerHTML = '';
          (hiddenContainer.value as HTMLElement).appendChild(element.cloneNode(true));
          currentPage = [];
          lastElementHeight = 0;
        }
      } else {
        // 没有发生分页
        currentPage.push(element);
        lastElementHeight = elementHeight;
      }
    }

    // 处理最后一页
    if (currentPage.length > 0) {
      // 普通分页
      pages.push(currentPage);
    }
    (hiddenContainer.value as HTMLElement).innerHTML = '';
    return pages;
  } else {
    // 最原始的老版本函数
    elements.forEach((element) => {
      (hiddenContainer.value as HTMLElement).appendChild(element.cloneNode(true)); // 类型断言为 HTMLElement
      const elementHeight = (hiddenContainer.value as HTMLElement).scrollHeight;
      if (elementHeight > maxHeight.value) {
        pages.push(currentPage);
        (hiddenContainer.value as HTMLElement).innerHTML = '';
        (hiddenContainer.value as HTMLElement).appendChild(element.cloneNode(true));
        currentPage = [element];
      } else {
        currentPage.push(element);
      }
    });
    if (currentPage.length > 0) {
      // 最后一页
      pages.push(currentPage);
      (hiddenContainer.value as HTMLElement).innerHTML = '';
    }
    return pages;
  }
};

const renderPage = (pageIndex: number) => {
  const contentContainer = shadowRoot.value?.querySelector('#content-container') as HTMLElement;
  contentContainer.innerHTML = '';
  if (pages.value === undefined) return;
  const subPage = pages.value[pageIndex];
  if (subPage === undefined) return;
  subPage.forEach((element) => {
    contentContainer.appendChild(element.cloneNode(true));
  });
  readProgress.value = pageIndex / (totalPages.value - 1);
  contentContainer.style.visibility = 'visible';
};

const prevPage = () => {
  if (currentPage.value > 0) {
    currentPage.value--;
    renderPage(currentPage.value);
  }
};

const nextPage = () => {
  if (currentPage.value < totalPages.value - 1) {
    currentPage.value++;
    renderPage(currentPage.value);
  }
};

const adjustFontSize = () => {
  if (!shadowRoot.value) return;

  // 查找已注入的样式
  let style = shadowRoot.value.querySelector('.font-size-styles');

  if (!style) {
    // 如果样式没有注入，则创建并注入样式
    style = document.createElement('style');
    style.className = 'font-size-styles'; // 给样式添加一个唯一的 class
    shadowRoot.value.appendChild(style);
  }

  // 更新样式内容
  style.textContent = `
    div {
      font-size: ${fontSize.value}px !important;
    }
    div h1, div h2, div h3, div h4, div h5, div h6 {
      font-size: ${headingFontSize.value}px !important;
    }
  `;
};

watch([fontSize, headingFontSize, maxHeight, readerWidth], () => {
  showPage(); // 页面更新
});

const showPage = (pageIndex?: number) => {
  if (hiddenContainer.value === undefined) return;
  if (readerContainer.value === undefined) return;
  adjustFontSize();
  hiddenContainer.value.style.width = `${readerWidth.value * 0.9}px`;
  readerContainer.value.style.width = `${readerWidth.value}px`;
  pages.value = getPages(rawElements.value as HTMLElement[]);
  if (pageIndex === undefined) {
    //! 这堆抽象东西用来防止拖字体大小拉爆阅读器
    //   const temp = Math.round(totalPages.value * readProgress.value);
    //   // console.log("will to",temp,"max",totalPages.value)
    //   if (temp >= totalPages.value - 1) {
    //     // console.log("too high")
    //     currentPage.value = totalPages.value - 1;
    //   } else if (temp < 0) {
    //     currentPage.value = 0;
    //   } else {
    //     currentPage.value = temp;
    //   }
    // } else {
    //   currentPage.value = pageIndex;
    // }
    if (totalPages.value > 1) {
      // 根据 readProgress 计算出 pageIndex
      const calculatedPageIndex = Math.round(readProgress.value * (totalPages.value - 1));
      // 确保 pageIndex 不小于 0，且不大于 totalPages.value - 1
      pageIndex = Math.max(0, Math.min(calculatedPageIndex, totalPages.value - 1));
    } else {
      // 如果总页数小于等于1，则始终在第0页
      pageIndex = 0;
    }
  }
  currentPage.value = pageIndex;
  // console.log(currentPage.value)
  renderPage(currentPage.value);
};

// 深拷贝函数
const deepClone = <T,>(obj: T): T => {
  // 处理 DOM 元素
  if (obj instanceof Node) {
    return obj.cloneNode(true) as T; // 克隆元素及其所有子节点
  }

  // 处理对象
  if (obj && typeof obj === 'object') {
    // 处理数组
    if (Array.isArray(obj)) {
      return obj.map((item) => deepClone(item)) as unknown as T; // 对数组中的每个元素进行深拷贝
    }

    // 处理普通对象
    const copy: Record<string, unknown> = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        copy[key] = deepClone(obj[key]); // 对对象的每个属性进行深拷贝
      }
    }
    return copy as T;
  }

  // 其他基本类型直接返回
  return obj;
};

const initReader = () => {
  if (patchouliContent.value === undefined) return;
  shadowRoot.value = patchouliContent.value.attachShadow({ mode: 'open' });
  hiddenContainer.value = document.createElement('div');
  hiddenContainer.value.style.position = 'absolute';
  //TODO 不是这个原因
  // hiddenContainer.value.style.visibility = 'hidden';
  hiddenContainer.value.id = 'taster-container';
  hiddenContainer.value.style.height = 'auto';
  hiddenContainer.value.style.width = `${readerWidth.value * 0.9}px`;

  shadowRoot.value.appendChild(hiddenContainer.value);
  readerContainer.value = document.createElement('div');
  readerContainer.value.id = 'content-container';
  readerContainer.value.style.visibility = 'hidden';
  readerContainer.value.style.width = `${readerWidth.value}px`;
  shadowRoot.value.appendChild(readerContainer.value);
};

const loadContent = async () => {
  try {
    const response = await fetch('content.html');
    const text = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(text, 'text/html');
    const title = doc.querySelector('title')?.innerText;
    if (title) {
      document.title = title;
    }

    const linkTags = doc.querySelectorAll('link[rel="stylesheet"]');
    linkTags.forEach((link) => {
      const htmlLink = link as HTMLLinkElement;
      if (!shadowRoot.value?.querySelector(`link[href="${htmlLink.href}"]`)) {
        const newLink = document.createElement('link');
        newLink.rel = 'stylesheet';
        newLink.href = htmlLink.href;
        shadowRoot.value?.appendChild(newLink);
      }
    });

    const styleTags = doc.querySelectorAll('style');
    styleTags.forEach((style) => {
      const styleElement = document.createElement('style');
      styleElement.innerHTML = style.innerHTML;
      shadowRoot.value?.appendChild(styleElement);
    });
    if (readerContainer.value === undefined) return;
    const bodyContent = doc.querySelector('body')?.innerHTML || '';
    readerContainer.value.innerHTML = bodyContent;
    rawElements.value = flattenDOM(readerContainer.value);
    // rawElements.value = deepClone(flattenDOM(readerContainer.value));
    //TODO 其实问题应该不是深拷贝？

    // const temp = structuredClone(readerContainer.value);
    // rawElements.value = flattenDOM(temp);

    showPage(0); //! 显示首页
  } catch (error) {
    console.error('加载内容失败:', error);
  }
};

// 生命周期钩子
onMounted(() => {
  initReader(); //! 初始化未受vue托管的dom树
  loadContent();
  nextTick(() => {
    // 等待 Vue 完成 DOM 更新后获取元素的尺寸
    if (patchouliReader.value) {
      readerWidth.value = patchouliReader.value.offsetWidth;
      maxHeight.value = patchouliReader.value.offsetHeight;
    }
    window.addEventListener('resize', handleResize);
  });
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
});
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
</style>
