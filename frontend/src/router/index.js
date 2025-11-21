import { createRouter, createWebHistory } from 'vue-router'
import Screening from '../views/Screening.vue'
import SystemMonitor from '../views/SystemMonitor.vue'
import BatchAssessment from '../views/BatchAssessment.vue'

// Admin views
import AdminLogin from '../views/admin/AdminLogin.vue'
import AdminLayout from '../views/admin/AdminLayout.vue'
import AdminDashboard from '../views/admin/AdminDashboard.vue'
import AdminUsers from '../views/admin/AdminUsers.vue'
import AdminPatients from '../views/admin/AdminPatients.vue'
import AdminResources from '../views/admin/AdminResources.vue'
import AdminSchedules from '../views/admin/AdminSchedules.vue'
import TumorRecognition from '../views/TumorRecognition.vue'

const routes = [
  { path: '/', name: 'Home', component: Screening },
  { path: '/recognition', name: 'TumorRecognition', component: TumorRecognition },
  { path: '/monitor', name: 'SystemMonitor', component: SystemMonitor },
  { path: '/batch-assessment', name: 'BatchAssessment', component: BatchAssessment },
  { path: '/admin/login', name: 'AdminLogin', component: AdminLogin },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: AdminDashboard },
      { path: 'users', name: 'AdminUsers', component: AdminUsers },
      { path: 'patients', name: 'AdminPatients', component: AdminPatients },
      { path: 'resources', name: 'AdminResources', component: AdminResources },
      { path: 'schedules', name: 'AdminSchedules', component: AdminSchedules },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.matched.some(r => r.meta?.requiresAuth)) {
    const token = localStorage.getItem('token')
    if (!token) return next('/admin/login')
  }
  next()
})

export default router