<template>
  <div class="batch-assessment">
    <div class="header">
      <h1>批量风险评估</h1>
      <p>支持多个患者的批量风险评估，提高筛查效率</p>
    </div>

    <div class="input-section">
      <div class="input-methods">
        <button 
          :class="['method-btn', { active: inputMethod === 'manual' }]"
          @click="inputMethod = 'manual'"
        >
          手动输入
        </button>
        <button 
          :class="['method-btn', { active: inputMethod === 'csv' }]"
          @click="inputMethod = 'csv'"
        >
          CSV文件上传
        </button>
      </div>

      <!-- 手动输入模式 -->
      <div v-if="inputMethod === 'manual'" class="manual-input">
        <div class="patients-list">
          <div v-for="(patient, index) in patients" :key="index" class="patient-form">
            <h3>患者 {{ index + 1 }}</h3>
            <div class="form-grid">
              <div class="form-group">
                <label>姓名:</label>
                <input v-model="patient.name" type="text" placeholder="患者姓名">
              </div>
              <div class="form-group">
                <label>年龄:</label>
                <input v-model.number="patient.age" type="number" min="18" max="100">
              </div>
              <div class="form-group">
                <label>BMI:</label>
                <input v-model.number="patient.bmi" type="number" step="0.1" min="15" max="50">
              </div>
              <div class="form-group">
                <label>吸烟史:</label>
                <select v-model="patient.smoking">
                  <option :value="false">否</option>
                  <option :value="true">是</option>
                </select>
              </div>
              <div class="form-group">
                <label>饮酒史:</label>
                <select v-model="patient.alcohol">
                  <option :value="false">否</option>
                  <option :value="true">是</option>
                </select>
              </div>
              <div class="form-group">
                <label>家族史:</label>
                <select v-model="patient.family_history">
                  <option :value="false">否</option>
                  <option :value="true">是</option>
                </select>
              </div>
              <div class="form-group">
                <label>症状评分:</label>
                <input v-model.number="patient.symptom_score" type="number" min="0" max="10">
              </div>
              <div class="form-group">
                <label>CEA (ng/mL):</label>
                <input v-model.number="patient.lab_cea" type="number" step="0.1" min="0">
              </div>
              <div class="form-group">
                <label>CA-125 (U/mL):</label>
                <input v-model.number="patient.lab_ca125" type="number" step="0.1" min="0">
              </div>
            </div>
            <button v-if="patients.length > 1" @click="removePatient(index)" class="remove-btn">
              删除患者
            </button>
          </div>
        </div>
        <div class="patient-controls">
          <button @click="addPatient" class="add-btn">添加患者</button>
          <button @click="clearAllPatients" class="clear-btn">清空所有</button>
        </div>
      </div>

      <!-- CSV上传模式 -->
      <div v-if="inputMethod === 'csv'" class="csv-input">
        <div class="upload-area">
          <input ref="csvFile" type="file" accept=".csv" @change="handleCSVUpload" style="display: none">
          <div class="upload-box" @click="$refs.csvFile.click()">
            <div class="upload-icon">📄</div>
            <p>点击上传CSV文件</p>
            <p class="upload-hint">文件应包含: name, age, bmi, smoking, alcohol, family_history, symptom_score, lab_cea, lab_ca125</p>
          </div>
        </div>
        <div v-if="csvData.length > 0" class="csv-preview">
          <h3>CSV数据预览 ({{ csvData.length }} 条记录)</h3>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>姓名</th>
                  <th>年龄</th>
                  <th>BMI</th>
                  <th>吸烟</th>
                  <th>饮酒</th>
                  <th>家族史</th>
                  <th>症状评分</th>
                  <th>CEA</th>
                  <th>CA-125</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in csvData.slice(0, 5)" :key="index">
                  <td>{{ row.name }}</td>
                  <td>{{ row.age }}</td>
                  <td>{{ row.bmi }}</td>
                  <td>{{ row.smoking ? '是' : '否' }}</td>
                  <td>{{ row.alcohol ? '是' : '否' }}</td>
                  <td>{{ row.family_history ? '是' : '否' }}</td>
                  <td>{{ row.symptom_score }}</td>
                  <td>{{ row.lab_cea }}</td>
                  <td>{{ row.lab_ca125 }}</td>
                </tr>
              </tbody>
            </table>
            <p v-if="csvData.length > 5" class="more-data">... 还有 {{ csvData.length - 5 }} 条记录</p>
          </div>
        </div>
      </div>
    </div>

    <div class="assessment-controls">
      <div class="options">
        <label>
          <input v-model="includeDetailedAnalysis" type="checkbox">
          包含详细分析
        </label>
      </div>
      <button 
        @click="performBatchAssessment" 
        :disabled="isAssessing || !hasValidData"
        class="assess-btn"
      >
        {{ isAssessing ? '评估中...' : '开始批量评估' }}
      </button>
    </div>

    <!-- 结果展示 -->
    <div v-if="assessmentResults" class="results-section">
      <div class="results-header">
        <h2>评估结果</h2>
        <div class="summary">
          <div class="summary-item">
            <span class="label">总患者数:</span>
            <span class="value">{{ assessmentResults.summary.total_patients }}</span>
          </div>
          <div class="summary-item">
            <span class="label">成功评估:</span>
            <span class="value">{{ assessmentResults.summary.successful_assessments }}</span>
          </div>
          <div class="summary-item">
            <span class="label">高风险患者:</span>
            <span class="value high-risk">{{ assessmentResults.summary.high_risk_patients }}</span>
          </div>
          <div class="summary-item">
            <span class="label">成功率:</span>
            <span class="value">{{ (assessmentResults.summary.success_rate * 100).toFixed(1) }}%</span>
          </div>
        </div>
      </div>

      <div class="results-table">
        <table>
          <thead>
            <tr>
              <th>患者</th>
              <th>风险分值</th>
              <th>风险等级</th>
              <th>置信度</th>
              <th>主要建议</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(result, index) in assessmentResults.results" :key="index">
              <td>{{ result.patient_data.name || `患者${index + 1}` }}</td>
              <td v-if="!result.error">
                <span :class="['risk-score', result.risk_level]">
                  {{ result.risk_score.toFixed(3) }}
                </span>
              </td>
              <td v-else>-</td>
              <td v-if="!result.error">
                <span :class="['risk-level', result.risk_level]">
                  {{ getRiskLevelText(result.risk_level) }}
                </span>
              </td>
              <td v-else>-</td>
              <td v-if="!result.error">{{ result.confidence.toFixed(3) }}</td>
              <td v-else>-</td>
              <td v-if="!result.error">{{ result.recommendations[0] || '暂无建议' }}</td>
              <td v-else>-</td>
              <td>
                <span v-if="result.error" class="status error">失败</span>
                <span v-else class="status success">成功</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="export-controls">
        <button @click="exportResults" class="export-btn">导出结果</button>
        <button @click="generateBatchReport" class="report-btn">生成批量报告</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BatchAssessment',
  data() {
    return {
      inputMethod: 'manual', // 'manual' or 'csv'
      patients: [this.createEmptyPatient()],
      csvData: [],
      includeDetailedAnalysis: false,
      isAssessing: false,
      assessmentResults: null
    }
  },
  computed: {
    hasValidData() {
      if (this.inputMethod === 'manual') {
        return this.patients.length > 0 && this.patients.some(p => p.age && p.bmi);
      } else {
        return this.csvData.length > 0;
      }
    }
  },
  methods: {
    createEmptyPatient() {
      return {
        name: '',
        age: 45,
        bmi: 24.0,
        smoking: false,
        alcohol: false,
        family_history: false,
        symptom_score: 3,
        lab_cea: 3.0,
        lab_ca125: 20.0
      };
    },
    addPatient() {
      this.patients.push(this.createEmptyPatient());
    },
    removePatient(index) {
      this.patients.splice(index, 1);
    },
    clearAllPatients() {
      this.patients = [this.createEmptyPatient()];
    },
    handleCSVUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const csv = e.target.result;
          const lines = csv.split('\n');
          const headers = lines[0].split(',').map(h => h.trim());
          
          this.csvData = [];
          for (let i = 1; i < lines.length; i++) {
            if (lines[i].trim()) {
              const values = lines[i].split(',').map(v => v.trim());
              const patient = {};
              headers.forEach((header, index) => {
                const value = values[index];
                if (header === 'age' || header === 'bmi' || header === 'symptom_score' || 
                    header === 'lab_cea' || header === 'lab_ca125') {
                  patient[header] = parseFloat(value) || 0;
                } else if (header === 'smoking' || header === 'alcohol' || header === 'family_history') {
                  patient[header] = value.toLowerCase() === 'true' || value === '1' || value.toLowerCase() === 'yes';
                } else {
                  patient[header] = value;
                }
              });
              this.csvData.push(patient);
            }
          }
          alert(`成功解析 ${this.csvData.length} 条患者数据`);
        } catch (error) {
          alert('CSV文件解析失败: ' + error.message);
        }
      };
      reader.readAsText(file);
    },
    async performBatchAssessment() {
      this.isAssessing = true;
      this.assessmentResults = null;

      try {
        const patientsData = this.inputMethod === 'manual' ? this.patients : this.csvData;
        
        const response = await fetch('/api/v1/assess/batch', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            patients: patientsData,
            include_detailed_analysis: this.includeDetailedAnalysis
          })
        });

        if (response.ok) {
          const data = await response.json();
          this.assessmentResults = data.data;
        } else {
          const error = await response.text();
          alert('批量评估失败: ' + error);
        }
      } catch (error) {
        alert('批量评估出错: ' + error.message);
      } finally {
        this.isAssessing = false;
      }
    },
    getRiskLevelText(level) {
      const levels = {
        'low': '低风险',
        'medium': '中风险', 
        'high': '高风险'
      };
      return levels[level] || level;
    },
    exportResults() {
      if (!this.assessmentResults) return;

      const csvContent = this.generateCSVContent();
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `batch_assessment_results_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    generateCSVContent() {
      const headers = ['患者姓名', '年龄', 'BMI', '风险分值', '风险等级', '置信度', '状态', '主要建议'];
      const rows = [headers.join(',')];
      
      this.assessmentResults.results.forEach((result, index) => {
        const row = [
          result.patient_data.name || `患者${index + 1}`,
          result.patient_data.age,
          result.patient_data.bmi,
          result.error ? '失败' : result.risk_score.toFixed(3),
          result.error ? '失败' : this.getRiskLevelText(result.risk_level),
          result.error ? '失败' : result.confidence.toFixed(3),
          result.error ? '失败' : '成功',
          result.error ? result.error : (result.recommendations[0] || '暂无建议')
        ];
        rows.push(row.join(','));
      });
      
      return rows.join('\n');
    },
    generateBatchReport() {
      // 这里可以调用后端API生成详细的批量报告
      alert('批量报告生成功能开发中...');
    }
  }
}
</script>

<style scoped>
.batch-assessment {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.header p {
  color: #7f8c8d;
  font-size: 16px;
}

.input-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.input-methods {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.method-btn {
  padding: 10px 20px;
  border: 2px solid #e0e0e0;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.method-btn.active {
  border-color: #3498db;
  background: #3498db;
  color: white;
}

.patient-form {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 20px;
  margin-bottom: 20px;
  position: relative;
}

.patient-form h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 500;
  margin-bottom: 5px;
  color: #34495e;
}

.form-group input,
.form-group select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.remove-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #e74c3c;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.patient-controls {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.add-btn, .clear-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.add-btn {
  background: #27ae60;
  color: white;
}

.clear-btn {
  background: #95a5a6;
  color: white;
}

.upload-area {
  margin-bottom: 20px;
}

.upload-box {
  border: 2px dashed #bdc3c7;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-box:hover {
  border-color: #3498db;
  background: #f8f9fa;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.upload-hint {
  font-size: 12px;
  color: #7f8c8d;
  margin-top: 10px;
}

.csv-preview {
  margin-top: 20px;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

th {
  background: #f8f9fa;
  font-weight: 600;
}

.more-data {
  text-align: center;
  padding: 10px;
  color: #7f8c8d;
  font-style: italic;
}

.assessment-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.assess-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.assess-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.results-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.results-header h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.summary-item {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  text-align: center;
}

.summary-item .label {
  display: block;
  font-size: 14px;
  color: #7f8c8d;
  margin-bottom: 5px;
}

.summary-item .value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #2c3e50;
}

.summary-item .value.high-risk {
  color: #e74c3c;
}

.results-table {
  overflow-x: auto;
  margin-bottom: 20px;
}

.risk-score.low { color: #27ae60; }
.risk-score.medium { color: #f39c12; }
.risk-score.high { color: #e74c3c; }

.risk-level.low { 
  background: #d5f4e6; 
  color: #27ae60; 
  padding: 4px 8px; 
  border-radius: 4px; 
  font-size: 12px;
}
.risk-level.medium { 
  background: #fef9e7; 
  color: #f39c12; 
  padding: 4px 8px; 
  border-radius: 4px; 
  font-size: 12px;
}
.risk-level.high { 
  background: #fadbd8; 
  color: #e74c3c; 
  padding: 4px 8px; 
  border-radius: 4px; 
  font-size: 12px;
}

.status.success {
  color: #27ae60;
  font-weight: 500;
}

.status.error {
  color: #e74c3c;
  font-weight: 500;
}

.export-controls {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.export-btn, .report-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.export-btn {
  background: #27ae60;
  color: white;
}

.report-btn {
  background: #9b59b6;
  color: white;
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .summary {
    grid-template-columns: 1fr;
  }
  
  .assessment-controls {
    flex-direction: column;
    gap: 15px;
  }
}
</style>