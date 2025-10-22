<template>
  <div class="card">
    <h2>患者管理</h2>
    <form class="grid" @submit.prevent="createPatient">
      <label>姓名<input v-model="form.name" required /></label>
      <label>年龄<input type="number" v-model.number="form.age" min="0" max="120" /></label>
      <label>性别<input v-model="form.sex" placeholder="M/F/其他" /></label>
      <label>联系方式<input v-model="form.contact" /></label>
      <label>风险等级<input v-model="form.risk_level" placeholder="低/中/高" /></label>
      <label>备注<input v-model="form.notes" /></label>
      <button type="submit">新增患者</button>
    </form>
    <table style="margin-top:12px;">
      <tr><th>ID</th><th>姓名</th><th>年龄</th><th>性别</th><th>风险</th><th>操作</th></tr>
      <tr v-for="p in patients" :key="p.id">
        <td>{{ p.id }}</td><td>{{ p.name }}</td><td>{{ p.age || '-' }}</td><td>{{ p.sex || '-' }}</td><td>{{ p.risk_level || '-' }}</td>
        <td><button @click="remove(p.id)" style="background:#b33;color:white;border:none;border-radius:8px;padding:6px 10px;">删除</button></td>
      </tr>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const patients = ref([])
const form = ref({ name: '', age: null, sex: '', contact: '', risk_level: '', notes: '' })

async function fetchPatients(){
  const { data } = await api.get('/admin/patients')
  patients.value = data
}

async function createPatient(){
  try {
    await api.post('/admin/patients', form.value)
    form.value = { name: '', age: null, sex: '', contact: '', risk_level: '', notes: '' }
    await fetchPatients()
  } catch (err){
    alert('新增患者失败：' + (err?.response?.data?.detail || err?.message || '未知错误'))
  }
}

async function remove(id){
  try {
    await api.delete(`/admin/patients/${id}`)
    await fetchPatients()
  } catch (err){
    alert('删除失败：' + (err?.response?.data?.detail || err?.message || '未知错误'))
  }
}

onMounted(fetchPatients)
</script>

<style>
.grid { display:grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
label { display:flex; flex-direction:column; gap:6px; }
input { background: rgba(18,18,22,0.9); border: 1px solid rgba(255,255,255,0.08); color: var(--text); border-radius: 10px; padding: 10px 12px; }
button { background: linear-gradient(135deg, var(--gold), var(--gold-2)); color: #141416; border: none; border-radius: 12px; padding: 10px 18px; font-weight: 600; cursor: pointer; }
@media (max-width: 900px){ .grid { grid-template-columns: 1fr; } }
</style>