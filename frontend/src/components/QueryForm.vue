<!-- src/views/QueryForm.vue -->
<template>
  <div id="app">
    <!-- 顶部用户信息 -->
    <header class="header-bar">
      <div class="logo">🛠️ Text2SQL 系统</div>
      <div class="user-info">
        <span class="icon">👤</span>
        <span class="text">{{ username }} (权限：{{ permission }})</span>
      </div>
    </header>

    <main class="main-content">
      <!-- 左侧模板列表 -->
      <aside class="template-aside card">
        <h3>常用查询模板</h3>
        <ul>
          <li v-for="(tpl, i) in queryTemplates" :key="i" @click="applyTemplate(tpl)">
            {{ tpl }}
          </li>
        </ul>
      </aside>

      <!-- 中央查询区 -->
      <section class="query-section card">
        <textarea
          v-model="sentence"
          placeholder="请输入查询需求，例如：我想查找商品信息表的所有信息"
        />

        <div v-if="suggestions.length" class="panel suggestions-panel">
          <h4>请选择一个表：</h4>
          <div class="tags">
            <span
              v-for="(tbl, i) in suggestions"
              :key="i"
              class="tag"
              @click="applySuggestion(tbl)"
            >{{ tbl }}</span>
          </div>
        </div>

        <div v-if="suggestionText" class="panel hint-panel">
          <h4>智能提示</h4>
          <p>{{ suggestionText }}</p>
        </div>

        <div class="actions">
          <button
            @click="requestSuggestion"
            :disabled="suggestionLoading || queryLoading"
            class="btn secondary"
          >
            {{ suggestionLoading ? '响应中...' : '请求建议' }}
          </button>
          <button
            @click="submitQuery"
            :disabled="suggestionLoading || queryLoading"
            class="btn primary"
          >
            {{ queryLoading ? '查询中...' : '查询' }}
          </button>
        </div>

        <div v-if="error" class="msg error">{{ error }}</div>
        <div v-if="responseTime !== null" class="msg info">
          响应：{{ responseTime }} ms
        </div>

        <transition name="fade">
          <div v-if="result" class="result-panel card">
            <div class="sql-box">
              <strong>SQL:</strong>
              <code>{{ result.sql }}</code>
            </div>
            <button class="btn tertiary" @click="exportToExcel">下载 Excel</button>

            <table class="result-table">
              <thead>
                <tr>
                  <th v-for="h in tableHeaders" :key="h">{{ h }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in result.result" :key="idx">
                  <td v-for="h in tableHeaders" :key="h">{{ row[h] }}</td>
                </tr>
              </tbody>
            </table>

            <div class="chart-buttons">
              <button @click="openChartModal('line')" class="btn small">折线图</button>
              <button @click="openChartModal('bar')" class="btn small">柱状图</button>
              <button @click="openChartModal('pie')" class="btn small">饼图</button>
            </div>
          </div>
        </transition>

        <!-- 渲染图表 -->
        <div v-if="chartData" class="chart-container">
          <div class="chart-wrapper card">
            <component :is="currentChartComponent" :chartData="chartData" class="chart-component" />
          </div>
        </div>
      </section>
    </main>

    <!-- 图表配置弹窗 -->
    <div v-if="showChartModal" class="modal-overlay">
      <div class="modal-card card">
        <h3>配置图表</h3>
        <div v-if="chartType !== 'pie'">
          <label>数值字段：</label>
          <select v-model="selectedStatField">
            <option v-for="f in numericFields" :key="f" :value="f">{{ f }}</option>
          </select>
          <label>分类字段：</label>
          <select v-model="selectedXAxisField">
            <option v-for="f in nonNumericFields" :key="f" :value="f">{{ f }}</option>
          </select>
        </div>
        <div v-else>
          <label>分类字段：</label>
          <select v-model="selectedXAxisField">
            <option v-for="f in nonNumericFields" :key="f" :value="f">{{ f }}</option>
          </select>
          <label>数值字段：</label>
          <select v-model="selectedStatField">
            <option v-for="f in numericFields" :key="f" :value="f">{{ f }}</option>
          </select>
        </div>
        <div class="modal-actions">
          <button @click="generateChart" class="btn primary small">生成</button>
          <button @click="closeChartModal" class="btn secondary small">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import axios from 'axios';
import { QUERY_URL,SUGGESTION_URL } from "@/api";
import * as XLSX from 'xlsx';
import LineChart from '@/components/LineChart.vue'
import BarChart from '@/components/BarChart.vue'
import PieChart from '@/components/PieChart.vue'

export default {
  components: { LineChart, BarChart, PieChart },
  setup() {
    // 从路由获取用户名和权限参数
    // 新代码：从 localStorage 获取
    const userInfo = ref(JSON.parse(localStorage.getItem('userInfo')) || null);
    const username = ref(userInfo.value?.username || '未登录用户');
    const permission = ref(userInfo.value?.permission || 0); // 改为数字类型
    const sentence = ref('');
    const result = ref(null);
    const error = ref('');
    const responseTime = ref(null);
    const suggestionLoading = ref(false);
    const queryLoading = ref(false);
    // 智能提示候选表名
    const suggestions = ref([]);
    const suggestionText = ref(''); // 智能提示文本
    const tableHeaders = computed(() => {
      if (result.value && result.value.headers && result.value.headers.length > 0) {
        return result.value.headers;
      }
      return [];
    });

    // 常用查询模板示例数组（根据实际业务调整模板内容）
    const queryTemplates = ref([
      "SELECT 产品名称, 单价 FROM 产品 WHERE 库存数量 > 100",
      "SELECT c.客户名称, COUNT(o.订单编号) AS 订单数量, SUM(o.订单总额) AS 订单总额 FROM 客户 c LEFT JOIN 订单 o ON c.客户编号 = o.客户编号 GROUP BY c.客户名称;",
      "SELECT * FROM 订单 WHERE 订单日期 BETWEEN '2025-04-01' AND '2025-04-09'",
      "使用“采购明细详情”视图，筛选明细总额>10000.00的记录，提取产品名称和数量。",
      "我想查找男性员工中出生日期在1985-03-15以后人的所有信息",
      "统计每个客户的订单数量和订单总额。",
      "我想查找所有产品的信息",
      "列出所有员工的姓名、所在部门的名称和部门位置。",
      "I would like to find information on all products",
      "I would like to find all the customer names and contact numbers",
    ]);

    // 点击常用模板时自动填充到查询输入框
    const applyTemplate = (template) => {
      sentence.value = template;
    };
    // **新增**：点击候选表后自动补全
    const applySuggestion = (tbl) => {
      sentence.value = `SELECT * FROM ${tbl}`;
      suggestions.value = [];
    };
    // 点击“请求建议”
    const requestSuggestion = async () => {
      if (!sentence.value.trim()) { error.value = '请输入查询需求后再请求建议'; return; }
      suggestionLoading.value = true;
      error.value = '';
      suggestions.value = [];
      suggestionText.value = '';
      try {
        const resp = await axios.post(SUGGESTION_URL, { sentence: sentence.value });
        suggestionText.value = resp.data.suggestion;
      } catch (err) {
        error.value = err.response?.data?.detail || err.message;
      } finally {
        suggestionLoading.value = false;
      }
    };


    const submitQuery = async () => {
      if (!sentence.value.trim()) { error.value = '请输入查询需求'; return; }
      queryLoading.value = true;
      error.value = '';
      result.value = null;
      suggestions.value = [];
      suggestionText.value = '';
      const start = Date.now();
      try {
        const resp = await axios.post(QUERY_URL, { sentence: sentence.value });
        if (resp.data.suggestions) suggestions.value = resp.data.suggestions;
        else if (resp.data.suggestionText) suggestionText.value = resp.data.suggestionText;
        else result.value = resp.data;
      } catch (err) {
        error.value = err.response?.data?.detail || err.message;
      } finally {
        responseTime.value = Date.now() - start;
        queryLoading.value = false;
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
      if ((type === 'line' || type === 'bar'||type === 'pie') && numericFields.value.length === 0) {
        alert("结果中没有数值型数据，无法生成折线图/柱状图/饼图")
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
      applySuggestion,
      suggestions,
      suggestionText,
      username,
      permission,
      sentence,
      result,
      error,
      suggestionLoading,
      queryLoading,
      tableHeaders,
      responseTime,
      queryTemplates,
      applyTemplate,
      submitQuery,
      requestSuggestion,
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
      currentChartComponent,
    };
  }
};
</script>

<style scoped>
/* 全局重置与背景 */
* { box-sizing: border-box; margin: 0; padding: 0; }
#app {
  min-height: 100vh;
  background: linear-gradient(135deg, #e0f7fa, #80deea);
  font-family: "Helvetica Neue", Arial, sans-serif;
}

.header-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 24px; height: 60px; background: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  position: sticky; top: 0;
}
.logo { font-size: 1.25rem; color: #00796b; }
.user-info { display: flex; align-items: center; color: #004d40; }
.user-info .icon { margin-right: 6px; }

.main-content {
  display: flex; padding: 24px; gap: 16px;
}

.card {
  background: #ffffff; border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
  padding: 16px;
}

.template-aside {
  width: 260px; max-height: calc(100vh - 100px);
  overflow-y: auto;
}
.template-aside h3 { margin-bottom: 12px; color: #00796b; }
.template-aside ul { list-style: none; }
.template-aside li {
  padding: 8px; border-radius: 4px; cursor: pointer;
  transition: background 0.2s;
}
.template-aside li:hover { background: #e8f0fe; }

.query-section {
  flex: 1; display: flex; flex-direction: column;
}
.query-section textarea {
  width: 100%; height: 120px; resize: none;
  padding: 12px; border: 1px solid #b2dfdb;
  border-radius: 6px; font-size: 1rem;
  transition: border-color 0.2s;
}
.query-section textarea:focus {
  outline: none; border-color: #00796b;
}

.panel { margin-top: 12px; }
.suggestions-panel h4,
.hint-panel h4 { margin-bottom: 6px; color: #00796b; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag {
  background: #f0f4ff; padding: 6px 10px;
  border-radius: 12px; cursor: pointer;
  transition: background 0.2s;
}
.tag:hover { background: #d2e3fc; }

.actions { display: flex; gap: 12px; margin-top: 16px; }
.btn {
  padding: 10px 20px; font-size: 0.95rem;
  border: none; border-radius: 6px;
  cursor: pointer; transition: background 0.2s, transform 0.2s;
}
.primary {
  background: #00796b; color: #fff;
}
.primary:hover {
  background: #004d40; transform: translateY(-2px);
}
.secondary {
  background: #009688; color: #fff;
}
.secondary:hover {
  background: #00695c; transform: translateY(-2px);
}
.tertiary {
  background: transparent; color: #00796b;
}
.tertiary:hover { text-decoration: underline; }
.small { padding: 6px 12px; font-size: 0.85rem; }

.msg { margin-top: 12px; font-weight: 500; }
.error { color: #d32f2f; }
.info { color: #004d40; }

.result-panel { margin-top: 20px; }
.sql-box { margin-bottom: 12px; font-family: monospace; }
.result-table {
  width: 100%; border-collapse: collapse;
  margin-top: 12px;
}
.result-table th,
.result-table td {
  padding: 8px; text-align: center;
  border: 1px solid #eee;
}

.chart-buttons { margin-top: 16px; display: flex; gap: 8px; }

.chart-container { display: flex; justify-content: center; margin-top: 24px; }
.chart-wrapper { width: 100%; max-width: 600px; padding: 16px; }
.chart-component { width: 100%; height: 300px; }

.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
}
.modal-card { width: 320px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }

.fade-enter-active,
.fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>


