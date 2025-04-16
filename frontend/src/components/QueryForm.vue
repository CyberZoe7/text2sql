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


        <!-- 图表生成按钮 -->
        <div class="chart-buttons">
          <button @click="openChartModal('line')">生成折线图</button>
          <button @click="openChartModal('bar')">生成柱状图</button>
          <button @click="openChartModal('pie')">生成饼图</button>
        </div>
      </div>

      <!-- 弹窗：图表配置 -->
      <div v-if="showChartModal" class="modal-overlay">
        <div class="modal">
          <h3>配置图表数据</h3>
          <div v-if="chartType === 'line' || chartType === 'bar'">
            <div class="form-group">
              <label>选择统计数据字段（数值型）:</label>
              <select v-model="selectedStatField">
                <option v-for="field in numericFields" :key="field" :value="field">{{ field }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>选择横坐标字段:</label>
              <select v-model="selectedXAxisField">
                <option v-for="field in nonNumericFields" :key="field" :value="field">{{ field }}</option>
              </select>
            </div>
          </div>
<div v-else-if="chartType === 'pie'">
  <div class="form-group">
    <label>选择分类字段:</label>
    <select v-model="selectedXAxisField"> <!-- 改为使用X轴字段 -->
      <option v-for="field in nonNumericFields" :key="field" :value="field">{{ field }}</option>
    </select>
  </div>
  <div class="form-group">
    <label>选择统计字段:</label>
    <select v-model="selectedStatField"> <!-- 新增数值字段选择 -->
      <option v-for="field in numericFields" :key="field" :value="field">{{ field }}</option>
    </select>
  </div>
</div>
          <div class="modal-actions">
            <button @click="generateChart">生成图表</button>
            <button @click="closeChartModal">取消</button>
          </div>
        </div>
      </div>

      <!-- 根据选择动态渲染图表 -->
      <div v-if="chartData" class="chart-display">
        <component :is="currentChartComponent" :chartData="chartData" />
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
import LineChart from '@/components/LineChart.vue'
import BarChart from '@/components/BarChart.vue'
import PieChart from '@/components/PieChart.vue'

export default {
  components: {
    LineChart,
    BarChart,
    PieChart
  },


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
      "我想知道男性员工中出生日期在1985-03-15以后人的所有信息",
      "我想知道所有的客户名称和联系电话",
      "我想知道所有产品的信息",
      "I would like to know all the product information",
      "I would like to know all the names and contact numbers of all customers",
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


    /* ======================== 图表部分 ============================= */
    // 控制图表弹窗的显示
    const showChartModal = ref(false)
    // 当前选择的图表类型
    const chartType = ref('')
    // 选择的统计字段（数值型）、横坐标字段以及饼图的名称字段
    const selectedStatField = ref('')
    const selectedXAxisField = ref('')
    const selectedPieField = ref('')

    // 保存生成的图表数据，传递到图表组件中
    const chartData = ref(null)
    // 当前渲染的图表组件名称
    const currentChartComponent = ref('')

    // 判断结果中哪些字段为数字（统计字段）
    const numericFields = computed(() => {
      if (!result.value || !result.value.result.length) return []
      const fields = []
      tableHeaders.value.forEach(field => {
        // 取第一行测试是否能转换为数字
        const firstVal = result.value.result[0][field]
        if (!isNaN(parseFloat(firstVal)) && isFinite(firstVal)) {
          fields.push(field)
        }
      })
      return fields
    })

    // 非数值型字段作为横坐标（可根据业务需求调整）
    const nonNumericFields = computed(() => {
      return tableHeaders.value.filter(field => !numericFields.value.includes(field))
    })

    // 打开图表配置弹窗
    const openChartModal = (type) => {
      // 如果没有数据，则不显示
      if (!result.value || !result.value.result.length) {
        alert("查询结果为空，无法生成图表")
        return
      }
      chartType.value = type
      // 对于折线图和柱状图，必须有可统计的数值字段，否则提示用户
      if ((type === 'line' || type === 'bar') && numericFields.value.length === 0) {
        alert("结果中没有数值型数据，无法生成折线图/柱状图")
        return
      }
      showChartModal.value = true
      // 默认选择第一个可用选项（如果有）
      if (type === 'line' || type === 'bar') {
        selectedStatField.value = numericFields.value[0] || ''
        selectedXAxisField.value = nonNumericFields.value[0] || ''
  } else if (type === 'pie') {
    selectedXAxisField.value = nonNumericFields.value[0] || ''
    selectedStatField.value = numericFields.value[0] || '' // 新增默认数值字段选择
  }
    }

    const closeChartModal = () => {
      showChartModal.value = false
    }

    // 生成图表数据，根据用户选择更新chartData，并决定渲染哪个图表组件
    const generateChart = () => {
      // 折线图、柱状图：需要统计字段和横坐标字段
      if (chartType.value === 'line' || chartType.value === 'bar') {
        if (!selectedStatField.value || !selectedXAxisField.value) {
          alert("请选择统计数据及横坐标字段")
          return
        }
        // 整理数据：横坐标数据和对应的数值
        const labels = result.value.result.map(row => row[selectedXAxisField.value])
        const dataValues = result.value.result.map(row => parseFloat(row[selectedStatField.value]))
        const dataObj = {
          labels,
          datasets: [
            {
              label: selectedStatField.value,
              data: dataValues,
              borderColor: '#4CAF50',
              backgroundColor: chartType.value === 'bar' ? 'rgba(54, 162, 235, 0.5)' : undefined,
              tension: chartType.value === 'line' ? 0.1 : undefined
            }
          ]
        }
        chartData.value = dataObj
        currentChartComponent.value = chartType.value === 'line' ? 'LineChart' : 'BarChart'
      } else if (chartType.value === 'pie') {
  if (!selectedXAxisField.value || !selectedStatField.value) {
    alert("请选择分类字段和统计字段")
    return
  }
  const groupedData = {}
  result.value.result.forEach(row => {
    const category = row[selectedXAxisField.value]
    const value = parseFloat(row[selectedStatField.value]) || 0

    if (!groupedData[category]) {
      groupedData[category] = 0
    }
    groupedData[category] += value
  })

  const labels = Object.keys(groupedData)
  const dataValues = Object.values(groupedData)

  const dataObj = {
    labels,
    datasets: [{
      label: selectedStatField.value,
      data: dataValues,
      backgroundColor: [
        '#FF6384', '#36A2EB', '#FFCE56',
        '#4BC0C0', '#9966FF', '#FF9F40'
      ]
    }]
  }

  chartData.value = dataObj
  currentChartComponent.value = 'PieChart'
}
      showChartModal.value = false
    }
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
      exportToExcel,
      showChartModal,
      chartType,
      openChartModal,
      closeChartModal,
      generateChart,
      numericFields,
      nonNumericFields,
      selectedStatField,
      selectedXAxisField,
      selectedPieField,
      chartData,
      currentChartComponent
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

/* 图表按钮 */
.chart-buttons {
  margin-top: 20px;
}
.chart-buttons button {
  margin-right: 10px;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  width: 300px;
}
.form-group {
  margin-bottom: 15px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
}
.modal-actions {
  text-align: right;
}
.modal-actions button {
  margin-left: 10px;
}

/* 图表展示区域 */
.chart-display {
  margin-top: 20px;
}
</style>
