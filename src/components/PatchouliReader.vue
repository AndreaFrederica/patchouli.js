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
        :onReaderClick="onReaderClick"
        :current-page="currentPage + 1"
        :total-pages="totalPages"
        :progress="progress"
        v-model:fontSize="fontSize"
        v-model:headingFontSize="headingFontSize"
        @prev-page="prevPage"
        @next-page="nextPage"
        @end-on-reader-click="endOnReaderClick"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onBeforeUnmount, ref, computed, nextTick, watch } from 'vue';
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

const totalPages = computed(() => pages.value.length);
const progress = computed(() => ((currentPage.value + 1) / totalPages.value) * 100);

const onReaderClick = ref(0);

const handleResize = () => {
  if (patchouliReader.value) {
    readerWidth.value = patchouliReader.value.offsetWidth;
    maxHeight.value = patchouliReader.value.offsetHeight;
  }
};

const endOnReaderClick = () => {
  onReaderClick.value = 0;
  // 清弹出状态栏的中断
};

// 点击翻页处理函数
const handleClick = (event: MouseEvent) => {
  const clickX = event.clientX;
  const screenWidth = window.innerWidth;
  const edgeWidth = screenWidth * 0.4; // 边缘区域为 20%

  // 仅在左右边缘20%点击才触发翻页
  if (clickX < edgeWidth) {
    prevPage(); // 点击左侧20%区域
  } else if (clickX > screenWidth - edgeWidth) {
    nextPage(); // 点击右侧20%区域
  } else {
    // console.log('11111');
    onReaderClick.value = 1;
  }
};

// 触摸滑动开始处理函数（全屏检测）
const handleTouchStart = (event: TouchEvent) => {
  touchStartX.value = event.touches[0].clientX;
};

// 触摸滑动结束处理函数（全屏检测）
const handleTouchEnd = (event: TouchEvent) => {
  touchEndX.value = event.changedTouches[0].clientX;
  handleSwipe();
};

// 滑动处理函数（全屏范围内检测滑动）
const handleSwipe = () => {
  if (touchStartX.value === null || touchEndX.value === null) return;

  const swipeDistance = touchEndX.value - touchStartX.value;
  // 设置滑动的阈值，避免误触
  const swipeThreshold = 50;

  if (swipeDistance > swipeThreshold) {
    prevPage(); // 右滑（向右滑动）
  } else if (swipeDistance < -swipeThreshold) {
    nextPage(); // 左滑（向左滑动）
  }
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

const getPages = (elements?: HTMLElement[]): HTMLElement[][] => {
  const pages: HTMLElement[][] = [];
  let currentPage: HTMLElement[] = [];
  if (elements === undefined) return pages;
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
    pages.push(currentPage);
    (hiddenContainer.value as HTMLElement).innerHTML = '';
  }
  return pages;
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
    const temp = Math.round(totalPages.value * readProgress.value);
    // console.log("will to",temp,"max",totalPages.value)
    if (temp >= totalPages.value - 1) {
      // console.log("too high")
      currentPage.value = totalPages.value - 1;
    } else if (temp < 0) {
      currentPage.value = 0;
    } else {
      currentPage.value = temp;
    }
  } else {
    currentPage.value = pageIndex;
  }
  // console.log(currentPage.value)
  renderPage(currentPage.value);
};

const initReader = () => {
  if (patchouliContent.value === undefined) return;
  shadowRoot.value = patchouliContent.value.attachShadow({ mode: 'open' });
  hiddenContainer.value = document.createElement('div');
  hiddenContainer.value.style.position = 'absolute';
  hiddenContainer.value.style.visibility = 'hidden';
  hiddenContainer.value.style.height = 'auto';
  hiddenContainer.value.style.width = `${readerWidth.value * 0.9}px`;

  shadowRoot.value.appendChild(hiddenContainer.value);
  readerContainer.value = document.createElement('div');
  readerContainer.value.id = 'content-container';
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
