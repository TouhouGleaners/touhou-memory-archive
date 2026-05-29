import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'

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
    if (!state.user) {
      await fetchUser()
      if (!state.user) {
        return { name: 'admin-login', query: { redirect: to.fullPath } }
      }
    }
  }
})

export default router
