<template>
  <div id="register">
    <div class="register-container">
      <h2>注册</h2>
      <form @submit.prevent="handleRegister">
        <!-- 用户名 -->
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

        <!-- 密码 -->
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

        <!-- 确认密码 -->
        <div class="input-group">
          <label for="confirmPassword">确认密码:</label>
          <input
            type="password"
            id="confirmPassword"
            v-model="confirmPassword"
            placeholder="请再次输入密码"
            required
          />
        </div>

        <!-- 新增：密钥 -->
        <div class="input-group">
          <label for="secretKey">注册密钥:</label>
          <input
            type="text"
            id="secretKey"
            v-model="secretKey"
            placeholder="请输入 8 位密钥"
            required
          />
        </div>

        <button type="submit" class="register-btn">注册</button>

        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
        <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { REGISTER_URL } from "@/api";

export default {
  name: "Register",
  data() {
    return {
      username: "",
      password: "",
      confirmPassword: "",
      secretKey: "",      // 新增
      errorMessage: "",
      successMessage: ""
    };
  },
  methods: {
    async handleRegister() {
      this.errorMessage = "";
      this.successMessage = "";

      // 基本校验
      if (!this.username || !this.password || !this.confirmPassword || !this.secretKey) {
        this.errorMessage = "用户名、密码和密钥都不能为空";
        return;
      }
      if (this.password !== this.confirmPassword) {
        this.errorMessage = "两次输入的密码不一致，请重新输入";
        return;
      }

      try {
        const response = await axios.post(REGISTER_URL, {
          username: this.username,
          password: this.password,
          secret_key: this.secretKey    // 传递密钥
        });
        if (response.data.success) {
          this.successMessage = "注册成功，请登录！";
        } else {
          // 后端会返回 detail: "密钥不存在" 或 "用户名已存在" 等
          this.errorMessage = response.data.detail || "注册失败";
        }
      } catch (error) {
        this.errorMessage = error.response
          ? error.response.data.detail
          : error.message;
      }
    },
  },
};
</script>

<style scoped>
.register-container {
  width: 400px;
  margin: 50px auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
h2 {
  margin-bottom: 20px;
  text-align: center;
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
button.register-btn {
  width: 100%;
  padding: 10px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
button.register-btn:hover {
  background-color: #3e9c7b;
}
.error-message {
  margin-top: 10px;
  color: red;
}
.success-message {
  margin-top: 10px;
  color: green;
}
</style>