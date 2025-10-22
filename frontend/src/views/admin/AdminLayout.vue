<template>
  <div class="admin">
    <aside class="sidebar">
      <div class="brand" style="text-align:center;">山理工奇思妙想队 <br>
        肿瘤检测后台</div>
      <nav>
        <router-link to="/admin/dashboard" class="nav">仪表盘</router-link>
        <router-link to="/admin/users" class="nav">用户管理</router-link>
        <router-link to="/admin/patients" class="nav">患者管理</router-link>
        <router-link to="/admin/resources" class="nav">资源管理</router-link>
        <router-link to="/admin/schedules" class="nav">排班管理</router-link>
      </nav>
      <div class="sidebar-footer">
        <button class="logout" @click="logout">退出登录</button>
      </div>
    </aside>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
function logout(){
  localStorage.removeItem('token')
  router.push('/admin/login')
}
</script>

<style>
.admin { display: grid; grid-template-columns: 240px 1fr; min-height: 100vh; }
.sidebar {
  background: rgba(20,20,24,0.6);
  border-right: 1px solid var(--border);
  backdrop-filter: blur(8px);
  padding: 16px;
}
.brand { font-weight: 700; margin-bottom: 16px; background: linear-gradient(135deg, var(--gold), var(--gold-2)); -webkit-background-clip:text; background-clip:text; color:transparent; }
.nav { display:block; padding: 10px 12px; border-radius: 10px; color: var(--text); text-decoration:none; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.06); }
.nav.router-link-active { border-color: var(--gold); color: var(--gold); }
.sidebar-footer { margin-top: 16px; }
.logout { width: 100%; background: linear-gradient(135deg, var(--gold), var(--gold-2)); color: #141416; border:none; border-radius: 10px; padding: 10px; font-weight: 600; cursor: pointer; }
.content { padding: 16px; }

@media (max-width: 900px){ .admin { grid-template-columns: 1fr; } .sidebar { grid-row: 2; } }
</style>