<template>
  <div class="card">
    <h2>受检信息与筛查输入</h2>
    <form @submit.prevent="assess">
      <div class="grid">
        <label>
          姓名（可选）
          <input v-model="patient.name" placeholder="匿名" />
        </label>
        <label>
          年龄
          <input type="number" v-model.number="form.age" min="0" max="120" required />
        </label>
        <label>
          BMI
          <input type="number" step="0.1" v-model.number="form.bmi" min="10" max="50" required />
        </label>
        <label>
          吸烟
          <input type="checkbox" v-model="form.smoking" />
        </label>
        <label>
          饮酒
          <input type="checkbox" v-model="form.alcohol" />
        </label>
        <label>
          家族肿瘤史
          <input type="checkbox" v-model="form.family_history" />
        </label>
        <label>
          症状评分（0-10）
          <input type="number" v-model.number="form.symptom_score" min="0" max="10" />
        </label>
        <label>
          CEA（ng/mL）
          <input type="number" v-model.number="form.lab_cea" min="0" max="100" />
        </label>
        <label>
          CA-125（U/mL）
          <input type="number" v-model.number="form.lab_ca125" min="0" max="500" />
        </label>
        <label>
          影像上传（支持PNG/JPG）
          <input type="file" accept=".jpg,.jpeg,.png" @change="onFile" />
        </label>
      </div>

      <div class="action-buttons">
        <button type="submit">评估风险</button>
        <button type="button" class="secondary" @click="recognizeImage" :disabled="!fileRef">识别</button>
      </div>
  </form>
  </div>

  <div v-if="result" class="card">
    <h2>评估结果</h2>
    <div class="result-grid">
      <div class="result-section">
        <h3>风险评估</h3>
        <p><strong>风险分值：</strong>{{ fmt(result.risk_score) }}</p>
        <p><strong>风险等级：</strong><span class="tag">{{ result.risk_level }}</span></p>
        <p><strong>置信度：</strong>{{ fmt(result.confidence) }}</p>
      </div>
      
      <div class="result-section" v-if="result.image_analysis">
        <h3>图像分析</h3>
        <p><strong>图像状态：</strong>{{ result.image_analysis.status }}</p>
        <p><strong>图像尺寸：</strong>{{ result.image_analysis.dimensions?.join('×') || '未知' }}</p>
        <p><strong>特征数量：</strong>{{ result.image_analysis.features_extracted || 0 }}</p>
      </div>
    </div>

    <div v-if="result.segmentation_results" class="result-section">
      <h3>分割分析结果</h3>
      <div class="segmentation-grid">
        <div><strong>检测到区域：</strong>{{ result.segmentation_results.regions_detected }}</div>
        <div><strong>最大区域面积：</strong>{{ result.segmentation_results.largest_area }}</div>
        <div><strong>总面积：</strong>{{ result.segmentation_results.total_area }}</div>
        <div><strong>区域数量：</strong>{{ result.segmentation_results.region_count }}</div>
      </div>
    </div>

    <div class="result-section">
      <h3>详细分析</h3>
      <p>{{ result.detailed_analysis }}</p>
    </div>

    <div class="result-section">
      <h3>个性化建议</h3>
      <ul class="recommendations">
        <li v-for="rec in result.recommendations" :key="rec">{{ rec }}</li>
      </ul>
    </div>

    <div class="result-section">
      <h3>关键影响因素</h3>
      <table>
        <tr><th>特征</th><th>贡献度</th></tr>
        <tr v-for="(v,k) in result.top_factors" :key="k">
          <td>{{ k }}</td><td>{{ v.toFixed(4) }}</td>
        </tr>
      </table>
    </div>

    <div v-if="result.model_performance" class="result-section">
      <h3>模型性能指标</h3>
      <div class="performance-grid">
        <div><strong>准确率：</strong>{{ fmt(result.model_performance.accuracy) }}</div>
        <div><strong>精确率：</strong>{{ fmt(result.model_performance.precision) }}</div>
        <div><strong>召回率：</strong>{{ fmt(result.model_performance.recall) }}</div>
        <div><strong>F1分数：</strong>{{ fmt(result.model_performance.f1_score) }}</div>
      </div>
    </div>

    <div class="action-buttons">
      <button @click="generateReport">生成报告</button>
      <button @click="analyzeImageOnly" v-if="fileRef" class="secondary">单独分析图像</button>
    </div>
  </div>

  <div v-if="recog" class="card">
    <h2>识别结果</h2>
    <div class="result-grid">
      <div class="result-section">
        <h3>总体</h3>
        <p><strong>肿瘤类型：</strong>{{ recog.tumor_type }}</p>
        <p><strong>良恶性概率：</strong>{{ pct(recog.malignancy_probability) }}</p>
        <p><strong>置信度：</strong>{{ pct(recog.confidence) }}</p>
      </div>
      <div class="result-section">
        <h3>类型分布</h3>
        <div class="segmentation-grid">
          <div v-for="(v,k) in recog.type_distribution" :key="k">
            <strong>{{ k }}：</strong>{{ pct(v) }}
          </div>
        </div>
      </div>
      <div class="result-section">
        <h3>ABCDE</h3>
        <div class="segmentation-grid">
          <div><strong>A：</strong>{{ fmt(recog.abcde?.A?.asymmetry) }}</div>
          <div><strong>B：</strong>{{ fmt(recog.abcde?.B?.border) }}</div>
          <div><strong>C：</strong>{{ fmt(recog.abcde?.C?.color_variation) }}</div>
          <div><strong>D：</strong>{{ fmt(recog.abcde?.D?.diameter_px) }}</div>
          <div><strong>E：</strong>{{ recog.abcde?.E?.evolving }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import api from '../services/api'

const patient = reactive({ name: '', age: '' })
const form = reactive({
  age: 45,
  bmi: 24,
  smoking: false,
  alcohol: false,
  family_history: false,
  symptom_score: 3,
  lab_cea: 3,
  lab_ca125: 20,
})

const fileRef = ref(null)
const result = ref(null)
const recog = ref(null)
const preview = ref('')

function onFile(e){
  fileRef.value = e.target.files?.[0] || null
  if (fileRef.value){
    if (!['image/jpeg','image/png'].includes(fileRef.value.type)){
      alert('仅支持JPG/PNG格式')
      fileRef.value = null
      return
    }
    if (fileRef.value.size > 10 * 1024 * 1024){
      alert('文件大小超过10MB')
      fileRef.value = null
      return
    }
    preview.value = URL.createObjectURL(fileRef.value)
  }
}

function fmt(v){
  return (v ?? 0).toFixed(3)
}

async function assess(){
  const fd = new FormData()
  const payload = { ...form }
  fd.append('payload', JSON.stringify(payload))
  if (fileRef.value) fd.append('image', fileRef.value)
  try {
    const { data } = await api.post('/api/v1/assess', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    result.value = data
    patient.age = String(form.age)
  } catch (err){
    alert('评估失败：' + (err?.message || '未知错误'))
  }
}

async function analyzeImageOnly(){
  if (!fileRef.value) {
    alert('请先选择图像文件')
    return
  }
  try {
    const fd = new FormData()
    fd.append('image', fileRef.value)
    const { data } = await api.post('/api/v1/image/analyze', fd, { 
      headers: { 'Content-Type': 'multipart/form-data' } 
    })
    alert(`图像分析完成：\n状态：${data.status}\n尺寸：${data.dimensions?.join('×') || '未知'}\n特征数量：${data.features_extracted || 0}`)
  } catch (err){
    alert('图像分析失败：' + (err?.response?.data?.detail || err?.message || '未知错误'))
  }
}

async function recognizeImage(){
  if (!fileRef.value){
    alert('请先选择图像文件')
    return
  }
  try {
    const fd = new FormData()
    fd.append('image', fileRef.value)
    const { data } = await api.post('/api/v1/image/recognize', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    recog.value = data
  } catch (err){
    alert('识别失败：' + (err?.response?.data?.detail || err?.message || '未知错误'))
  }
}

async function generateReport(){
  if (!result.value){
    alert('请先完成风险评估')
    return
  }
  try {
    const { data } = await api.post('/api/v1/report', {
      patient: { name: patient.name || '匿名', age: form.age },
      result: result.value,
    })
    const w = window.open('', '_blank')
    w.document.write(data.content)
    w.document.close()
  } catch (err){
    alert('生成报告失败：' + (err?.message || '未知错误'))
  }
}
</script>

<style>
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow);
  backdrop-filter: blur(10px);
  animation: fadeInUp 320ms ease both;
  margin-bottom: 16px;
}

.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; align-items: start; }
label { display: flex; flex-direction: column; gap: 8px; color: var(--text); }

