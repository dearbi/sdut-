<template>
  <div class="card login">
    <h2>后台登录</h2>
    <form @submit.prevent="onSubmit">
      <label>用户名<input v-model="username" required /></label>
      <label>密码<input type="password" v-model="password" required /></label>
      <button type="submit">登录</button>
    </form>
    <p class="hint">首次使用可用管理员账号：admin / 123456</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../services/api'

const router = useRouter()
const username = ref('admin')
const password = ref('123456')

async function onSubmit(){
  try {
    const { data } = await api.post('/admin/auth/login', { username: username.value, password: password.value })
    localStorage.setItem('token', data.access_token)
    router.push('/admin/dashboard')
  } catch (err){
    alert('登录失败：' + (err?.response?.data?.detail || err?.message || '未知错误'))
  }
}
</script>

<style>
.login { max-width: 460px; margin: 0 auto; }
label { display:flex; flex-direction: column; gap:6px; margin-bottom: 12px; }
input { background: rgba(18,18,22,0.9); border: 1px solid rgba(255,255,255,0.08); color: var(--text); border-radius: 10px; padding: 10px 12px; }
button { background: linear-gradient(135deg, var(--gold), var(--gold-2)); color: #141416; border: none; border-radius: 12px; padding: 10px 18px; font-weight: 600; cursor: pointer; }
.hint { color: var(--muted); font-size: 12px; margin-top: 8px; }
</style>