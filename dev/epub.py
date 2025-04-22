import os
import re
import io
import html
from typing import Optional
import zipfile
import mimetypes
import posixpath
import urllib.parse

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 添加 CORS 中间件，允许所有来源和 GET、POST、OPTIONS 方法
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "HEAD", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# 针对需要处理的文本类型文件
PROCESS_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "text/css",
    "application/javascript",
}


def translate_path(url_path: str) -> str:
    """
    将 URL 路径转换为本地文件系统路径，默认以当前工作目录作为根目录。
    """
    parsed = urllib.parse.urlparse(url_path)
    path = urllib.parse.unquote(parsed.path)
    if path.startswith("/"):
        path = path[1:]
    if not path:
        return os.getcwd()
    return os.path.join(os.getcwd(), path)


def list_directory(directory: str, request_path: str) -> HTMLResponse:
    """列出普通文件系统目录的内容"""
    try:
        entries = os.listdir(directory)
    except OSError:
        raise HTTPException(status_code=403, detail="无法列出目录")
    entries.sort()
    html_content = (
        f"<html><head><title>目录：{html.escape(request_path)}</title></head>"
    )
    html_content += f"<body><h2>目录：{html.escape(request_path)}</h2><hr><ul>"
    # 添加返回上一级目录链接（若不在根目录）
    if request_path != "/":
        parent = os.path.dirname(request_path.rstrip("/"))
        if not parent.endswith("/"):
            parent += "/"
        html_content += f'<li><a href="{html.escape(parent)}">..</a></li>'
    for name in entries:
        full_path = os.path.join(directory, name)
        display_name = name + "/" if os.path.isdir(full_path) else name
        link = urllib.parse.quote(name)
        url = (
            request_path.rstrip("/") + "/" + link if request_path != "/" else "/" + link
        )
        html_content += (
            f'<li><a href="{html.escape(url)}">{html.escape(display_name)}</a></li>'
        )
    html_content += "</ul><hr></body></html>"
    return HTMLResponse(content=html_content)


def list_epub_directory(
    z: zipfile.ZipFile, current_dir: str, base_url: str
) -> HTMLResponse:
    """
    针对 epub 内部的虚拟目录，生成目录列表页面。
    参数：
      - z: 已打开的 zipfile.ZipFile 对象
      - current_dir: 当前虚拟目录路径（使用 posix 格式，可能为空字符串）
      - base_url: 请求的 URL 前缀，用于构造超链接
    """
    # 保证以 "/" 结尾，方便后续匹配
    if current_dir and not current_dir.endswith("/"):
        current_dir += "/"
    # 获取当前目录下的所有直接子路径（文件或文件夹）
    dirs = set()
    files = []
    for name in z.namelist():
        if not name.startswith(current_dir):
            continue
        sub_path = name[len(current_dir) :]
        if not sub_path:
            continue
        parts = sub_path.split("/")
        if len(parts) > 1:
            dirs.add(parts[0])
        else:
            files.append(parts[0])
    dirs = sorted(dirs)
    files = sorted(files)
    html_content = f"<html><head><title>目录：{html.escape(base_url)}</title></head>"
    html_content += f"<body><h2>目录：{html.escape(base_url)}</h2><hr><ul>"
    # 如果不在根目录，增加返回上级目录链接
    if current_dir:
        # 截掉末尾的斜杠后取目录名称
        parent = posixpath.dirname(current_dir.rstrip("/"))
        if parent:
            parent += "/"
        html_content += f'<li><a href="{html.escape(parent)}">..</a></li>'
    for d in dirs:
        link = urllib.parse.quote(d)
        html_content += f'<li><a href="{html.escape(link)}/">{html.escape(d)}/</a></li>'
    for f in files:
        link = urllib.parse.quote(f)
        html_content += f'<li><a href="{html.escape(link)}">{html.escape(f)}</a></li>'
    html_content += "</ul><hr></body></html>"
    return HTMLResponse(content=html_content)


