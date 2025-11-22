# 黑金主题样式规范指南

## 概述
本指南定义了肿瘤筛查系统的黑金主题视觉规范，确保整个应用保持一致的设计语言和用户体验。

## 色彩系统

### 主色调
- **背景色**: `#121212` - 深黑色背景，营造专业医疗氛围
- **主金色**: `#FFD700` - 纯金色，用于主要交互元素
- **辅助金色**: `#FFA500` - 橙金色，用于悬停状态
- **深金色**: `#B8860B` - 深金棕色，用于激活状态

### 文字颜色
- **主要文字**: `#FFFFFF` - 纯白色，确保最佳可读性
- **次要文字**: `#CCCCCC` - 浅灰色，用于辅助信息
- **提示文字**: `#999999` - 中灰色，用于占位符和说明
- **禁用文字**: `#666666` - 深灰色，用于禁用状态

### 状态颜色
- **成功**: `#00FF00` - 亮绿色，用于成功状态
- **警告**: `#FFAA00` - 橙黄色，用于警告状态
- **错误**: `#FF4444` - 亮红色，用于错误状态
- **信息**: `#4488FF` - 蓝色，用于信息提示

## 组件样式规范

### 按钮 (Button)
```css
/* 主要按钮 */
.el-button--primary {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  border: none;
  color: #121212;
  font-weight: 600;
  transition: all 0.3s ease;
}

.el-button--primary:hover {
  background: linear-gradient(135deg, #FFA500 0%, #FFD700 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(255, 215, 0, 0.4);
}
```

### 输入框 (Input)
```css
/* 输入框样式 */
.el-input__wrapper {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.el-input__wrapper:hover {
  border-color: rgba(255, 215, 0, 0.6);
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.2);
}

.el-input__wrapper.is-focus {
  border-color: #FFD700;
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
}
```

### 卡片 (Card)
```css
/* 卡片样式 */
.el-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 215, 0, 0.2);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.el-card:hover {
  border-color: rgba(255, 215, 0, 0.4);
  box-shadow: 0 8px 32px rgba(255, 215, 0, 0.15);
  transform: translateY(-2px);
}
```

### 表格 (Table)
```css
/* 表格样式 */
.el-table {
  background: transparent;
  color: #FFFFFF;
}

.el-table th {
  background: rgba(255, 215, 0, 0.1);
  color: #FFD700;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 215, 0, 0.3);
}

.el-table tr {
  background: rgba(255, 255, 255, 0.02);
  transition: background 0.3s ease;
}

.el-table tr:hover {
  background: rgba(255, 215, 0, 0.05);
}
```

### 标签 (Tag)
```css
/* 标签样式 */
.el-tag {
  background: rgba(255, 215, 0, 0.15);
  border: 1px solid rgba(255, 215, 0, 0.4);
  color: #FFD700;
  border-radius: 20px;
}

.el-tag--success {
  background: rgba(0, 255, 0, 0.15);
  border-color: rgba(0, 255, 0, 0.4);
  color: #00FF00;
}

.el-tag--danger {
  background: rgba(255, 68, 68, 0.15);
  border-color: rgba(255, 68, 68, 0.4);
  color: #FF4444;
}
```

## 动画效果

### 页面过渡
```css
/* 页面切换淡入效果 */
.page-transition {
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### 按钮波纹效果
```css
/* 波纹动画 */
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
  background: rgba(255, 215, 0, 0.6);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.ripple:active::before {
  width: 300px;
  height: 300px;
}
```

### 悬停动效
```css
/* 悬停上浮效果 */
.hover-lift {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.hover-lift:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(255, 215, 0, 0.2);
}
```

## 响应式设计

### 断点设置
```css
/* 响应式断点 */
@media (max-width: 768px) {
  /* 移动端样式 */
  .container {
    padding: 0 16px;
  }
  
  .el-card {
    margin: 8px 0;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  /* 平板端样式 */
  .container {
    padding: 0 24px;
  }
}

@media (min-width: 1025px) {
  /* 桌面端样式 */
  .container {
    padding: 0 32px;
  }
}
```

## 可访问性

### 对比度标准
- 所有文字与背景对比度 ≥ 4.5:1 (符合WCAG 2.1 AA标准)
- 交互元素对比度 ≥ 3:1
- 金色元素在黑色背景上对比度 ≥ 12:1

### 焦点指示器
```css
/* 焦点样式 */
:focus-visible {
  outline: 2px solid #FFD700;
  outline-offset: 2px;
}

/* 键盘导航高亮 */
.el-button:focus-visible,
.el-input__wrapper:focus-visible {
  box-shadow: 0 0 0 3px rgba(255, 215, 0, 0.3);
}
```

## 使用指南

### 快速开始
1. 在组件中使用CSS变量确保一致性
2. 遵循色彩对比度标准
3. 添加适当的过渡动画
4. 测试响应式布局

### 最佳实践
- 使用金色渐变增强视觉层次
- 保持足够的留白空间
- 统一圆角半径 (8px, 12px, 16px)
- 一致的阴影深度和方向

### 性能优化
- 使用CSS变量减少重复代码
- 合理使用硬件加速 (transform, opacity)
- 避免过度使用box-shadow
- 优化动画性能

## 更新日志

### v1.0.0 (2024-11-22)
- 初始黑金主题规范
- 完整的组件样式定义
- 动画效果指南
- 响应式设计规范
- 可访问性标准

---

*本规范将持续更新以适应新的设计需求和技术发展。*