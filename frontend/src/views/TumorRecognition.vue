<template>
  <div class="page">
    <div class="header">
      <h2>肿瘤照片识别</h2>
      <el-button type="primary" @click="syncDatasets" plain>同步数据集</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <div class="upload-section">
            <el-upload
              drag
              :auto-upload="false"
              :on-change="onUploadChange"
              :show-file-list="false"
              accept=".jpg,.jpeg,.png"
            >
              <i class="el-icon--upload"></i>
              <div class="el-upload__text">拖拽或点击上传 JPG/PNG（≤10MB）</div>
            </el-upload>
            <div class="controls">
              <el-button :disabled="!file" :type="'primary'" class="primary-med" @click="recognize">识别</el-button>
              <el-button :disabled="!file" @click="rotate">旋转</el-button>
              <span class="scale-label">缩放</span>
              <el-slider v-model="scale" :min="0.5" :max="2" :step="0.1" style="width:200px" />
            </div>
          </div>
          <div v-if="previewUrl" class="preview">
            <div class="canvas-wrap" :style="wrapStyle">
              <img :src="previewUrl" :style="imgStyle" />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <el-steps :active="step" finish-status="success" align-center>
            <el-step title="上传中" />
            <el-step title="处理中" />
            <el-step title="分析完成" />
          </el-steps>

          <el-collapse v-if="result" v-model="activePanels" class="result-panels">
            <el-collapse-item name="summary" title="识别总览">
              <div class="summary">
                <div><b>肿瘤类型：</b>{{ result.tumor_type }}</div>
                <div><b>良恶性概率：</b>{{ pct(result.malignancy_probability) }}</div>
                <div><b>置信度：</b>{{ pct(result.confidence) }}</div>
              </div>
            </el-collapse-item>
            <el-collapse-item name="distribution" title="类型分布">
              <div class="grid">
                <div v-for="(p,k) in result.type_distribution" :key="k" class="pill">
                  <span>{{ k }}</span>
                  <span>{{ pct(p) }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item name="abcde" title="ABCDE特征描述">
              <ul class="abcde">
                <li><b>A</b> 不对称：{{ fmt(result.abcde.A.asymmetry) }}</li>
                <li><b>B</b> 边界规则性：{{ fmt(result.abcde.B.border) }}</li>
                <li><b>C</b> 颜色变化：{{ fmt(result.abcde.C.color_variation) }}</li>
                <li><b>D</b> 直径像素：{{ fmt(result.abcde.D.diameter_px) }}</li>
                <li><b>E</b> 演变：{{ result.abcde.E.evolving }}</li>
              </ul>
            </el-collapse-item>
            <el-collapse-item v-if="result.s3" name="storage" title="存储信息">
              <div><b>S3 URL：</b><a :href="result.s3.url" target="_blank">{{ result.s3.url }}</a></div>
            </el-collapse-item>
          </el-collapse>

          <div v-else class="placeholder">上传图片以查看识别结果</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../services/api'

const file = ref(null)
const previewUrl = ref('')
const scale = ref(1)
const rotation = ref(0)
const step = ref(0)
const result = ref(null)
const activePanels = ref(['summary'])

function onUploadChange(fileObj){
  const f = fileObj?.raw || fileObj
  if (!f) return
  if (!['image/jpeg','image/png'].includes(f.type)){
    ElMessage.error('仅支持JPG/PNG格式')
    return
  }
  if (f.size > 10 * 1024 * 1024){
    ElMessage.error('文件大小超过10MB')
    return
  }
  file.value = f
  previewUrl.value = URL.createObjectURL(f)
}

function rotate(){ rotation.value = (rotation.value + 90) % 360 }

const imgStyle = computed(() => ({
  transform: `scale(${scale.value}) rotate(${rotation.value}deg)`,
}))

const wrapStyle = computed(() => ({
  background: '#0f172a',
  border: '1px solid #1f2937',
  borderRadius: '12px',
  padding: '12px',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '320px'
}))

function pct(v){ return `${Math.round((v||0)*100)}%` }
function fmt(v){ return (v ?? 0).toFixed(3) }

async function recognize(){
  if (!file.value){ ElMessage.error('请先上传图片'); return }
  step.value = 1
  const fd = new FormData()
  fd.append('image', file.value)
  try{
    step.value = 2
    const { data } = await api.post('/api/v1/image/recognize', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    result.value = data
    activePanels.value = ['summary','distribution','abcde']
    step.value = 3
  }catch(err){
    ElMessage.error(err?.response?.data?.detail || err?.message || '识别失败')
    step.value = 0
  }
}

async function syncDatasets(){
  try{
    const { data } = await api.post('/api/v1/datasets/sync')
    ElMessage.success(`同步完成：${data?.data?.categories?.length || 0} 类目`)
  }catch(err){
    ElMessage.error('数据集同步失败')
  }
}
</script>

<style>
.page { padding: 12px }
.header { display:flex; justify-content: space-between; align-items: center; margin-bottom: 12px }
.primary-med { background: #1f6feb; border-color: #1f6feb }
.upload-section { display:flex; flex-direction: column; gap: 12px }
.controls { display:flex; align-items: center; gap: 12px }
.scale-label { color: #94a3b8 }
.preview { margin-top: 12px }
.result-panels { margin-top: 12px }
.grid { display:grid; grid-template-columns: repeat(2, 1fr); gap: 8px }
.pill { display:flex; justify-content: space-between; padding:8px 12px; border:1px solid #334155; border-radius: 8px }
.abcde { list-style:none; padding:0; margin:0 }
.abcde li { margin-bottom:8px }
.placeholder { color:#94a3b8; margin-top: 12px }
</style>