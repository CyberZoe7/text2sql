<template>
  <div id="app">
    <div class="login-container">
      <h2>登录</h2>
      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <label for="username">用户名:</label>
          <input
            type="text"
            id="username"
            v-model="username"
            placeholder="请输入用户名"
            required
          />
        </div>

        <div class="input-group">
          <label for="password">密码:</label>
          <input
            type="password"
            id="password"
            v-model="password"
            placeholder="请输入密码"
            required
          />
        </div>
        <div class="grid-buttons">
          <button type="submit" class="login-btn">登录</button>
          <button type="button" class="Register_btn" @click="toRegister">注册</button>
        </div>
        <div class="extra-buttons">
          <button type="button" class="forgot-btn" @click="toForgotPassword">忘记密码？</button>
        </div>
        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { LOGIN_URL } from "@/api";
export default {
  name: "Login",
  data() {
    return {
      username: "",
      password: "",
      errorMessage: "",
    };
  },
  methods: {
    // 处理登录功能
async handleLogin() {
  if (!this.username || !this.password) {
    this.errorMessage = "用户名和密码不能为空";
    return;
  }
  try {
    const response = await axios.post(LOGIN_URL, {
      username: this.username,
      password: this.password,
    });
    if (response.data.success) {
        this.errorMessage = "";
        // 添加权限处理

        // 存储用户信息（含权限）
        localStorage.setItem('userInfo', JSON.stringify({
          username: response.data.username,
          permission: response.data.permission,
          token: response.data.token
        }));
        localStorage.setItem('loginTime', Date.now().toString()); // 当前时间戳（毫秒）

        this.$router.push({
          path: "/query"
        });
    } else {
      this.errorMessage = "用户名或密码错误！";
    }
  } catch (error) {
    this.errorMessage = "登录请求失败，请稍后再试！";
    }
  },
    toRegister() {
      this.$router.push("/register");
    },
    toForgotPassword() {
      this.$router.push("/forgot-password");
    }
  },
};
</script>

<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  text-align: center;
  margin-top: 50px;
}

.login-container {
  height: auto;
  width: 420px;
  margin: 0 auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

h2 {
  margin-bottom: 20px;
}

.input-group {
  margin-bottom: 20px;
  text-align: left;
}

.input-group label {
  display: block;
  margin-bottom: 5px;
}

.input-group input {
  width: 96%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.grid-buttons {
  display: grid;
  grid-template-columns: repeat(2, auto); /* 两列自动宽度 */
  gap: 10px;
  margin-bottom: 10px;
}

button.login-btn,
button.Register_btn{
  width: 100%;
  padding: 10px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
button.forgot-btn {
    background-color: transparent; /* 设置背景为透明 */
    border: none; /* 移除边框 */
    color: #000; /* 设置文本颜色，可以根据需要调整 */
    font-size: 16px; /* 设置字体大小，可以根据需要调整 */
    cursor: pointer; /* 鼠标悬停时显示手型指针 */
    padding: 0; /* 移除默认的内边距 */
}

button.login-btn:hover,
button.Register_btn:hover{
  background-color: #3e9c7b;
}

.extra-buttons {
  margin-bottom: 10px;
}

.error-message {
  margin-top: 10px;
  color: red;
}
</style>
