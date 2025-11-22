<template>
  <div v-if="isAdmin">
    <router-view />
  </div>
  <div v-else class="container">
    <header>
      <h1 style="text-align: center;">肿瘤数智化筛查系统</h1>
      <p style="text-align: center;">多模态输入 · 个性化风险评估 · 可解释报告</p>
      <nav class="main-nav">
        <router-link to="/recognition" class="nav-link">🔍 识别</router-link>
        <router-link to="/" class="nav-link">🏠 筛查评估</router-link>
        <router-link to="/batch-assessment" class="nav-link">📋 批量评估</router-link>
        <router-link to="/monitor" class="nav-link">📊 系统监控</router-link>
        <router-link to="/admin" class="nav-link">⚙️ 管理后台</router-link>
      </nav>
    </header>
    <router-view />
    <footer class="brand-footer">
      <div class="brand">
        神思杯-神思妙想队项目
      </div>
      <small>声明：本原型仅用于技术演示，不替代临床诊断。</small>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const isAdmin = computed(() => route.path.startsWith('/admin'))
</script>

<style>
:root {
  --bg-start: #121212;
  --bg-end: #1a1a1a;
  --surface: rgba(42,42,42,0.7);
  --border: rgba(255,215,0,0.25);
  --gold: #FFD700;
  --gold-2: #F0E68C;
  --text: #E0E0E0;
  --muted: #B0B0B0;
  --shadow: 0 20px 40px rgba(0,0,0,0.6);
  --gold-gradient: linear-gradient(135deg, var(--gold), var(--gold-2));
  --gold-ripple: rgba(255,215,0,0.3);
  --gold-focus: rgba(255,215,0,0.4);
  --gold-hover: rgba(255,215,0,0.1);
}

* { box-sizing: border-box; }
html, body { height: 100%; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, "Noto Sans", "PingFang SC", "Microsoft Yahei", sans-serif;
  margin: 0;
  color: var(--text);
  background: radial-gradient(1200px 800px at 20% 10%, var(--bg-start), var(--bg-end));
  line-height: 1.5;
}

.container {
  max-width: 1080px;
  margin: 0 auto;
  padding: 24px;
}

header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

h1 {
  margin: 0 0 8px 0;
  letter-spacing: 0.5px;
  font-weight: 600;
  background: var(--gold-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

p { color: var(--muted); margin: 0 0 8px; line-height: 1.5; }

.brand-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--border);
  margin-top: 24px;
  padding-top: 12px;
  color: var(--muted);
}

.brand {
  font-weight: 600;
  background: linear-gradient(135deg, var(--gold), var(--gold-2));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.main-nav {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border);

}

.nav-link {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 8px;
  color: var(--muted);
  text-decoration: none;
  border: 1px solid var(--border);
  transition: all 0.3s ease;
  font-size: 14px;
  font-weight: 500;
  position: relative;
  overflow: hidden;
}

.nav-link:hover {
  color: var(--text);
  border-color: var(--gold);
  background: var(--gold-hover);
}

.nav-link.router-link-active {
  color: var(--gold);
  border-color: var(--gold);
  background: rgba(255,215,0,0.08);
  box-shadow: 0 0 12px var(--gold-ripple);
}

@media (max-width: 600px) {
  .main-nav {
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
}
/* 页面过渡动画 */
.page-enter-active, .page-leave-active {
  transition: opacity 0.3s ease;
}
.page-enter-from, .page-leave-to {
  opacity: 0;
}

/* 按钮波纹效果 */
.ripple {
  position: relative;
  overflow: hidden;
}
.ripple::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: var(--gold-ripple);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}
.ripple:active::before {
  width: 300px;
  height: 300px;
}

/* 金色粒子动画 */
@keyframes gold-particle {
  0% { transform: scale(0); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}
.gold-particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: var(--gold);
  border-radius: 50%;
  animation: gold-particle 0.6s ease-out;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .container {
    padding: 16px;
  }
  
  h1 {
    font-size: 24px;
  }
  
  .main-nav {
    gap: 12px;
  }
  
  .nav-link {
    padding: 10px 14px;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .main-nav {
    flex-direction: column;
    gap: 8px;
  }
  
  .nav-link {
    width: 100%;
    text-align: center;
  }
}
</style>