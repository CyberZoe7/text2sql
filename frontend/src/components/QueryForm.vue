<!-- src/views/QueryForm.vue -->
<template>
  <div class="query-container">
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
      <aside class="template-aside">
        <h3>常用查询模板</h3>
        <ul>
          <li v-for="(tpl, i) in queryTemplates" :key="i" @click="applyTemplate(tpl)">
            {{ tpl }}
          </li>
        </ul>
      </aside>

      <!-- 中央查询区 -->
      <section class="query-section">
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
          <div v-if="result" class="result-panel">
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

        <!-- 渲染并优化图表展示 -->
        <div v-if="chartData" class="chart-container">
          <div class="chart-wrapper">
            <component :is="currentChartComponent" :chartData="chartData" class="chart-component" />
          </div>
        </div>
      </section>
    </main>

    <!-- 图表配置弹窗 -->
    <div v-if="showChartModal" class="modal-overlay">
      <div class="modal-card">
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
      "SELECT * FROM 员工 WHERE 部门编号 = '1'",
      "SELECT * FROM 订单 WHERE 订单日期 BETWEEN '2025-04-01' AND '2025-04-09'",
      "使用“采购明细详情”视图，筛选明细总额>10000.00的记录，提取产品名称和数量。",
      "我想查找男性员工中出生日期在1985-03-15以后人的所有信息",
      "我想查找所有的客户名称和联系电话",
      "我想查找所有产品的信息",
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
.query-container { display: flex; flex-direction: column; height: 100vh; }
.header-bar { display: flex; justify-content: space-between; align-items: center; padding: 0 24px; background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
.main-content { flex: 1; display: flex; overflow: hidden; }
.template-aside { width: 280px; background: #fafafa; padding: 16px; border-right: 1px solid #eee; overflow-y: auto; }
.template-aside ul li { padding: 8px; margin-bottom: 6px; border-radius: 4px; cursor: pointer; transition: background .2s; }
.template-aside ul li:hover { background: #e8f0fe; }
.query-section { flex: 1; padding: 24px; overflow-y: auto; }
textarea { width: 100%; height: 100px; resize: none; padding: 12px; border-radius: 4px; border: 1px solid #ddd; margin-bottom: 16px; }
.actions { display: flex; gap: 12px; margin-bottom: 12px; }
.btn { border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn.primary { background: #4caf50; color: #fff; }
.btn.secondary { background: #2196f3; color: #fff; }
.btn.tertiary { background: transparent; color: #2196f3; }
.msg { margin: 8px 0; }
.msg.error { color: #e74c3c; }
.msg.info { color: #666; }
.result-panel { margin-top: 16px; }
.result-table { width: 100%; border-collapse: collapse; margin-top: 12px; }
.result-table th, .result-table td { padding: 8px; text-align: center; border: 1px solid #eee; }
.panel { background: #fff; padding: 12px; border-radius: 4px; margin-bottom: 12px; }
.suggestions-panel .tag { cursor: pointer; background: #f0f4ff; padding: 4px 8px; border-radius: 12px; margin: 4px; display: inline-block; }
.chart-container { display: flex; flex-direction: column; align-items: center; margin-top: 24px; }
.chart-wrapper { width: 100%; max-width: 600px; background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.chart-component { width: 100%; height: 300px; }
.modal-overlay { position: fixed; top:0; left:0; right:0; bottom:0; display: flex; align-items:center; justify-content:center; background: rgba(0,0,0,0.4); }
.modal-card { background: #fff; border-radius: 6px; padding: 24px; width: 320px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top:16px; }
.fade-enter-active, .fade-leave-active { transition: opacity .3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>


