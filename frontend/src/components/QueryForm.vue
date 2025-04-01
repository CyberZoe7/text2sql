<template>
  <div class="container">
    <div class="card">
      <h2>基于 Text2SQL 的智能数据库查询系统</h2>
      <textarea
        v-model="sentence"
        placeholder="请输入查询需求，例如：我想查找商品信息表的所有信息"
        rows="4">
      </textarea>
      <button @click="submitQuery">查询</button>
      <div v-if="loading" class="status loading">查询中...</div>
      <div v-if="error" class="status error">{{ error }}</div>
      <div v-if="result" class="result">
        <h3>生成的 SQL 语句:</h3>
        <pre>{{ result.sql }}</pre>
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
import axios from 'axios';

export default {
  setup() {
    const sentence = ref('');
    const result = ref(null);
    const loading = ref(false);
    const error = ref('');

    const tableHeaders = computed(() => {
      if (result.value && result.value.headers && result.value.headers.length > 0) {
        return result.value.headers;
      }
      return [];
    });

    const submitQuery = async () => {
      error.value = '';
      result.value = null;
      if (!sentence.value.trim()) {
        error.value = '请输入查询需求';
        return;
      }
      loading.value = true;
      try {
        const response = await axios.post('http://10.135.9.41:8000/api/query', {
          sentence: sentence.value
        });
        result.value = response.data;
      } catch (err) {
        error.value = err.response ? err.response.data.detail : err.message;
      } finally {
        loading.value = false;
      }
    };

    return {
      sentence,
      result,
      loading,
      error,
      tableHeaders,
      submitQuery
    };
  }
};
</script>

<style scoped>
/* 页面容器居中并添加背景色 */
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
  width: 100%;
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
</style>
