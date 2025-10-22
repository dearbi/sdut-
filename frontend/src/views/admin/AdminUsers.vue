<template>
  <div class="card">
    <h2>用户管理</h2>
    <form class="row" @submit.prevent="createUser">
      <input v-model="newUser.username" placeholder="用户名" required />
      <input type="password" v-model="newUser.password" placeholder="密码" required />
      <input v-model="newUser.email" placeholder="邮箱（可选）" />
      <button type="submit">创建用户</button>
    </form>
    <table style="margin-top:12px;">
      <tr><th>ID</th><th>用户名</th><th>邮箱</th><th>角色</th></tr>
      <tr v-for="u in users" :key="u.id">
        <td>{{ u.id }}</td>
        <td>{{ u.username }}</td>
        <td>{{ u.email || '-' }}</td>
        <td>{{ (u.roles||[]).join(', ') }}</td>
      </tr>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const users = ref([])
const newUser = ref({ username: '', password: '', email: '' })

async function fetchUsers(){
  const { data } = await api.get('/admin/users')
  users.value = data
}

async function createUser(){
  try {
    await api.post('/admin/users', newUser.value)
    newUser.value = { username: '', password: '', email: '' }
    await fetchUsers()
  } catch (err){
    alert('创建用户失败：' + (err?.response?.data?.detail || err?.message || '未知错误'))
  }
}

onMounted(fetchUsers)
</script>

<style>
.row { display:flex; gap:8px; align-items:center; }
input { flex:1; background: rgba(18,18,22,0.9); border: 1px solid rgba(255,255,255,0.08); color: var(--text); border-radius: 10px; padding: 10px 12px; }
button { background: linear-gradient(135deg, var(--gold), var(--gold-2)); color: #141416; border: none; border-radius: 12px; padding: 10px 18px; font-weight: 600; cursor: pointer; }
</style>