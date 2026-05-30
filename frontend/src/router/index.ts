import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const HomeView = () => import('../views/HomeView.vue')
const LoginView = () => import('../views/admin/LoginView.vue')
const AdminLayout = () => import('../views/admin/AdminLayout.vue')
const DashboardHome = () => import('../views/admin/DashboardHome.vue')
const VideoManage = () => import('../views/admin/VideoManage.vue')

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
      component: AdminLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'admin-home',
          component: DashboardHome
        },
        {
          path: 'videos',
          name: 'admin-videos',
          component: VideoManage
        }
      ]
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
