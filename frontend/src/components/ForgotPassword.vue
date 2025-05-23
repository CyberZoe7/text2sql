<template>
  <div id="app">
    <div class="card-container">
      <h2 class="title">忘记密码</h2>
      <form @submit.prevent="handleForgot" class="form">
        <div class="input-group">
          <label for="username">用户名</label>
          <input id="username" v-model="username" placeholder="请输入用户名" required />
        </div>

        <div class="input-group">
          <label for="secretKey">注册密钥</label>
          <input id="secretKey" v-model="secretKey" placeholder="请输入注册密钥" required />
        </div>

        <div class="input-group">
          <label for="newPassword">新密码</label>
          <input
            id="newPassword"
            type="password"
            v-model="newPassword"
            placeholder="请输入新密码"
            required
          />
        </div>

        <div class="input-group">
          <label for="confirmPassword">确认新密码</label>
          <input
            id="confirmPassword"
            type="password"
            v-model="confirmPassword"
            placeholder="请再次输入新密码"
            required
          />
        </div>

        <button type="submit" class="btn primary">提交</button>

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
      secretKey: "",
      newPassword: "",
      confirmPassword: "",
      errorMessage: "",
      successMessage: ""
    };
  },
  methods: {
    async handleForgot() {
      this.errorMessage = "";
      this.successMessage = "";

      if (!this.username || !this.secretKey || !this.newPassword || !this.confirmPassword) {
        this.errorMessage = "所有字段都不能为空";
        return;
      }
      if (this.newPassword !== this.confirmPassword) {
        this.errorMessage = "两次输入的新密码不一致";
        return;
      }

      try {
        const resp = await axios.post(FORGOT_PASSWORD_URL, {
          username: this.username,
          secret_key: this.secretKey,
          new_password: this.newPassword
        });
        if (resp.data.success) {
          this.successMessage = "密码已更新，请使用新密码登录！";
        } else {
          this.errorMessage = resp.data.detail || "更新失败";
        }
      } catch (e) {
        this.errorMessage = e.response?.data.detail || e.message;
      }
    }
  }
};
</script>

<style scoped>
/* 与 Register.vue 同样的全局与容器样式 */
* { box-sizing:border-box; margin:0; padding:0; }
#app {
  display:flex; align-items:center; justify-content:center;
  min-height:100vh;
  background:linear-gradient(135deg,#e0f7fa,#80deea);
}
.card-container {
  background:#fff; max-width:400px; width:100%;
  padding:30px 25px; border-radius:12px;
  box-shadow:0 8px 16px rgba(0,0,0,0.1);
  transition:transform .3s;
}
.card-container:hover { transform:translateY(-4px); }
.title {
  text-align:center; font-size:1.75rem;
  color:#00796b; margin-bottom:20px;
}
.form { display:flex; flex-direction:column; }
.input-group { margin-bottom:18px; }
.input-group label {
  display:block; margin-bottom:6px;
  font-weight:500; color:#004d40;
}
.input-group input {
  width:100%; padding:10px 12px;
  border:1px solid #b2dfdb; border-radius:6px;
  transition:border-color .2s;
}
.input-group input:focus {
  outline:none; border-color:#00796b;
}
.btn {
  width:100%; padding:10px; font-size:1rem;
  border:none; border-radius:6px; cursor:pointer;
  transition:background .2s,transform .2s;
}
.primary {
  background:#00796b; color:#fff; margin-top:10px;
}
.primary:hover {
  background:#004d40; transform:translateY(-2px);
}
.error-message {
  margin-top:12px; text-align:center;
  color:#d32f2f; font-weight:500;
}
.success-message {
  margin-top:12px; text-align:center;
  color:#388e3c; font-weight:500;
}
</style>
