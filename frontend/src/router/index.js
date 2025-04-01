import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Login.vue';
import QueryForm from '../components/QueryForm.vue';

const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login
  },
  {
    path: '/query',
    name: 'QueryForm',
    component: QueryForm
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
