<!-- # Patchouli.js -->

<!-- <div style="text-align: center;">
  <img src="https://s1.imagehub.cc/images/2024/11/23/061628d0fab6b4699c2c7b58a57dcd2f.png" alt="description" width="150" height="150">
</div> -->
  <!-- 文本 -->
  <!-- <h1 style="
       font-family: 'Gaegu', 'Noto Emoji', sans-serif; 
       font-size: 80px; 
       color: #efe0f7;">
    Patchouli.js
  </h1> -->

<div align=center>
  <!-- 图片 -->
  <img src="https://s1.imagehub.cc/images/2024/11/23/061628d0fab6b4699c2c7b58a57dcd2f.png" 
       alt="Description" 
       style="width: 150px; height: 150px;" />
<img src="https://s1.imagehub.cc/images/2024/11/23/61fdec4ace5670711d55156671145e51.png" 
       alt="Description" 
       style="width: 360px; height: 60px;" />
</div>

<!-- Google Fonts -->
<!-- <link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gaegu&family=Noto+Color+Emoji&family=Noto+Emoji:wght@300..700&display=swap" rel="stylesheet"> -->

## 简介

Patchouli.js 是一个基于 Vue 编写的 HTML 文档阅读器，支持单页和分页显示。它提供了灵活的界面和便捷的功能，允许用户在不同模式下查看文档内容，支持页面翻页、字体大小调整等功能，旨在提供一个用户友好的阅读体验。

目前Patchouli.js 尚未达到发布标准 如需使用 请自行人工引入 同时需自行修改挂载生命周期

### 关于测试

public里提供了`epub.py`用以进行开发测试 请自行准备epub文件用以测试

## 特性

- **单页与分页显示**：可以切换不同的显示模式，满足不同用户的需求。
- **翻页功能**：提供上一页、下一页的翻页控制，用户可以通过按钮方便地切换文档页。
- **字体大小调整**：用户可以根据自己的阅读习惯，动态调整文档正文和标题的字体大小。
- **高阶分页引擎**：根据需要启用更为复杂的分页控制，适应大型文档的阅读需求。
- **折叠面板**：提供一个可折叠的浮动面板，包含翻页、字体设置和模式切换等控制选项。
- **在线图片分页支持**：通过预缓存的方式来在没有图片大小注解的情况下正确切分包含图片的页面 此功能可能在低阶分页器中工作不正常

## 分页引擎

**如果Basic目标已经实现 则该组件可用**

#### 引擎

- [ ] 源生成：通过解析HTML和CSS来重新生成新的HTML和CSS来正确处理文档 （正在编写 可使用）
  - [x] Basic：html生成器
  - [ ] CSS生成器
- [ ] 指针：通过分页指针进行分页 可能对CSS的兼容性更好 （正在编写 可使用）
  - [x] Basic：基础解析
  - [x] Middle：模板生成
  - [ ] Advance: 复杂模板嵌套生成

#### 公共组件

- [ ] 段落切分器
  - [x] Basic：基础切分
  - [ ] 标点挤压 (短时间没有计划)
- [ ] CSS处理器
  - [x] Basic：自动引入
    - [x] 自动循环引用
  - [ ] CSS自定义
    - [ ] 流处理CSS
    - [ ] 额外CSS
- [ ] JS处理器（没有实现）
  - [ ] Basic：自动引入
    - [ ] 自动循环引用
  - [ ] JS自定义
    - [ ] 流处理JS
    - [ ] 额外JS
- [ ] 生命周期钩子
  - [x] afterRender
  - [ ] 导入接口
  - [ ] 从书籍导入

## 阅读模式

- **流式阅读器**：直接渲染RAW文档 提供最强的兼容性
- **高阶分页器**：基于段落+字符碰撞实现的分页 显示效果略好 但是目前不支持排版规则
- **低阶分页器**：基于段落碰撞实现的分页 能避免排版意外 但是在某些段落上回遇到不可预料的错误（超长段落） 目前此问题没有修复 请谨慎使用

## 待办事项清单

- [ ] JavaScript支持
- [ ] 更好的分页引擎
- [ ] 显示区域调整
- [ ] 完整的弹出工具栏
- [ ] 上状态栏
- [ ] 下状态栏
- [ ] 注解支持
- [x] epub支持（部分）
- [x] epub开发服务器
- [ ] 排版规则 可见的未来不会有计划支持
