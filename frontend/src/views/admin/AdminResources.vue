<template>
  <div class="card">
    <h2>资源管理</h2>
    <form class="row" @submit.prevent="createResource">
      <input v-model="form.name" placeholder="资源名称" required />
      <input v-model="form.type" placeholder="类型（设备/房间等）" />
      <input v-model.number="form.department_id" placeholder="科室ID（可选）" />
      <button type="submit">新增资源</button>
    </form>
    <table style="margin-top:12px;">
      <thead>
        <tr><th>ID</th><th>名称</th><th>类型</th><th>科室</th><th>状态</th></tr>
      </thead>
      <tbody>
        <tr v-for="r in resources" :key="r.id">
          <td>{{ r.id }}</td>
          <td>{{ r.name }}</td>
          <td>{{ r.type || '-' }}</td>
          <td>{{ r.department_id || '-' }}</td>
          <td>{{ r.status }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const resources = ref([])
const form = ref({ name: '', type: '', department_id: null })

async function fetchResources(){
  const { data } = await api.get('/admin/resources')
  resources.value = data
}

async function createResource(){
  try {
    await api.post('/admin/resources', form.value)
    form.value = { name: '', type: '', department_id: null }
    await fetchResources()
  } catch (err){
    alert('新增资源失败：' + (err?.response?.data?.detail || err?.message || '未知错误'))
  }
}

onMounted(fetchResources)
</script>

<style>
.row { display:flex; gap:8px; align-items:center; }
input { flex:1; background: rgba(18,18,22,0.9); border: 1px solid rgba(255,255,255,0.08); color: var(--text); border-radius: 10px; padding: 10px 12px; }
button { background: linear-gradient(135deg, var(--gold), var(--gold-2)); color: #141416; border: none; border-radius: 12px; padding: 10px 18px; font-weight: 600; cursor: pointer; }
</style>