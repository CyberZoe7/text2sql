<template>
  <div id="forgot-password">
    <div class="forgot-container">
      <h2>忘记密码</h2>
      <form @submit.prevent="handleForgotPassword">

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

        <!-- 注册密钥 -->
        <div class="input-group">
          <label for="secretKey">注册密钥:</label>
          <input
            type="text"
            id="secretKey"
            v-model="secretKey"
            placeholder="请输入 8 位注册密钥"
            required
          />
        </div>

        <!-- 新密码 -->
        <div class="input-group">
          <label for="newPassword">新密码:</label>
          <input
            type="password"
            id="newPassword"
            v-model="newPassword"
            placeholder="请输入新密码"
            required
          />
        </div>

        <!-- 确认新密码 -->
        <div class="input-group">
          <label for="confirmPassword">确认新密码:</label>
          <input
            type="password"
            id="confirmPassword"
            v-model="confirmPassword"
            placeholder="请再次输入新密码"
            required
          />
        </div>

        <button type="submit" class="forgot-btn">提交</button>

        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
        <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { FORGOT_PASSWORD_URL } from "@/api";

export default {
  name: "ForgotPassword",
  data() {
    return {
      username: "",
      secretKey: "",        // 新增
      newPassword: "",
      confirmPassword: "",
      errorMessage: "",
      successMessage: ""
    };
  },
  methods: {
    async handleForgotPassword() {
      this.errorMessage = "";
      this.successMessage = "";

      // 基本校验
      if (!this.username || !this.secretKey || !this.newPassword || !this.confirmPassword) {
        this.errorMessage = "所有字段都不能为空";
        return;
      }
      if (this.newPassword !== this.confirmPassword) {
        this.errorMessage = "两次输入的新密码不一致";
        return;
      }

      try {
        const response = await axios.post(FORGOT_PASSWORD_URL, {
          username: this.username,
          secret_key: this.secretKey,      // 传递密钥
          new_password: this.newPassword
        });

        if (response.data.success) {
          this.successMessage = "密码已成功更新，请使用新密码登录！";
        } else {
          this.errorMessage = response.data.detail || "更新密码失败";
        }
      } catch (error) {
        this.errorMessage = error.response
          ? error.response.data.detail
          : error.message;
      }
    }
  }
};
</script>

<style scoped>
.forgot-container {
  width: 400px;
  margin: 50px auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
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
button.forgot-btn {
  width: 100%;
  padding: 10px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
button.forgot-btn:hover {
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
