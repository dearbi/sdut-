<template>
  <div class="card">
    <h2>排班管理</h2>
    <form class="grid" @submit.prevent="createSchedule">
      <label>资源ID<input v-model.number="form.resource_id" required /></label>
      <label>患者ID<input v-model.number="form.patient_id" /></label>
      <label>开始时间<input type="datetime-local" v-model="form.start_time" required /></label>
      <label>结束时间<input type="datetime-local" v-model="form.end_time" required /></label>
      <button type="submit">创建排班</button>
    </form>
    <table style="margin-top:12px;">
      <tr><th>ID</th><th>资源ID</th><th>患者ID</th><th>开始</th><th>结束</th><th>状态</th></tr>
      <tr v-for="s in schedules" :key="s.id">
        <td>{{ s.id }}</td>
        <td>{{ s.resource_id }}</td>
        <td>{{ s.patient_id || '-' }}</td>
        <td>{{ formatDT(s.start_time) }}</td>
        <td>{{ formatDT(s.end_time) }}</td>
        <td>{{ s.status }}</td>
      </tr>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const schedules = ref([])
const form = ref({ resource_id: null, patient_id: null, start_time: '', end_time: '' })

function toISO(dt){
  // v-model returns 'YYYY-MM-DDTHH:mm'; convert to ISO string
  return new Date(dt).toISOString()
}

function formatDT(dt){
  try { return new Date(dt).toLocaleString() } catch { return dt }
}

async function fetchSchedules(){
  const { data } = await api.get('/admin/schedules')
  schedules.value = data
}

async function createSchedule(){
  try {
    const payload = { resource_id: form.value.resource_id, patient_id: form.value.patient_id || null,
      start_time: toISO(form.value.start_time), end_time: toISO(form.value.end_time) }
    await api.post('/admin/schedules', payload)
    form.value = { resource_id: null, patient_id: null, start_time: '', end_time: '' }
    await fetchSchedules()
  } catch (err){
    alert('创建排班失败：' + (err?.response?.data?.detail || err?.message || '未知错误'))
  }
}

onMounted(fetchSchedules)
</script>

<style>
.grid { display:grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
label { display:flex; flex-direction:column; gap:6px; }
input { background: rgba(18,18,22,0.9); border: 1px solid rgba(255,255,255,0.08); color: var(--text); border-radius: 10px; padding: 10px 12px; }
button { background: linear-gradient(135deg, var(--gold), var(--gold-2)); color: #141416; border: none; border-radius: 12px; padding: 10px 18px; font-weight: 600; cursor: pointer; }
@media (max-width: 900px){ .grid { grid-template-columns: 1fr; } }
</style>