/* 统一所有文本输入框尺寸与间距 */
input:not([type="checkbox"]) {
  background: rgba(18,18,22,0.9);
  border: 1px solid rgba(255,255,255,0.08);
  color: var(--text);
  border-radius: 10px;
  padding: 10px 12px;
  height: 42px; /* 统一高度 */
  width: 100%; /* 统一宽度 */
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  box-sizing: border-box;
  margin: 0; /* 统一外边距 */
}

input[type="file"] { height: auto; padding: 8px 12px; }

/* 深色主题下自定义复选框样式，统一尺寸与对齐 */
input[type="checkbox"] {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border: 2px solid var(--border);
  border-radius: 4px;
  background: rgba(18,18,22,0.9);
  position: relative;
  margin: 2px 0; /* 统一上下间距，与文本居中对齐 */
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}
input[type="checkbox"]:hover { border-color: rgba(255,255,255,0.16); }
input[type="checkbox"]:focus { box-shadow: 0 0 0 3px rgba(212,175,55,0.12); }
input[type="checkbox"]:checked { border-color: var(--gold); background: rgba(212,175,55,0.12); }
input[type="checkbox"]:checked::after {
  content: '';
  position: absolute;
  left: 4px; top: 0px;
  width: 6px; height: 12px;
  border-right: 2px solid var(--gold);
  border-bottom: 2px solid var(--gold);
  transform: rotate(45deg);
}