def recursive_search_opf(z: zipfile.ZipFile, current_dir: str = "") -> Optional[str]:
    """
    递归查找在当前目录（current_dir）下是否存在 content.opf 文件。
    若存在则返回该文件的完整路径；否则继续在当前目录的直接子目录中进行递归搜索。
    """
    # 确保 current_dir 以 "/" 结尾（除了空字符串）
    if current_dir and not current_dir.endswith("/"):
        current_dir += "/"

    # 构造候选文件路径
    candidate = current_dir + "content.opf"
    # 遍历 zip 中的所有条目查找直接匹配的 candidate
    for name in z.namelist():
        if name.lower() == candidate.lower():
            return name

    # 没有在当前目录直接找到，则收集当前目录下的所有直接子目录
    subdirs = set()
    for name in z.namelist():
        if not name.startswith(current_dir):
            continue
        # 剥离掉 current_dir 部分
        remaining = name[len(current_dir) :]
        # 如果 remaining 包含 '/'，则说明后面还有子目录
        if "/" in remaining:
            subdir = remaining.split("/", 1)[0]
            # 构造完整子目录路径（不带尾部斜杠）
            subdirs.add(current_dir + subdir)
    # 按照字母顺序遍历每个子目录进行递归搜索
    for subdir in sorted(subdirs):
        result = recursive_search_opf(z, subdir)
        if result:
            return result
    return None


def get_epub_root(z: zipfile.ZipFile) -> str:
    """
    递归搜索 epub 压缩包内 content.opf 文件所在目录。
    如果未找到，则抛出 HTTPException；否则返回 content.opf 所在的目录（如果在根目录则返回空字符串）。
    """
    result = recursive_search_opf(z, "")
    if not result:
        raise HTTPException(status_code=500, detail="epub 内未找到 content.opf")
    # 打印调试信息
    print(f"找到 content.opf 在: {posixpath.dirname(result)}/content.opf")
    return posixpath.dirname(result)


def is_directory_in_zip(z: zipfile.ZipFile, path: str) -> bool:
    """
    判断在 zip 包中，指定的 path 是否为目录
    如果有条目以 path + "/" 开头，认为它是目录。
    """
    if path and not path.endswith("/"):
        path += "/"
    for name in z.namelist():
        if name.startswith(path):
            return True
    return False


def find_in_zip(z: zipfile.ZipFile, path: str) -> bool:
    """判断 zip 包中是否存在指定的文件（路径精确匹配）"""
    return path in z.namelist()


@app.get("/{full_path:path}")
async def serve(full_path: str, request: Request):
    """
    根据 URL 路径提供文件服务：
      - 如果 URL 中包含 *.epub，则认为是请求 epub 内的文件
      - 否则按照普通文件系统处理
    """
    # 分析 URL 路径，看是否包含 .epub 节点
    parts = full_path.split("/")
    epub_index = None
    for i, part in enumerate(parts):
        if part.lower().endswith(".epub"):
            epub_index = i
            break

    if epub_index is not None:
        epub_filename = "/".join(parts[: epub_index + 1])
        inner_path = "/".join(parts[epub_index + 1 :])
        return await serve_epub(epub_filename, inner_path, request)
    else:
        # 普通文件系统处理
        url_path = "/" + full_path
        file_path = translate_path(url_path)
        if os.path.isdir(file_path):
            # 重定向目录（没有斜杠则添加）
            if not url_path.endswith("/"):
                return RedirectResponse(url=url_path + "/")
            for index in ("index.html", "index.htm"):
                index_path = os.path.join(file_path, index)
                if os.path.exists(index_path):
                    file_path = index_path
                    break
            else:
                return list_directory(file_path, url_path)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件未找到")
        ctype, _ = mimetypes.guess_type(file_path)
        print(f"type= {ctype}")
        if ctype is None:
            ctype = "application/octet-stream"
        if ctype in PROCESS_TYPES:
            try:
                with open(file_path, "rb") as f:
                    wrapper = io.TextIOWrapper(f, encoding="utf-8", errors="replace")
                    new_lines = []
                    host = request.headers.get("host", f"{request.client.host}:9100")
                    absolute_url_prefix = f"http://{host}/"

                    def replace_attr(match):
                        attr = match.group(1)
                        relative_path = match.group(2)
                        new_url = urllib.parse.urljoin(
                            absolute_url_prefix, relative_path
                        )
                        return f'{attr}="{new_url}"'

                    for line in wrapper:
                        new_line = re.sub(
                            r'(src|href)="(\.\./[^"]+)"', replace_attr, line
                        )
                        new_lines.append(new_line)
                    modified_content = "".join(new_lines)
                    encoded = modified_content.encode("utf-8")
                    return Response(content=encoded, media_type=ctype)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        else:
            return FileResponse(file_path, media_type=ctype)


