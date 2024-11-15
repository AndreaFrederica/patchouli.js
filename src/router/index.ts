import { createRouter, createWebHistory } from 'vue-router'
import PatchouliReader from '@/components/PatchouliReader.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: PatchouliReader, // 设置根路径渲染 PatchouliReader.vue
  },
  // 其他已注册的路由
  // { path: '/about', component: About },

  // Catch-all 路由，用来匹配所有未注册的路由
  {
    path: '/:pathMatch(.*)*',
    beforeEnter: async (to, from, next) => {
      // 尝试通过 fetch 请求检查目标文件是否存在
      const targetPath = `/public/${to.path}` // 构造文件的路径
      try {
        const response = await fetch(targetPath)

        // 如果目标文件存在，响应状态码为 200
        if (response.ok) {
          // 文件存在，重定向到目标文件
          window.location.href = targetPath
        } else {
          // 文件不存在，跳转到 404.html
          window.location.href = '/404.html'
        }
      } catch (error) {
        // 捕获错误时（比如文件无法访问），重定向到 404.html
        window.location.href = '/404.html'
      }
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
