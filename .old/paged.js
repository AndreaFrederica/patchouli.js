function flattenDOM(node) {
    let elements = [];
    node.childNodes.forEach(child => {
        if (child.nodeType === Node.ELEMENT_NODE) {
            elements.push(child);
            elements = elements.concat(flattenDOM(child));
        }
    });
    return elements;
}

function getPages(elements) {
    let pages = [];
    let currentPage = [];
    let currentHeight = 0;
    // const maxHeight = window.innerHeight;
    let maxHeight = 600;
    elements.forEach(element => {
        const elementHeight = element.offsetHeight;
        if (elementHeight > 0) {
            if (currentHeight + elementHeight > maxHeight) {
                pages.push(currentPage);
                currentPage = [element];
                currentHeight = elementHeight;
            } else {
                currentPage.push(element);
                currentHeight += elementHeight;
            }
        }
    });

    if (currentPage.length > 0) {
        pages.push(currentPage);
    }
    return pages
}

function renderPage(pageIndex, pages) {
    const container = document.getElementById('content');
    container.innerHTML = '';
    pages[pageIndex].forEach(element => {
        container.appendChild(element.cloneNode(true));
    });
    updateProgress(pageIndex + 1, pages.length);
}

function updateProgress(current, total) {
    document.getElementById('current-page').innerText = current;
    document.getElementById('total-pages').innerText = total;
    const progress = document.getElementById('progress');
    progress.style.width = `${(current / total) * 100}%`;
}

window.onload = () => {
    requestAnimationFrame(() => {
        const allElements = flattenDOM(document.getElementById('content'));
        const pages = getPages(allElements)


        // 初始渲染第一页
        let currentPageIndex = 0;
        renderPage(currentPageIndex, pages);

        // 更新总页数
        document.getElementById('total-pages').innerText = pages.length;

        // 翻页按钮事件
        document.getElementById('prev').addEventListener('click', () => {
            if (currentPageIndex > 0) {
                currentPageIndex--;
                renderPage(currentPageIndex, pages);
            }
        });

        document.getElementById('next').addEventListener('click', () => {
            if (currentPageIndex < pages.length - 1) {
                currentPageIndex++;
                renderPage(currentPageIndex, pages);
            }
        });
    });
};