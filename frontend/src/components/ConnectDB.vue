<template>
  <div id="app">
    <div class="login-container">
      <h2 class="title">数据库连接配置</h2>
      <form @submit.prevent="handleConnect" class="login-form">
        <!-- 数据库类型 -->
        <div class="input-group">
          <label>数据库类型</label>
          <div class="radio-group">
            <label>
              <input type="radio" value="mysql" v-model="dbType" /> MySQL
            </label>
            <label>
              <input type="radio" value="postgresql" v-model="dbType" /> PostgreSQL
            </label>
          </div>
        </div>

        <!-- 主机 -->
        <div class="input-group">
          <label for="host">主机 (Host)</label>
          <input
            id="host"
            type="text"
            v-model="host"
            placeholder="localhost"
            required
          />
        </div>

        <!-- 端口 -->
        <div class="input-group">
          <label for="port">端口 (Port)</label>
          <input
            id="port"
            type="number"
            v-model.number="port"
            :placeholder="dbType==='mysql' ? 3306 : 5432"
            required
          />
        </div>

        <!-- 用户名 -->
        <div class="input-group">
          <label for="username">用户名</label>
          <input
            id="username"
            type="text"
            v-model="username"
            placeholder="请输入用户名"
            required
          />
        </div>

        <!-- 密码 -->
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

        <!-- 数据库名 -->
        <div class="input-group">
          <label for="database">数据库名</label>
          <input
            id="database"
            type="text"
            v-model="database"
            placeholder="请输入数据库名称"
            required
          />
        </div>

        <!-- 按钮组 -->
        <div class="button-group">
          <button type="submit" class="btn primary">
            {{ loading ? '连接中...' : '连接' }}
          </button>
          <button type="button" class="btn secondary" @click="clearForm">
            清空
          </button>
        </div>

        <!-- 提示信息 -->
        <div v-if="message" :class="['error-message', success ? 'success' : '']">
          {{ message }}
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { CONNECT_DB_URL } from "@/api";

export default {
  name: "ConnectDB",
  data() {
    return {
      dbType: "mysql",
      host: "localhost",
      port: null,
      username: "",
      password: "",
      database: "",
      loading: false,
      message: "",
      success: false,
    };
  },
  watch: {
    // 根据类型自动填端口
    dbType(val) {
      this.port = val === "mysql" ? 3306 : 5432;
    }
  },
  methods: {
    async handleConnect() {
      this.message = "";
      this.success = false;
      if (!this.host || !this.port || !this.username || !this.password || !this.database) {
        this.message = "所有字段均为必填";
        return;
      }
      this.loading = true;
      try {
        const resp = await axios.post(CONNECT_DB_URL, {
          db_type: this.dbType,
          host: this.host,
          port: this.port,
          username: this.username,
          password: this.password,
          database: this.database
        });
        if (resp.data.success) {
          this.message = "连接成功！";
          this.success = true;
          // 可选：保存拼接好的 URL 以供后续使用
          localStorage.setItem("db_url", resp.data.db_url);
        } else {
          this.message = "连接失败，请检查参数";
        }
      } catch (err) {
        this.message = err.response?.data?.detail || "连接请求失败";
      } finally {
        this.loading = false;
      }
    },
    clearForm() {
      this.host = "localhost";
      this.port = this.dbType === "mysql" ? 3306 : 5432;
      this.username = "";
      this.password = "";
      this.database = "";
      this.message = "";
      this.success = false;
    }
  },
  created() {
    // 初始化端口
    this.port = 3306;
  }
};
</script>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }
#app {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; background: linear-gradient(135deg, #e0f7fa, #80deea);
  font-family: "Helvetica Neue", Arial, sans-serif;
}
.login-container {
  background: #fff; width: 100%; max-width: 400px;
  padding: 30px 25px; border-radius: 12px;
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
  transition: transform 0.3s;
}
.login-container:hover { transform: translateY(-4px); }
.title {
  font-size: 1.75rem; color: #00796b; text-align: center;
  margin-bottom: 25px;
}
.login-form { display: flex; flex-direction: column; }
.input-group { margin-bottom: 20px; }
.input-group label {
  display: block; margin-bottom: 6px;
  font-weight: 500; color: #004d40;
}
.input-group input {
  width: 100%; padding: 10px 12px;
  border: 1px solid #b2dfdb; border-radius: 6px;
  font-size: 1rem; transition: border-color 0.2s;
}
.input-group input:focus {
  outline: none; border-color: #00796b;
}
.radio-group {
  display: flex; gap: 20px; margin-top: 6px;
}
.radio-group label {
  font-size: 0.95rem; color: #004d40; cursor: pointer;
}
.radio-group input { margin-right: 6px; }
.button-group {
  display: flex; gap: 10px; margin-bottom: 15px;
}
.btn {
  flex: 1; padding: 10px 0; font-size: 1rem;
  border: none; border-radius: 6px; cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}
.btn:hover { transform: translateY(-2px); }
.primary {
  background-color: #00796b; color: #fff;
}
.primary:hover { background-color: #004d40; }
.secondary {
  background-color: #b2dfdb; color: #004d40;
}
.secondary:hover { background-color: #80cbc4; }
.error-message {
  text-align: center; margin-top: 10px; font-weight: 500;
}
.error-message.success { color: #388e3c; }
.error-message:not(.success) { color: #d32f2f; }
</style>
