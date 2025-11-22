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
.stat { background: var(--surface); border:1px solid var(--border); border-radius: 12px; padding: 12px; backdrop-filter: blur(10px); transition: all 0.3s ease; }
.stat:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(255,215,0,0.15); }
.label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.value { font-size: 24px; font-weight: 700; background: var(--gold-gradient); -webkit-background-clip:text; background-clip:text; color:transparent; }

/* 风险分布样式 */
.card ul { list-style: none; padding: 0; margin: 0; }
.card li { 
  background: var(--gold-hover); 
  border: 1px solid var(--border); 
  border-radius: 8px; 
  padding: 8px 12px; 
  margin-bottom: 8px; 
  color: var(--text);
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
}
.card li:hover { 
  border-color: var(--gold);
  background: rgba(255,215,0,0.15);
}

@media (max-width: 900px){ 
  .grid { grid-template-columns: repeat(2, 1fr); } 
}
@media (max-width: 480px){ 
  .grid { grid-template-columns: 1fr; } 
  .stat { padding: 16px; }
  .value { font-size: 20px; }
}
</style>