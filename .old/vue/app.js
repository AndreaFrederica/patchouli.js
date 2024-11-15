// app.js

Vue.component('pagination-panel', {
    props: ['currentPage', 'totalPages', 'progress'],
    template: `
        <div class="pagination-panel">
            <div>当前页: {{ currentPage }} / {{ totalPages }}</div>
            <div class="progress-bar">
                <div class="progress" :style="{ width: progress + '%' }"></div>
            </div>
            <div class="page-buttons">
                <button @click="$emit('prev-page')" :disabled="currentPage <= 1">上一页</button>
                <button @click="$emit('next-page')" :disabled="currentPage >= totalPages">下一页</button>
            </div>
        </div>
    `
});

new Vue({
    el: '#app',
    data() {
        return {
            pages: [],
            currentPage: 0,
            maxHeight: 600, // 单页最大高度
            fontSize: 16, // 正文字体大小（默认16px）
            headingFontSize: 24, // 各级标题的字体大小（默认24px）
        };
    },
    computed: {
        totalPages() {
            return this.pages.length;
        },
        progress() {
            return ((this.currentPage + 1) / this.totalPages) * 100;
        }
    },
    methods: {
        flattenDOM(node) {
            let elements = [];
            node.childNodes.forEach(child => {
                if (child.nodeType === Node.ELEMENT_NODE) {
                    elements.push(child);
                    elements = elements.concat(this.flattenDOM(child));
                }
            });
            return elements;
        },

        getPages(elements, shadowRoot) {
            const pages = [];
            const hiddenContainer = document.createElement('div'); // 创建一个隐藏容器
            hiddenContainer.style.position = 'absolute';
            hiddenContainer.style.visibility = 'hidden'; // 隐藏容器
            hiddenContainer.style.height = 'auto'; // 高度设置为自动（使其根据内容大小变化）

            // shadowRoot.appendChild(hiddenContainer); // 将隐藏容器添加到 shadowRoot
            this.shadowRoot.appendChild(hiddenContainer); // 将隐藏容器添加到 shadowRoot

            let currentPage = [];

            // 遍历所有元素并决定如何分页
            elements.forEach(element => {
                hiddenContainer.appendChild(element.cloneNode(true)); // 将元素添加到隐藏容器
                let elementHeight = hiddenContainer.scrollHeight; // 获取当前添加后的高度

                // 判断当前元素是否超出了最大页高度
                if (elementHeight > this.maxHeight) {
                    // 当前页满了，开始新的一页
                    pages.push(currentPage);
                    hiddenContainer.innerHTML = ''; // 清空隐藏容器
                    hiddenContainer.appendChild(element.cloneNode(true)); // 将当前元素作为新的一页开始
                    currentPage = [element]; // 将当前元素作为新的页面
                } else {
                    currentPage.push(element); // 否则将元素添加到当前页
                }
            });

            // 添加最后一页
            if (currentPage.length > 0) {
                pages.push(currentPage);
            }

            // shadowRoot.removeChild(hiddenContainer); // 清理隐藏容器
            this.shadowRoot.removeChild(hiddenContainer); // 清理隐藏容器

            return pages;
        }
        ,
        renderPage(pageIndex) {
            const contentContainer = this.shadowRoot.querySelector('#content-container');  // 获取容器
            contentContainer.innerHTML = ''; // 清空容器内容

            // 将当前页的元素渲染到 #content-container 中
            this.pages[pageIndex].forEach(element => {
                contentContainer.appendChild(element.cloneNode(true));
            });
        }
        ,

        prevPage() {
            if (this.currentPage > 0) {
                this.currentPage--;
                this.renderPage(this.currentPage, this.shadowRoot); // 调用修改后的 renderPage
            }
        },
        nextPage() {
            if (this.currentPage < this.totalPages - 1) {
                this.currentPage++;
                this.renderPage(this.currentPage, this.shadowRoot); // 调用修改后的 renderPage
            }
        },
        adjustFontSize() {
            // 获取 shadow DOM 内的 content 容器
            const contentContainer = this.shadowRoot.querySelector('#content');

            if (!contentContainer) return; // 确保 shadowRoot 中的 #content 容器存在

            // 调整正文字体大小
            contentContainer.style.fontSize = `${this.fontSize}px`;

            // 调整标题字体大小 (H1, H2, H3等)
            const headings = contentContainer.querySelectorAll('h1, h2, h3, h4, h5, h6');
            headings.forEach(heading => {
                heading.style.fontSize = `${this.headingFontSize}px`;
            });
        }
        ,
        async loadContent() {
            try {
                const response = await fetch('test/content.html');
                const text = await response.text();

                // 使用 DOMParser 解析 HTML 字符串
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');

                // 创建 shadowRoot
                const appContentContainer = document.getElementById('content');
                this.shadowRoot = appContentContainer.attachShadow({ mode: 'open' }); // 创建 shadow DOM

                // 提取标题并设置
                const title = doc.querySelector('title')?.innerText;
                if (title) {
                    document.title = title;
                }

                // 创建一个新的 div 容器并将其添加到 shadowRoot
                const contentContainer = document.createElement('div'); // 创建一个新的 div
                contentContainer.id = 'content-container'; // 给它一个唯一的 ID
                this.shadowRoot.appendChild(contentContainer); // 现在可以安全地将它添加到 shadowRoot 中

                // 提取并加载外部 CSS 文件到 shadowRoot
                const linkTags = doc.querySelectorAll('link[rel="stylesheet"]');
                linkTags.forEach(link => {
                    // 检查页面是否已经加载过该 CSS 文件，避免重复加载
                    if (!this.shadowRoot.querySelector(`link[href="${link.href}"]`)) {
                        const newLink = document.createElement('link');
                        newLink.rel = 'stylesheet';
                        newLink.href = link.href;  // 引用外部 CSS 文件
                        this.shadowRoot.appendChild(newLink); // 将外部样式文件添加到 shadowRoot
                    }
                });

                // 提取内联样式并注入到 shadowRoot
                const styleTags = doc.querySelectorAll('style');
                styleTags.forEach(style => {
                    const styleElement = document.createElement('style');
                    styleElement.innerHTML = style.innerHTML;
                    this.shadowRoot.appendChild(styleElement); // 将内联样式添加到 shadowRoot
                });


                // 提取 body 内容并注入到 contentContainer 内部
                const bodyContent = doc.querySelector('body').innerHTML;
                contentContainer.innerHTML = bodyContent;

                // 初始化分页内容
                const allElements = this.flattenDOM(contentContainer);
                this.pages = this.getPages(allElements);
                this.renderPage(this.currentPage);

                // 调整字体大小
                this.adjustFontSize();

            } catch (error) {
                console.error('加载内容失败:', error);
            }
        }


    },
    mounted() {
        this.$nextTick(() => {
            // 通过 ref 获取 app 元素并获取它的高度
            this.maxHeight = this.$refs.app.offsetHeight;
            console.log("App height:", this.maxHeight);
            this.loadContent(); // 加载外部内容
        });
    }
});
