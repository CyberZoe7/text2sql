<template>
  <div id="app">
    <div class="login-container">
      <h2 class="title">欢迎登录</h2>

      <!-- 顶部次级链接 -->
      <div class="top-actions">
        <button type="button" class="link-btn small" @click="toModifyPermission">
          修改权限
        </button>
        <button type="button" class="link-btn small" @click="toConnectDB">
          选择数据库
        </button>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="input-group">
          <label for="username">用户名</label>
          <input
            type="text"
            id="username"
            v-model="username"
            placeholder="请输入用户名"
            required
          />
        </div>

        <div class="input-group">
          <label for="password">密码</label>
          <input
            type="password"
            id="password"
            v-model="password"
            placeholder="请输入密码"
            required
          />
        </div>

        <!-- 主操作按钮 -->
        <div class="button-group">
          <button type="submit" class="btn primary">登录</button>
          <button type="button" class="btn secondary" @click="toRegister">
            注册
          </button>
        </div>

        <div class="extra-actions">
          <button type="button" class="link-btn" @click="toForgotPassword">
            忘记密码？
          </button>
        </div>

        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { LOGIN_URL } from "@/api";
import ConnectDB from "@/components/ConnectDB.vue";
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
    async handleLogin() {
      this.errorMessage = "";
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
          localStorage.setItem(
            "userInfo",
            JSON.stringify({
              username: response.data.username,
              permission: response.data.permission,
              token: response.data.token,
            })
          );
          localStorage.setItem("loginTime", Date.now().toString());
          this.$router.push("/query");
        } else {
          this.errorMessage = "用户名或密码错误！";
        }
      } catch {
        this.errorMessage = "登录请求失败，请确定是否已连接数据库";
      }
    },
    toRegister() {
      this.$router.push("/register");
    },
    toForgotPassword() {
      this.$router.push("/forgot-password");
    },
    toModifyPermission() {
      this.$router.push("/modify-permission");
    },
    toConnectDB(){
      this.$router.push("/connectdb");
    }
  },
};
</script>

<style scoped>
/* 全局重置 */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

/* 背景渐变 */
#app {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #e0f7fa, #80deea);
  font-family: "Helvetica Neue", Arial, sans-serif;
}

/* 卡片容器 */
.login-container {
  background: #ffffff;
  width: 100%;
  max-width: 400px;
  padding: 30px 25px;
  border-radius: 12px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}
.login-container:hover {
  transform: translateY(-4px);
}

/* 标题 */
.title {
  font-size: 1.75rem;
  color: #00796b;
  text-align: center;
  margin-bottom: 25px;
}

/* 表单布局 */
.login-form {
  display: flex;
  flex-direction: column;
}

/* 输入框组 */
.input-group {
  margin-bottom: 20px;
}
.input-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #004d40;
}
.input-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #b2dfdb;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}
.input-group input:focus {
  outline: none;
  border-color: #00796b;
}
/* 顶部次级链接：放在标题下方，右对齐 */
.top-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 16px;
}

/* 小号链接样式，跟忘记密码保持一致，但字体更小 */
.link-btn.small {
  font-size: 0.85rem;
  color: #00796b;
}
.link-btn.small:hover {
  color: #004d40;
}
/* 按钮组 */

/* 主操作按钮组 */
.button-group {
  display: flex;
  gap: 10px;
  margin: 20px 0;
}
.button-group .btn {
  flex: 1;
}
.btn {
  flex: 1;
  padding: 10px 0;
  font-size: 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}
.btn:hover {
  transform: translateY(-2px);
}
.primary {
  background-color: #00796b;
  color: #fff;
}
.primary:hover {
  background-color: #004d40;
}
.secondary {
  background-color: #b2dfdb;
  color: #004d40;
}
.secondary:hover {
  background-color: #80cbc4;
}

/* 忘记密码 链接 */
.extra-actions {
  text-align: center;
  margin-bottom: 15px;
}
.link-btn {
  background: none;
  border: none;
  color: #00796b;
  font-size: 0.95rem;
  cursor: pointer;
  text-decoration: underline;
  transition: color 0.2s;
}
.link-btn:hover {
  color: #004d40;
}

/* 错误提示 */
.error-message {
  text-align: center;
  color: #d32f2f;
  margin-top: 10px;
  font-weight: 500;
}
</style>
