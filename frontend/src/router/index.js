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
    component: QueryForm,
    meta: { requiresAuth: true }
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
// 路由守卫
router.beforeEach((to, from, next) => {
  const userInfo = localStorage.getItem('userInfo');
  const loginTime = localStorage.getItem('loginTime');
  const maxSessionDuration = 60 * 60 * 1000; // 1 小时

  const now = Date.now();

  // 判断是否过期
  const isExpired = loginTime && (now - parseInt(loginTime) > maxSessionDuration);

  if (isExpired) {
    // 清除本地信息
    localStorage.removeItem('userInfo');
    localStorage.removeItem('loginTime');
  }

  // 再判断是否允许访问
  if (to.meta.requiresAuth && (!userInfo || isExpired)) {
    next('/'); // 没登录或者过期就跳转登录
  } else {
    next(); // 允许通行
  }
});
export default router;
