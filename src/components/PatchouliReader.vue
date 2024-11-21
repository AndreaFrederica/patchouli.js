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
        v-model:fontSize="fontSize"
        v-model:headingFontSize="headingFontSize"
        @prev-page="prevPage"
        @next-page="nextPage"
        @switch-paged_engine="switchPagedEngine"
        @switch-view-mode="switchViewMode"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onBeforeUnmount, ref, computed, nextTick, watch, provide } from 'vue';
import FloatingControls from '@/components/FloatingControls.vue';

const rawElements = ref<HTMLElement[]>(); // 原始html内容 这里面不知道为什么开启高级切分器后有可能进屎
// let rawElements: undefined | HTMLElement[] = undefined; // 原始html内容 这里面不知道为什么开启高级切分器后有可能进屎
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
const displayReadProgress = computed(() => readProgress.value * 100);

// 高阶分页支持
const flag_high_level_paged_engine = ref(true);
//TODO 依赖于深拷贝运行 但是不启用目前也没有去掉深拷贝（安全性）
const flag_single_page_mode = ref(false);
// TODO 未全部完成 单页流式阅读器
// 启用激进分页模式 目前一直开着
const flag_aggressive_paging_engine = ref(false);
// 激进分页模式的阈值 小于这个就进行激进分页
const aggressive_paging_threshold = 0.95; // 默认值为 0.9
// 分页模式的阈值 小于这个就进行分页
const paging_threshold = 0.95; // 默认值为 0.9
const flag_flatten_DOM = ref(true);
// 依赖展平dom树的方法来实现渲染
// TODO 应当实现一个不依赖dom展平的分页器

const onReaderClick = ref(false);
provide('PatchouliReader_onReaderClick', onReaderClick);

const handleResize = () => {
  if (patchouliReader.value) {
    readerWidth.value = patchouliReader.value.offsetWidth;
    maxHeight.value = patchouliReader.value.offsetHeight;
  }
};

