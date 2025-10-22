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
          <input type="file" accept="image/*" @change="onFile" />
        </label>
      </div>

      <button type="submit">评估风险</button>
    </form>
  </div>

  <div v-if="result" class="card">
    <h2>评估结果</h2>
    <p><strong>风险分值：</strong>{{ fmt(result.risk_score) }}</p>
    <p><strong>风险等级：</strong><span class="tag">{{ result.risk_level }}</span></p>
    <p><strong>建议：</strong>{{ result.recommendations }}</p>
    <h3>关键影响因素</h3>
    <table>
      <tr><th>特征</th><th>贡献度</th></tr>
      <tr v-for="(v,k) in result.top_factors" :key="k">
        <td>{{ k }}</td><td>{{ v.toFixed(4) }}</td>
      </tr>
    </table>

    <button @click="generateReport">生成报告</button>
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

function onFile(e){
  fileRef.value = e.target.files?.[0] || null
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

@media (max-width: 720px){
  .grid { grid-template-columns: 1fr; }
}
</style>