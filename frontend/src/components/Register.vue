<template>
  <div id="app">
    <div class="card-container">
      <h2 class="title">用户注册</h2>
      <form @submit.prevent="handleRegister" class="form">
        <div class="input-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="username"
            placeholder="请输入用户名"
            required
          />
        </div>

        <div class="input-group">
          <label for="password">密码</label>
          <input
            id="password"
            type="password"
            v-model="password"
            placeholder="请输入密码"
            required
          />
        </div>

        <div class="input-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            type="password"
            v-model="confirmPassword"
            placeholder="请再次输入密码"
            required
          />
        </div>

        <div class="input-group">
          <label for="secretKey">注册密钥</label>
          <input
            id="secretKey"
            v-model="secretKey"
            placeholder="请输入 8 位密钥"
            required
          />
        </div>

        <button type="submit" class="btn primary">注册</button>

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
      secretKey: "",
      errorMessage: "",
      successMessage: ""
    };
  },
  methods: {
    async handleRegister() {
      this.errorMessage = "";
      this.successMessage = "";

      if (!this.username || !this.password || !this.confirmPassword || !this.secretKey) {
        this.errorMessage = "所有字段都不能为空";
        return;
      }
      if (this.password !== this.confirmPassword) {
        this.errorMessage = "两次输入的密码不一致";
        return;
      }

      try {
        const resp = await axios.post(REGISTER_URL, {
          username: this.username,
          password: this.password,
          secret_key: this.secretKey
        });
        if (resp.data.success) {
          this.successMessage = "注册成功，请登录！";
        } else {
          this.errorMessage = resp.data.detail || "注册失败";
        }
      } catch (e) {
        this.errorMessage = e.response?.data.detail || e.message;
      }
    }
  }
};
</script>

<style scoped>
* { box-sizing: border-box; margin:0; padding:0; }
#app {
  display:flex; align-items:center; justify-content:center;
  min-height:100vh;
  background:linear-gradient(135deg,#e0f7fa,#80deea);
}
.card-container {
  background:#fff;
  width:100%; max-width:400px;
  padding:30px 25px;
  border-radius:12px;
  box-shadow:0 8px 16px rgba(0,0,0,0.1);
  transition:transform .3s;
}
.card-container:hover { transform:translateY(-4px); }

.title {
  text-align:center;
  font-size:1.75rem;
  color:#00796b;
  margin-bottom:20px;
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
  font-size:1rem;
  transition:border-color .2s;
}
.input-group input:focus {
  outline:none; border-color:#00796b;
}

.btn {
  width:100%; padding:10px;
  font-size:1rem; border:none;
  border-radius:6px; cursor:pointer;
  transition:background .2s, transform .2s;
}
.primary {
  background:#00796b; color:#fff;
  margin-top:10px;
}
.primary:hover {
  background:#004d40; transform:translateY(-2px);
}

.error-message {
  margin-top:12px;
  text-align:center; color:#d32f2f; font-weight:500;
}
.success-message {
  margin-top:12px;
  text-align:center; color:#388e3c; font-weight:500;
}
</style>
