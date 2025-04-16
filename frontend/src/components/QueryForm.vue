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

      <!-- 常用查询模板区域 -->
      <div class="template-panel">
        <h3>常用查询模板</h3>
        <ul class="template-list">
          <li v-for="(template, index) in queryTemplates" :key="index" @click="applyTemplate(template)">
            {{ template }}
          </li>
        </ul>
      </div>

      <textarea
        v-model="sentence"
        placeholder="请输入查询需求，例如：我想查找商品信息表的所有信息"
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
import * as XLSX from 'xlsx';

export default {
  setup() {
    // 从路由获取用户名和权限参数
    const route = useRoute();
    const username = ref(route.query.username || '未登录用户');
    const permission = ref(route.query.permission || '未知');

    const sentence = ref('');
    const result = ref(null);
    const loading = ref(false);
    const error = ref('');
    const responseTime = ref(null);

    const tableHeaders = computed(() => {
      if (result.value && result.value.headers && result.value.headers.length > 0) {
        return result.value.headers;
      }
      return [];
    });

    // 常用查询模板示例数组（根据实际业务调整模板内容）
    const queryTemplates = ref([
      "SELECT 产品名称, 单价 FROM 产品 WHERE 库存数量 > 100",
      "SELECT * FROM 员工 WHERE 部门编号 = '1'",
      "SELECT * FROM 订单 WHERE 订单日期 BETWEEN '2025-04-01' AND '2025-04-09'",
      "我想知道所有男性员工的信息",
      "我想知道所有的客户名称和联系电话",
    ]);

    // 点击常用模板时自动填充到查询输入框
    const applyTemplate = (template) => {
      sentence.value = template;
    };

    const submitQuery = async () => {
      error.value = '';
      result.value = null;
      responseTime.value = null;
      if (!sentence.value.trim()) {
        error.value = '请输入查询需求';
        return;
      }
      loading.value = true;
      const startTime = Date.now();
      try {
        // 将 permission 参数传递给后端 (如果后端需要校验)
        const response = await axios.post(QUERY_URL, {
          sentence: sentence.value,
          permission: Number(permission.value)
        });
        result.value = response.data;
      } catch (err) {
        error.value = err.response ? err.response.data.detail : err.message;
      } finally {
        loading.value = false;
        const endTime = Date.now();
        responseTime.value = endTime - startTime;
      }
    };

    // 导出 Excel 的方法（保持原来逻辑）
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
      username,
      permission,
      sentence,
      result,
      loading,
      error,
      tableHeaders,
      responseTime,
      queryTemplates,
      applyTemplate,
      submitQuery,
      exportToExcel
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

/* 常用查询模板区域 */
.template-panel {
  background: #f7f7f7;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 15px;
  text-align: left;
}

.template-panel h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #333;
}

.template-list {
  list-style: none;
  padding-left: 0;
  margin: 0;
}

.template-list li {
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 4px;
  transition: background 0.3s;
  margin-bottom: 4px;
}

.template-list li:hover {
  background: #e0f7f1;
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

/* 下载按钮样式 */
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
