import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'

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

router.beforeEach(async (to) => {
  if (to.meta.requiresAuth) {
    const { state, isLoggedIn, fetchUser } = useAuth()
    if (!isLoggedIn.value) {
      return { name: 'admin-login', query: { redirect: to.fullPath } }
    }
    // 有 token 但还没拿到 user 信息，等一下再决定
    if (!state.user) {
      await fetchUser()
      if (!state.user) {
        return { name: 'admin-login', query: { redirect: to.fullPath } }
      }
    }
  }
})

export default router