button {
  background: linear-gradient(135deg, var(--gold), var(--gold-2));
  color: #141416;
  border: none;
  border-radius: 12px;
  padding: 10px 18px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  box-shadow: var(--shadow);
  height: 42px; /* 与输入框统一高度 */
}
button:hover { transform: translateY(-1px); box-shadow: 0 12px 24px rgba(212,175,55,0.28); }
button:active { transform: translateY(0); opacity: 0.95; }

.tag {
  display:inline-block; padding:4px 8px; border-radius:8px;
  background: rgba(212,175,55,0.12);
  color: var(--gold);
  border: 1px solid rgba(212,175,55,0.35);
}

table { width:100%; border-collapse: collapse; margin-top: 12px; }
td, th { border:1px solid rgba(255,255,255,0.08); padding:8px 10px; }
tr:nth-child(even) td { background: rgba(255,255,255,0.02); }

@keyframes fadeInUp { 0% { opacity: 0; transform: translateY(8px);} 100% { opacity: 1; transform: translateY(0);} }

/* 新增样式 */
.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.result-section {
  background: rgba(18,18,22,0.6);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.result-section h3 {
  margin: 0 0 12px 0;
  color: var(--gold);
  font-size: 16px;
  font-weight: 600;
}

.segmentation-grid, .performance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.segmentation-grid div, .performance-grid div {
  background: rgba(255,255,255,0.02);
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.05);
}

.recommendations {
  list-style: none;
  padding: 0;
  margin: 0;
}

.recommendations li {
  background: rgba(212,175,55,0.08);
  border: 1px solid rgba(212,175,55,0.2);
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  color: var(--text);
}

.recommendations li:before {
  content: "💡";
  margin-right: 8px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.action-buttons button.secondary {
  background: rgba(255,255,255,0.1);
  color: var(--text);
  border: 1px solid var(--border);
}

.action-buttons button.secondary:hover {
  background: rgba(255,255,255,0.15);
  transform: translateY(-1px);
}

@media (max-width: 720px){
  .grid { grid-template-columns: 1fr; }
  .result-grid { grid-template-columns: 1fr; }
  .segmentation-grid, .performance-grid { grid-template-columns: 1fr; }
  .action-buttons { flex-direction: column; }
}
</style>