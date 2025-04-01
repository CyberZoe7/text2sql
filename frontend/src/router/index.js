import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Login.vue';
import QueryForm from '../components/QueryForm.vue';
import Register from '../components/Register.vue';
import ForgotPassword from "@/components/ForgotPassword.vue";
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
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: ForgotPassword
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
