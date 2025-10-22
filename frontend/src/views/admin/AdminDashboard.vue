<template>
  <div class="card">
    <h2>仪表盘</h2>
    <div class="grid">
      <div class="stat">
        <div class="label">用户</div>
        <div class="value">{{ metrics.users }}</div>
      </div>
      <div class="stat">
        <div class="label">患者</div>
        <div class="value">{{ metrics.patients }}</div>
      </div>
      <div class="stat">
        <div class="label">资源</div>
        <div class="value">{{ metrics.resources }}</div>
      </div>
      <div class="stat">
        <div class="label">排班</div>
        <div class="value">{{ metrics.schedules }}</div>
      </div>
    </div>
    <div class="card" style="margin-top:16px;">
      <h3>风险分布</h3>
      <ul>
        <li v-for="(v,k) in metrics.risk_distribution" :key="k">{{ k }}：{{ v }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import api from '../../services/api'

const metrics = reactive({ users: 0, patients: 0, resources: 0, schedules: 0, risk_distribution: {} })

onMounted(async () => {
  try {
    const { data } = await api.get('/admin/dashboard/metrics')
    Object.assign(metrics, data)
  } catch (err){
    alert('获取仪表盘数据失败：' + (err?.message || '未知错误'))
  }
})
</script>

<style>
.grid { display:grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.stat { background: rgba(18,18,22,0.9); border:1px solid var(--border); border-radius: 12px; padding: 12px; }
.label { color: var(--muted); }
.value { font-size: 24px; font-weight: 700; background: linear-gradient(135deg, var(--gold), var(--gold-2)); -webkit-background-clip:text; background-clip:text; color:transparent; }
@media (max-width: 900px){ .grid { grid-template-columns: repeat(2, 1fr); } }
</style>