async def serve_epub(epub_filename: str, inner_path: str, request: Request) -> Response:
    """
    处理 epub 文件：
      1. 根据 epub_filename 定位文件系统中 epub 文件；
      2. 打开 epub 压缩包，获取 content.opf 所在目录作为虚拟根目录；
      3. 根据 inner_path（相对于虚拟根目录）判断是目录或文件，目录则返回列表页，文件则返回文件内容，
         同时对文本文件按行处理并进行相同的替换逻辑。
    """
    fs_epub_path = translate_path("/" + epub_filename)
    if not os.path.exists(fs_epub_path):
        raise HTTPException(status_code=404, detail="epub 文件未找到")
    try:
        with zipfile.ZipFile(fs_epub_path, "r") as z:
            # 得到 epub 内虚拟根目录（content.opf 所在目录）
            epub_root = get_epub_root(z)  # 例如 "OEBPS" 或空字符串
            # 构造虚拟访问路径：将 epub_root 与 inner_path 结合
            # 注意使用 posixpath.join 以符合 zip 内文件路径的格式
            if inner_path:
                virtual_path = posixpath.join(epub_root, inner_path)
            else:
                virtual_path = epub_root

            # 如果虚拟路径对应的是目录（判断是否有条目以该路径为前缀）
            if is_directory_in_zip(z, virtual_path):
                # 如果 URL 没有以斜杠结束，则重定向补齐
                if not request.url.path.endswith("/"):
                    return RedirectResponse(url=request.url.path + "/")
                # 优先判断目录下是否有 index.html 或 index.htm
                for index in ("index.html", "index.htm"):
                    candidate = (
                        posixpath.join(virtual_path, index) if virtual_path else index
                    )
                    if find_in_zip(z, candidate):
                        virtual_path = candidate
                        break
                else:
                    # 返回目录列表页面
                    # base_url 即请求 URL 中 epub 文件后面的部分
                    return list_epub_directory(z, virtual_path, request.url.path)
            # 到这里，virtual_path 应该对应 zip 包中存在的文件
            if not find_in_zip(z, virtual_path):
                raise HTTPException(status_code=404, detail="文件未找到 in epub")
            # 读取文件内容（字节）
            data = z.read(virtual_path)
            # 根据文件后缀猜测 MIME 类型
            ctype, _ = mimetypes.guess_type(virtual_path)
            print(f"type= {ctype}")
            if ctype is None:
                ctype = "application/octet-stream"
            # 对于文本文件，按行处理替换
            if ctype in PROCESS_TYPES:
                try:
                    text = data.decode("utf-8", errors="replace")
                    # 构造绝对 URL 前缀，形如：http://host/epub文件名/
                    host = request.headers.get("host", f"{request.client.host}:9100")
                    absolute_url_prefix = f"http://{host}/{epub_filename}/"

                    def replace_attr(match):
                        attr = match.group(1)  # 'src' 或 'href'
                        relative_path = match.group(2)
                        # 移除所有前导的 "../"
                        while relative_path.startswith("../"):
                            relative_path = relative_path[3:]
                        # 使用 urljoin 拼接时此时不会发生跳级操作
                        new_url = urllib.parse.urljoin(
                            absolute_url_prefix, relative_path
                        )
                        return f'{attr}="{new_url}"'

                    new_lines = []
                    for line in text.splitlines(keepends=True):
                        new_line = re.sub(
                            r'(src|href)="(\.\./[^"]+)"', replace_attr, line
                        )
                        new_lines.append(new_line)

                    modified_content = "".join(new_lines)
                    encoded = modified_content.encode("utf-8")
                    return Response(content=encoded, media_type=ctype)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
            else:
                return Response(content=data, media_type=ctype)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="不是合法的 epub 文件")


if __name__ == "__main__":
    import uvicorn

    print("Serving at port 9100")
    uvicorn.run(app, host="0.0.0.0", port=9100)
