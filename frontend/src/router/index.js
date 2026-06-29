import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Payments from '../views/Payments.vue'
import Projects from '../views/Projects.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import Clients from '../views/Clients.vue'
import ClientDetail from '../views/ClientDetail.vue'

const routes = [
  { path: '/',                component: Dashboard },
  { path: '/payments',        component: Payments },
  { path: '/projects',        component: Projects },
  { path: '/projects/:id',    component: ProjectDetail },
  { path: '/clients',         component: Clients },
  { path: '/clients/:id',     component: ClientDetail },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
