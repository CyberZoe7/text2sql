<template>
  <div id="register">
    <div class="register-container">
      <h2>注册</h2>
      <form @submit.prevent="handleRegister">
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

        <button type="submit" class="register-btn">注册</button>

        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
        <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "Register",
  data() {
    return {
      username: "",
      password: "",
      errorMessage: "",
      successMessage: ""
    };
  },
  methods: {
    async handleRegister() {
      this.errorMessage = "";
      this.successMessage = "";
      if (!this.username || !this.password) {
        this.errorMessage = "用户名和密码不能为空";
        return;
      }
      try {
        const response = await axios.post("http://10.135.9.41:8000/api/register", {
          username: this.username,
          password: this.password,
        });
        if (response.data.success) {
          this.successMessage = "注册成功，请登录！";
          // 可选择自动跳转到登录页面
          // this.$router.push("/login");
        } else {
          this.errorMessage = response.data.detail || "注册失败";
        }
      } catch (error) {
        this.errorMessage = error.response ? error.response.data.detail : error.message;
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
