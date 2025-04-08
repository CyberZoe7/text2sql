<template>
  <div class="container">
    <!-- 用户信息显示 -->
    <div class="user-info">
      <span class="username-icon">👤</span>
      <span class="username-text">
        {{ username }} (权限：{{ permission }})
      </span>
    </div>
    <div class="card">
      <h2>基于 Text2SQL 的智能数据库查询系统</h2>
      <textarea
        v-model="sentence"
        placeholder="请输入查询需求，例如：我想查找产品表的所有信息"
        rows="4">
      </textarea>
      <button @click="submitQuery">查询</button>
      <!-- 在查询按钮下显示响应时间 -->
      <div v-if="responseTime !== null" class="response-time">
        响应时间：{{ responseTime }} 毫秒
      </div>
      <div v-if="loading" class="status loading">查询中...</div>
      <div v-if="error" class="status error">{{ error }}</div>
      <div v-if="result" class="result">
        <h3>生成的 SQL 语句:</h3>
        <pre>{{ result.sql }}</pre>
        <button class="download-btn" @click="exportToExcel">下载Excel结果</button>
        <h3>查询结果:</h3>
        <table>
          <thead>
            <tr>
              <th v-for="header in tableHeaders" :key="header">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in result.result" :key="index">
              <td v-for="header in tableHeaders" :key="header">{{ row[header] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { QUERY_URL } from "@/api";
import * as XLSX from 'xlsx'; // 新增导入

export default {
  setup() {
    // 从路由中获取 username 和 permission 参数
    const route = useRoute();
    const username = ref(route.query.username || '未登录用户');
    // permission 初始值为字符串，如果需要做数值判断，转换为数值
    const permission = ref(route.query.permission || 0);

    const sentence = ref('');
    const result = ref(null);
    const loading = ref(false);
    const error = ref('');
    // 新增响应时间，初始为 null
    const responseTime = ref(null);

    const tableHeaders = computed(() => {
      if (result.value && result.value.headers && result.value.headers.length > 0) {
        return result.value.headers;
      }
      return [];
    });

    const submitQuery = async () => {
      error.value = '';
      result.value = null;
      responseTime.value = null;
      if (!sentence.value.trim()) {
        error.value = '请输入查询需求';
        return;
      }
      loading.value = true;
      // 记录开始时间（毫秒）
      const startTime = Date.now();
      try {
        // 注意将 permission 参数（转换为数字）传递给后端
        const response = await axios.post(QUERY_URL, {
          sentence: sentence.value,
          permission: Number(permission.value)
        });
        result.value = response.data;
      } catch (err) {
        error.value = err.response ? err.response.data.detail : err.message;
      } finally {
        loading.value = false;
        // 计算响应时间
        const endTime = Date.now();
        responseTime.value = endTime - startTime;
      }
    };
    // 新增导出方法
    const exportToExcel = () => {
      if (!result.value || !tableHeaders.value.length) return;

      const worksheetData = [
        tableHeaders.value,
        ...result.value.result.map(row =>
          tableHeaders.value.map(header => row[header])
        )
      ];

      const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "查询结果");
      XLSX.writeFile(workbook, `查询结果_${new Date().toLocaleString()}.xlsx`);
    };

    return {
      exportToExcel,
      username,
      permission,
      sentence,
      result,
      loading,
      error,
      tableHeaders,
      responseTime,
      submitQuery
    };
  }
};
</script>

<style scoped>
/* 用户信息样式 */
.user-info {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(255, 255, 255, 0.9);
  padding: 8px 15px;
  border-radius: 25px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 100;
}

.username-icon {
  font-size: 16px;
}

.username-text {
  font-size: 14px;
  color: #42b983;
  font-weight: 500;
}

/* 页面容器 */
.container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

/* 卡片样式 */
.card {
  background: #fff;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 700px;
  text-align: center;
}

/* 标题 */
h2 {
  margin-bottom: 20px;
  color: #333;
}

/* 文本域 */
textarea {
  width: 92%;
  padding: 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;
  margin-bottom: 15px;
}

/* 查询按钮 */
button {
  background-color: #42b983;
  color: #fff;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s ease;
  margin-bottom: 15px;
}

button:hover {
  background-color: #369870;
}

/* 响应时间样式 */
.response-time {
  font-size: 14px;
  color: #666;
  margin-bottom: 15px;
}

/* 状态提示 */
.status {
  margin: 10px 0;
  font-size: 14px;
}

.loading {
  color: #666;
}

.error {
  color: #e74c3c;
}

/* 查询结果区域 */
.result {
  margin-top: 20px;
  text-align: left;
}

/* SQL 语句预览 */
.result pre {
  background: #f0f0f0;
  padding: 10px;
  border-radius: 4px;
  overflow: auto;
}

/* 查询结果表格 */
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

th,
td {
  padding: 10px;
  border: 1px solid #ddd;
  text-align: center;
}

thead {
  background: #f7f7f7;
}

tbody tr:nth-child(even) {
  background: #fbfbfb;
}
/* 新增下载按钮样式（可选） */
.download-btn {
  margin: 15px 0;
  background-color: #42b983;
  color: white;
  padding: 10px 20px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  transition: background-color 0.3s;
}

.download-btn:hover {
  background-color: #369870;
}
</style>