// 点击翻页处理函数
const handleClick = (event: MouseEvent) => {
  // 检查是否存在选中的文本
  const selection = window.getSelection();
  if (selection && selection.toString().length > 0) {
    return; // 如果有选中文本，则忽略点击事件
  }

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

const handleWheel = (event: WheelEvent) => {
  if (flag_single_page_mode.value !== true) {
    //鼠标滚轮事件
    if (event.deltaY > 0) {
      // 向下滚动
      nextPage();
    } else if (event.deltaY < 0) {
      // 向上滚动
      prevPage();
    }
  } else {
    // 单页模式下转为计算阅读进度
    const scrollTop = window.scrollY; // 当前页面顶部滚动位置
    const scrollHeight = document.documentElement.scrollHeight; // 整个文档高度
    const clientHeight = document.documentElement.clientHeight; // 可视区域高度

    // 确保不会出现分母为 0 的情况
    readProgress.value =
      scrollHeight > clientHeight ? Math.min(scrollTop / (scrollHeight - clientHeight), 1) : 1;
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

const getParentTextContent = (element: HTMLElement): string => {
  let directText = '';
  Array.from(element.childNodes).forEach((child) => {
    if (child instanceof Text) {
      directText += child.nodeValue?.trim() || '';
    }
  });
  return directText;
};

const flattenDOM = (
  node: Node,
  flattenCompletely: boolean,
  parentClassPath = '',
): HTMLElement[] => {
  const elements: HTMLElement[] = [];

  node.childNodes.forEach((child) => {
    if (child.nodeType === Node.ELEMENT_NODE) {
      const element = child as HTMLElement;

      // 如果当前元素是 <ruby> 元素，直接保留
      if (element.nodeName === 'RUBY') {
        elements.push(element);
        return;
      }

      // 如果没有子元素，跳过展平，直接保留该元素
      if (!element.childNodes.length) {
        elements.push(element);
        return;
      }

      // 如果子元素只有 <ruby> 元素，保留 <ruby> 元素及其结构
      const hasOnlyRubyChild = Array.from(element.childNodes).every(
        (childNode) => childNode.nodeName === 'RUBY',
      );

      if (hasOnlyRubyChild) {
        elements.push(element);
        return;
      }

      if (flattenCompletely) {
        // 处理完全展平逻辑
        const currentClass = (node as HTMLElement).className || '';
        const sanitizedClass = currentClass.replace(/[^a-zA-Z0-9_-]/g, '-').replace(/^-+|-+$/g, '');

        const classPath = parentClassPath
          ? `${parentClassPath}__${sanitizedClass}`
          : sanitizedClass;

        if (classPath) {
          element.className = `${element.className} parent-${classPath}`;
        }

        const clonedElement = element.cloneNode(false) as HTMLElement; // 浅克隆移除子节点
        clonedElement.innerText = getParentTextContent(element);
        elements.push(clonedElement);
        elements.push(...flattenDOM(element, flattenCompletely, classPath));
      } else {
        // 保留嵌套关系，仅添加母节点本身
        elements.push(element);
      }
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
const getParagraphs_Simple = (element: HTMLElement): [HTMLElement, HTMLElement] | undefined => {
  const part1 = cloneElementStyleAndClass(element);
  const part2 = cloneElementStyleAndClass(element);

  // 获取原始文本内容
  const text = element.innerText;
  const container = hiddenContainer.value as HTMLElement;
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
  part1Text = part1Text.substring(0, part1Text.length - 1);
  part1.innerText = part1Text;
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
  let flag_high_level_paged = false;
  if (flag_single_page_mode.value) {
    // 单页流式阅读器
    elements.forEach((element) => {
      currentPage.push(element);
    });
    pages.push(currentPage);
    (hiddenContainer.value as HTMLElement).innerHTML = '';
    return pages;
  } else if (flag_high_level_paged_engine.value) {
    let i = 0;
    let end = elements.length;
    while (i < end) {
      // if (flag_high_level_paged) i--; // i++最先计算 发生插入后需要用这个修正？
      hiddenContainer.value?.appendChild(elements[i].cloneNode(true)); // 类型断言为 HTMLElement
      const now_hight = (hiddenContainer.value as HTMLElement).scrollHeight;
      if (now_hight <= maxHeight.value * paging_threshold) {
        // 能塞得进去 往这一页里面塞东西
        currentPage.push(elements[i]);
        i++;
      } else {
        // 碰撞测试失败 塞不进去 开始高级分页 或者结束一页
        hiddenContainer.value?.removeChild(hiddenContainer.value.lastChild as HTMLElement); // 清理失败节点 给高级分页流出空间
        let result = undefined; // 性能优化 避免重复调用高级分页算法
        if (flag_high_level_paged === false) result = getParagraphs_Simple(elements[i]);
        // console.log(flag_high_level_paged !== true && result !== undefined);
        if (flag_high_level_paged !== true && result !== undefined) {
          // 可以进行高级分页
          flag_high_level_paged = true;
          currentPage.push(<HTMLElement>result[0].cloneNode(true));
          elements.splice(i + 1, 0, <HTMLElement>result[1].cloneNode(true));
          i++;
          end++;
        } else {
          // 结束一页 高级分页失败了也会回退到这里
          if (currentPage.length === 0) {
            // 高级分页引擎也无法处理的东西 比如说图片
            currentPage.push(elements[i]);
            i++;
          }
          pages.push(currentPage);
          currentPage = [];
          (hiddenContainer.value as HTMLElement).innerHTML = '';
          flag_high_level_paged = false;
        }
      }
    }
    if (currentPage.length > 0) {
      // 最后一页
      pages.push(currentPage);
    }
    (hiddenContainer.value as HTMLElement).innerHTML = '';
    return pages;
  } else {
    // 最原始的老版本函数
    elements.forEach((element) => {
      hiddenContainer.value?.appendChild(element.cloneNode(true)); // 类型断言为 HTMLElement
      const elementHeight = (hiddenContainer.value as HTMLElement).scrollHeight;
      if (elementHeight > maxHeight.value * paging_threshold) {
        pages.push(currentPage);
        (hiddenContainer.value as HTMLElement).innerHTML = '';
        hiddenContainer.value?.appendChild(element.cloneNode(true));
        currentPage = [element];
      } else {
        currentPage.push(element);
      }
    });
    if (currentPage.length > 0) {
      // 最后一页
      pages.push(currentPage);
    }
    (hiddenContainer.value as HTMLElement).innerHTML = '';
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
  if (flag_single_page_mode.value !== true) {
    readProgress.value = pageIndex / (totalPages.value - 1);
  }
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

const switchPagedEngine = () => {
  flag_high_level_paged_engine.value = flag_high_level_paged_engine.value === true ? false : true;
};

const switchViewMode = () => {
  flag_single_page_mode.value = flag_single_page_mode.value === true ? false : true;
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

watch(
  [
    fontSize,
    headingFontSize,
    maxHeight,
    readerWidth,
    flag_high_level_paged_engine,
    flag_single_page_mode,
  ],
  () => {
    showPage(); // 页面更新
  },
);

const cloneHTMLElementList = (elements: HTMLElement[]): HTMLElement[] =>
  elements.map((el) => el.cloneNode(true) as HTMLElement);

const showPage = (pageIndex?: number) => {
  if (hiddenContainer.value === undefined) return;
  if (readerContainer.value === undefined) return;
  adjustFontSize();
  hiddenContainer.value.style.width = `${readerWidth.value}px`;
  readerContainer.value.style.width = `${readerWidth.value}px`;
  // pages.value = getPages(rawElements.value as HTMLElement[]);
  const temp = cloneHTMLElementList(rawElements.value as HTMLElement[]);
  pages.value = getPages(temp);
  if (pageIndex === undefined && flag_single_page_mode.value != true) {
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
  if (flag_single_page_mode.value) {
    pageIndex = 0;
  }
  if (pageIndex === undefined) {
    pageIndex = 0;
    console.log('在计算页码的时候未覆盖了');
    //TODO 这种情况真的存在吗
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
  hiddenContainer.value.style.width = `${readerWidth.value}px`;

  shadowRoot.value.appendChild(hiddenContainer.value);
  readerContainer.value = document.createElement('div');
  readerContainer.value.id = 'content-container';
  readerContainer.value.style.visibility = 'hidden';
  readerContainer.value.style.width = `${readerWidth.value}px`;
  // 注入 CSS 样式，限制图片高度
  const style = document.createElement('style');
  style.textContent = `
    img {
      max-height: 100%; /* 图片最大高度不超过容器 */
      max-width: 100%; /* 图片宽度自适应容器 */
      object-fit: contain; /* 等比缩放 */
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
  `;
  shadowRoot.value.appendChild(style);
  shadowRoot.value.appendChild(readerContainer.value);
};

function ensureCompleteHTML(htmlText: string) {
  // 确保输入是字符串
  if (typeof htmlText !== 'string') {
    throw new Error('Input must be a string');
  }

  const hasHtmlTag = /<html[\s\S]*?>/i.test(htmlText);
  const hasHeadTag = /<head[\s\S]*?>/i.test(htmlText);
  const hasBodyTag = /<body[\s\S]*?>/i.test(htmlText);

  // 如果没有 <html> 标签
  if (!hasHtmlTag) {
    // 检查是否包含其他 HTML 标签
    const containsHTMLTags = /<\w+[\s\S]*?>/i.test(htmlText);

    if (containsHTMLTags) {
      // 如果包含其他 HTML 标签，则包裹在 <html> 和 <body> 中
      htmlText = `<!DOCTYPE html><html><head></head><body>${htmlText}</body></html>`;
    } else {
      // 如果没有任何标签，直接补全空的 HTML 结构
      htmlText = `<!DOCTYPE html><html><head></head><body>${htmlText}</body></html>`;
    }
  } else {
    // 如果有 <html>，但没有 <head>
    if (!hasHeadTag) {
      if (hasBodyTag) {
        // 有 <body> 的情况，在 <body> 前补充 <head>
        htmlText = htmlText.replace(/<body[\s\S]*?>/i, (match) => `<head></head>${match}`);
      } else {
        // 没有 <body> 的情况，在 <html> 后插入 <head> 和 <body>
        htmlText = htmlText.replace(/<html[\s\S]*?>/i, (match) => `${match}<head></head><body>`);
        htmlText += '</body>';
      }
    }

    // 如果没有 <body>，在 </head> 后插入 <body>
    if (!hasBodyTag) {
      htmlText = htmlText.replace(/<\/head>/i, (match) => `${match}<body>`);
      htmlText += '</body>'; // 补充 <body> 尾
    }
  }

  // 确保 </html> 在文档的最后
  if (!/<\/html>$/i.test(htmlText)) {
    htmlText += '</html>';
  }

  return htmlText;
}

const parseHTML = (text: string) => {
  // 这个东西在目前环境下不太靠谱
  const parser = new DOMParser();
  const doc = parser.parseFromString(text, 'text/html');

  // 检查是否存在解析错误
  if (!doc.querySelector('parsererror')) {
    return doc; // 成功解析，返回整个 DOM 树
  }

  // 如果解析失败，使用 innerHTML 方法作为回退
  console.warn('DOMParser failed, falling back to innerHTML.');
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = text;

  // 包装成一个类似 DOM 树的文档结构
  const fallbackDoc = document.implementation.createHTMLDocument('');
  // fallbackDoc.body.append(...tempDiv.childNodes); // 将子节点复制到文档中
  fallbackDoc.body.append(...Array.from(tempDiv.childNodes));

  return fallbackDoc; // 返回整个回退的 DOM 树
};

const loadContent = async (url: string): Promise<void> => {
  try {
    // 获取 HTML 内容
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch content: ${response.status} ${response.statusText}`);
    }
    let text = await response.text();
    text = ensureCompleteHTML(text);

    // 解析 HTML
    // const parser = new DOMParser();
    // const doc = parser.parseFromString(text, 'text/html');
    const doc = parseHTML(text);

    // 更新页面标题
    const title = doc.querySelector('title')?.innerText;
    if (title) {
      document.title = title;
    }

    // 添加 <link> 样式表
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

    // 添加内联样式 <style>
    const styleTags = doc.querySelectorAll('style');
    styleTags.forEach((style) => {
      const styleElement = document.createElement('style');
      styleElement.textContent = style.textContent; // 优化为 textContent
      shadowRoot.value?.appendChild(styleElement);
    });

    // 确保阅读容器已初始化
    if (!readerContainer.value) {
      throw new Error('readerContainer 未初始化');
    }

    // 设置内容到阅读容器
    const bodyContent = doc.querySelector('body')?.innerHTML || '';
    readerContainer.value.innerHTML = bodyContent;

    // 克隆 DOM 并展平为元素列表
    const clonedContent = readerContainer.value.cloneNode(true) as HTMLElement;
    rawElements.value = flattenDOM(clonedContent, flag_flatten_DOM.value);
  } catch (error) {
    console.error('加载内容失败:', error);
    console.error(error);
  }
};

// 生命周期钩子
onMounted(async () => {
  initReader(); //! 初始化未受 Vue 托管的 DOM 树
  await loadContent('content.html'); //! 加载内容
  nextTick(() => {
    // 设置尺寸并绑定事件
    if (patchouliReader.value) {
      readerWidth.value = patchouliReader.value.offsetWidth;
      maxHeight.value = patchouliReader.value.offsetHeight;
    }
    window.addEventListener('resize', handleResize);
    window.addEventListener('wheel', handleWheel);
    nextTick(() => {
      showPage(0); //显示首页 不知道为什么 第一次预渲染不吃css
    });
  });
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  window.removeEventListener('wheel', handleWheel);
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
