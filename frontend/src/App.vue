<template>
  <div v-if="isAdmin">
    <router-view />
  </div>
  <div v-else class="container">
    <header>
      <h1 style="text-align: center;"><img src="./logo.png" alt="山东理工大学" style="height:53px; vertical-align: middle; margin-right: 16px;">肿瘤数智化筛查系统</h1>
      <p style="text-align: center;">多模态输入 · 个性化风险评估 · 可解释报告</p>
    </header>
    <router-view />
    <footer class="brand-footer">
      <div class="brand">
        <img src="./logo.png" alt="山东理工大学" style="height: 34px; vertical-align: middle; margin-right: 8px;">
        山理工神思妙想队项目
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
  --bg-start: #0b0b0f;
  --bg-end: #111218;
  --surface: rgba(20,20,24,0.7);
  --border: rgba(255,255,255,0.08);
  --gold: #d4af37;
  --gold-2: #b88900;
  --text: #e8e8ea;
  --muted: #9aa0a6;
  --shadow: 0 20px 40px rgba(0,0,0,0.45);
}

* { box-sizing: border-box; }
html, body { height: 100%; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, "Noto Sans", "PingFang SC", "Microsoft Yahei", sans-serif;
  margin: 0;
  color: var(--text);
  background: radial-gradient(1200px 800px at 20% 10%, var(--bg-start), var(--bg-end));
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
}

p { color: var(--muted); margin: 0 0 8px; }

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
</style>