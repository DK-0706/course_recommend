import { createRouter, createWebHistory } from 'vue-router'
import { api, type UserSession } from './api'
import LoginView from './views/LoginView.vue'
import StudentView from './views/StudentView.vue'
import TeacherView from './views/TeacherView.vue'
import AdminView from './views/AdminView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login/student' },
    { path: '/login/:role(student|teacher|admin)', component: LoginView, meta: { public: true } },
    { path: '/register', component: LoginView, meta: { public: true, registerRole: 'student' } },
    { path: '/register/:role(teacher|admin)', component: LoginView, meta: { public: true } },
    { path: '/student', component: StudentView, meta: { role: 'student' } },
    { path: '/teacher', component: TeacherView, meta: { role: 'teacher' } },
    { path: '/teacher/course/:action(add|edit|students)/:id?', component: TeacherView, meta: { role: 'teacher' } },
    { path: '/admin', component: AdminView, meta: { role: 'admin' } },
    { path: '/admin/logs', component: AdminView, meta: { role: 'admin' } },
    { path: '/:pathMatch(.*)*', redirect: '/login/student' },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  try {
    const user = await api<UserSession>('/api/auth/me')
    if (!user.authenticated || !user.role) return '/login/student'
    if (to.meta.role && user.role !== to.meta.role) return `/${user.role}`
    return true
  } catch {
    return '/login/student'
  }
})

export default router
