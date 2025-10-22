<template>
  <div class="monitor-container">
    <div class="card">
      <h2>🔍 系统监控面板</h2>
      <p class="subtitle">实时监控AI模型性能和系统状态</p>
    </div>

    <!-- 系统状态 -->
    <div class="card">
      <h3>📊 系统状态</h3>
      <div v-if="systemStatus" class="status-grid">
        <div class="status-item">
          <div class="status-label">系统状态</div>
          <div class="status-value" :class="systemStatus.status === 'success' ? 'success' : 'error'">
            {{ systemStatus.status === 'success' ? '正常' : '异常' }}
          </div>
        </div>
        <div class="status-item">
          <div class="status-label">已加载模型</div>
          <div class="status-value">{{ systemStatus.data?.models?.models_loaded || 0 }}</div>
        </div>
        <div class="status-item">
          <div class="status-label">处理器状态</div>
          <div class="status-value success">{{ systemStatus.data?.processor_status || '未知' }}</div>
        </div>
        <div class="status-item">
          <div class="status-label">目录状态</div>
          <div class="status-value success">{{ Object.keys(systemStatus.data?.directories || {}).length }} 个目录</div>
        </div>
      </div>
    </div>

    <!-- 模型性能 -->
    <div class="card">
      <h3>🤖 AI模型性能</h3>
      <div v-if="modelPerformance" class="models-grid">
        <div v-for="(model, name) in modelPerformance.data?.metrics" :key="name" class="model-card">
          <h4>{{ getModelDisplayName(name) }}</h4>
          <div class="metric-item">
            <span>平均CV得分:</span>
            <span class="metric-value">{{ (model.cv_mean * 100).toFixed(2) }}%</span>
          </div>
          <div class="metric-item">
            <span>标准差:</span>
            <span class="metric-value">{{ (model.cv_std * 100).toFixed(3) }}%</span>
          </div>
          <div class="cv-scores">
            <div class="cv-label">交叉验证得分:</div>
            <div class="scores-list">
              <span v-for="score in model.cv_scores" :key="score" class="score-badge">
                {{ (score * 100).toFixed(1) }}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 目录信息 -->
    <div class="card">
      <h3>📁 存储目录状态</h3>
      <div v-if="systemStatus?.data?.directories" class="directories-grid">
        <div v-for="(dir, name) in systemStatus.data.directories" :key="name" class="directory-item">
          <div class="dir-name">{{ getDirDisplayName(name) }}</div>
          <div class="dir-info">
            <div class="dir-status" :class="dir.exists ? 'success' : 'error'">
              {{ dir.exists ? '✓ 存在' : '✗ 不存在' }}
            </div>
            <div class="file-count">{{ dir.file_count }} 个文件</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="card">
      <h3>🛠️ 系统操作</h3>
      <div class="action-buttons">
        <button @click="refreshData" :disabled="loading">
          {{ loading ? '刷新中...' : '🔄 刷新数据' }}
        </button>
        <button @click="retrainModels" :disabled="retraining" class="secondary">
          {{ retraining ? '重训练中...' : '🔧 重新训练模型' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const systemStatus = ref(null)
const modelPerformance = ref(null)
const loading = ref(false)
const retraining = ref(false)

function getModelDisplayName(name) {
  const names = {
    'risk_assessment': '风险评估模型',
    'feature_analysis': '特征分析模型',
    'advanced_prediction': '高级预测模型'
  }
  return names[name] || name
}

function getDirDisplayName(name) {
  const names = {
    'uploads': '上传目录',
    'tmp_ct': 'CT临时目录',
    'tmp_image': '图像临时目录',
    'tmp_mask': '掩码临时目录',
    'tmp_draw': '绘制临时目录',
    'reports': '报告目录',
    'models': '模型目录'
  }
  return names[name] || name
}

async function fetchSystemStatus() {
  try {
    const { data } = await api.get('/api/v1/system/status')
    systemStatus.value = data
  } catch (err) {
    console.error('获取系统状态失败:', err)
  }
}

async function fetchModelPerformance() {
  try {
    const { data } = await api.get('/api/v1/models/performance')
    modelPerformance.value = data
  } catch (err) {
    console.error('获取模型性能失败:', err)
  }
}

async function refreshData() {
  loading.value = true
  try {
    await Promise.all([fetchSystemStatus(), fetchModelPerformance()])
  } finally {
    loading.value = false
  }
}

async function retrainModels() {
  if (!confirm('确定要重新训练所有AI模型吗？这可能需要几分钟时间。')) {
    return
  }
  
  retraining.value = true
  try {
    const { data } = await api.post('/api/v1/models/retrain')
    alert('模型重训练完成！\n' + data.message)
    await refreshData()
  } catch (err) {
    alert('模型重训练失败：' + (err?.response?.data?.detail || err?.message || '未知错误'))
  } finally {
    retraining.value = false
  }
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.monitor-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.subtitle {
  color: var(--muted);
  margin: 0;
  font-size: 14px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.status-item {
  background: rgba(18,18,22,0.6);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}

.status-label {
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 8px;
}

.status-value {
  font-size: 18px;
  font-weight: 600;
}

.status-value.success {
  color: #4ade80;
}

.status-value.error {
  color: #ef4444;
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.model-card {
  background: rgba(18,18,22,0.6);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
}

.model-card h4 {
  margin: 0 0 16px 0;
  color: var(--gold);
  font-size: 16px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 4px 0;
}

.metric-value {
  font-weight: 600;
  color: var(--gold);
}

.cv-scores {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.cv-label {
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 8px;
}

.scores-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.score-badge {
  background: rgba(212,175,55,0.12);
  color: var(--gold);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid rgba(212,175,55,0.3);
}

.directories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.directory-item {
  background: rgba(18,18,22,0.6);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px;
}

.dir-name {
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text);
}

.dir-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dir-status.success {
  color: #4ade80;
}

.dir-status.error {
  color: #ef4444;
}

.file-count {
  color: var(--muted);
  font-size: 12px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-buttons button {
  background: linear-gradient(135deg, var(--gold), var(--gold-2));
  color: #141416;
  border: none;
  border-radius: 10px;
  padding: 12px 20px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-buttons button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-buttons button.secondary {
  background: rgba(255,255,255,0.1);
  color: var(--text);
  border: 1px solid var(--border);
}

.action-buttons button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(212,175,55,0.3);
}

@media (max-width: 768px) {
  .status-grid, .models-grid, .directories-grid {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-direction: column;
  }
}
</style>