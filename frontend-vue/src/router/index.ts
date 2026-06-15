import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/PublicLayout.vue'),
      children: [
        {
          path: '',
          name: 'self-service',
          component: () => import('@/views/SelfServiceView.vue'),
          meta: { public: true },
        },
      ],
    },
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      // All admin pages require login; viewer is bounced to self-service.
      meta: { requiresAuth: true, denyRoles: ['viewer'] },
      children: [
        { path: 'dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
        { path: 'tickets', name: 'tickets', component: () => import('@/views/TicketsView.vue') },
        { path: 'users', name: 'users', component: () => import('@/views/UsersView.vue') },
        { path: 'knowledge', name: 'knowledge', component: () => import('@/views/KnowledgeView.vue') },
        { path: 'rpa', name: 'rpa', component: () => import('@/views/RpaView.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  const denyRoles = to.meta.denyRoles as string[] | undefined
  if (denyRoles && auth.role && denyRoles.includes(auth.role)) {
    // viewer trying to reach the back office -> send to public self-service
    return { name: 'self-service' }
  }

  return true
})

export default router
