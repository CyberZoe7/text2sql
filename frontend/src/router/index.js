// 从vue-router库导入创建路由器和web history模式的函数
import { createRouter, createWebHistory } from 'vue-router';

// 导入路由对应的Vue组件
import Login from '../components/Login.vue';        // 登录组件
import QueryForm from '../components/QueryForm.vue'; // 查询表单组件 
import Register from '../components/Register.vue';   // 注册组件
import ForgotPassword from "@/components/ForgotPassword.vue"; // 忘记密码组件

// 导入axios库用于HTTP请求
import axios from 'axios'

// 配置axios请求拦截器
axios.interceptors.request.use(
  config => {
    // 从localStorage获取用户信息
    const userInfo = JSON.parse(localStorage.getItem('userInfo'))
    
    // 如果存在token，自动添加到请求头的Authorization字段
    if (userInfo?.token) {
      config.headers.Authorization = `Bearer ${userInfo.token}`
    }
    return config
  }, 
  error => {
    // 请求错误时直接拒绝Promise
    return Promise.reject(error)
  }
)

// 定义路由配置数组
const routes = [
  {
    path: '/',           // 路径
    name: 'Login',       // 路由名称
    component: Login     // 对应的组件
  },
  {
    path: '/query',
    name: 'QueryForm',
    component: QueryForm,
    meta: { requiresAuth: true } // 元数据，标识需要认证
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

// 创建路由器实例
const router = createRouter({
  // 使用HTML5 history模式
  history: createWebHistory(process.env.BASE_URL), // 基于环境变量的基础路径
  routes // 注入定义的路由配置
});

// 全局路由守卫
router.beforeEach((to, from, next) => {
  // 获取本地存储的用户信息和登录时间
  const userInfo = localStorage.getItem('userInfo');
  const loginTime = localStorage.getItem('loginTime');
  
  // 会话最大持续时间（1小时）
  const maxSessionDuration = 60 * 60 * 1000; 

  // 获取当前时间戳
  const now = Date.now();

  // 判断会话是否过期（登录时间存在且当前时间-登录时间 > 最大持续时间）
  const isExpired = loginTime && (now - parseInt(loginTime) > maxSessionDuration);

  // 如果已过期
  if (isExpired) {
    // 清除本地存储的认证信息
    localStorage.removeItem('userInfo');
    localStorage.removeItem('loginTime');
  }

  // 检查目标路由是否需要认证
  if (to.meta.requiresAuth) {
    // 如果用户信息不存在或会话过期
    if (!userInfo || isExpired) {
      next('/'); // 重定向到登录页
    } else {
      next(); // 放行
    }
  } else {
    next(); // 不需要认证的路由直接放行
  }
});

// 导出配置好的路由器实例
export default router;