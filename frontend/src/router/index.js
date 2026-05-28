import { createRouter, createWebHashHistory } from 'vue-router'

// 懒加载组件
const HomeView = () => import('../views/HomeView.vue')
const LoginView = () => import('../views/admin/LoginView.vue')
const DashboardView = () => import('../views/admin/DashboardView.vue')

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/admin/login',
      name: 'admin-login',
      component: LoginView
    },
    {
      path: '/admin',
      name: 'admin',
      component: DashboardView,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !localStorage.getItem('token')) {
    return { name: 'admin-login' }
  }
})

export default router
