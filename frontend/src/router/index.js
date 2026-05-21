import { createRouter, createWebHashHistory } from 'vue-router'

// 懒加载组件
const HomeView = () => import('../views/HomeView.vue')
// const AboutView = () => import('../views/AboutView.vue')

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    }
  ]
})

export default router