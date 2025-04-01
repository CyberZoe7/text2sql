import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Login.vue';
import QueryForm from '../components/QueryForm.vue';
import Register from '../components/Register.vue';
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
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
