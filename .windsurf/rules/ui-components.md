---
description: 前端微组件设计规范 — 所有 UI 原子组件必须遵循冰蓝绿主题
---

# 前端微组件设计规范 (UI Components)

所有前端 UI 原子组件（表单控件、交互元素、反馈组件）必须严格遵循冰蓝绿主题体系，禁止使用浏览器默认样式或 Arco Design 原始主题样式。

## 核心原则

- **统一视觉语言**：所有微组件必须与 `glass-card`、`btn-primary`、`input-field` 同一视觉体系。
- **禁止浏览器默认样式**：原生 `<select>`、`<checkbox>`、`<radio>` 等必须自定义样式或用组件封装。
- **颜色仅从色板取**：禁止使用 Tailwind 内置色（如 `gray-700`、`blue-500`），必须使用项目色板值。
- **圆角统一 12px**：所有表单控件 `border-radius: 12px`，小型控件可用 `8px`，pill 形使用 `999px`。

## 表单控件

### Select 下拉框

原生 `<select>` 存在浏览器默认下拉箭头和选项列表样式无法自定义的问题。必须做以下处理：

```css
/* 基础样式 — 与 input-field 一致 */
select.input-field {
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,..."); /* 冰蓝色下拉箭头 SVG */
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 14px;
  padding-right: 36px;
  cursor: pointer;
}

/* option 样式（有限控制） */
select.input-field option {
  background: #0d1221;
  color: #e8f0f8;
}
```

**推荐方案**：对于需要精确控制样式的场景，使用自定义下拉组件替代原生 `<select>`，实现毛玻璃下拉面板、冰蓝高亮选项、搜索过滤等。

### Checkbox 复选框

```css
input[type="checkbox"] {
  accent-color: #5ce1ff;
  width: 16px;
  height: 16px;
  cursor: pointer;
}
```

或封装为自定义组件，使用冰蓝色勾选态 + 毛玻璃背景。

### Radio 单选框

```css
input[type="radio"] {
  accent-color: #5ce1ff;
  width: 14px;
  height: 14px;
  cursor: pointer;
}
```

### Range 滑动条

```css
input[type="range"] {
  accent-color: #5ce1ff;
  height: 4px;
  cursor: pointer;
}
```

推荐自定义：轨道 `rgba(92, 225, 255, 0.1)`，滑块 `#5ce1ff` 带 glow 效果。

### Textarea 文本域

与 `.input-field` 完全一致，额外控制 `resize`：

- 默认 `resize: none`
- 如需缩放加 `resize: vertical`

## 交互组件

### Tab 标签切换

| 状态 | 样式 |
|------|------|
| **默认** | `text-[#5a6d82]` 无背景 |
| **Hover** | `text-[#94a8c0] bg-white/5` |
| **选中** | `text-primary bg-primary/10 border-b-2 border-primary` 或 `bg-primary/15 rounded-xl` |

### Toggle 开关

- 关闭：轨道 `rgba(90, 109, 130, 0.3)`，圆点 `#5a6d82`
- 开启：轨道 `rgba(92, 225, 255, 0.3)`，圆点 `#5ce1ff` + glow

### Tooltip 提示

```css
.tooltip {
  background: #162032;
  color: #e8f0f8;
  border: 1px solid rgba(92, 225, 255, 0.1);
  border-radius: 8px;
  font-size: 12px;
  padding: 4px 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
```

### Modal 弹窗

- 遮罩：`bg-black/70 backdrop-blur-sm`
- 面板：`.glass-card !rounded-2xl`
- 头部：`border-b border-[rgba(92,225,255,0.06)]`
- 关闭按钮：`text-[#5a6d82] hover:text-primary`

### Dropdown Menu 下拉菜单

```css
.dropdown-menu {
  background: rgba(13, 18, 33, 0.9);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(92, 225, 255, 0.1);
  border-radius: 12px;
  padding: 4px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.dropdown-item {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: #94a8c0;
  cursor: pointer;
  transition: all 0.1s ease;
}

.dropdown-item:hover {
  background: rgba(92, 225, 255, 0.08);
  color: #5ce1ff;
}
```

## 反馈组件

### Toast / Notification

| 类型 | 左侧色条 | 图标色 |
|------|----------|--------|
| **Success** | `#a0ffcf` | `text-accent` |
| **Error** | `#ff6b8a` | `text-error` |
| **Warning** | `#ffcf5c` | `text-warning` |
| **Info** | `#7dc4ff` | `text-info` |

面板：`glass-card` 样式 + 左侧 3px 色条。

### Loading / Spinner

- 使用 Lucide `loader-2` 图标 + `animate-spin`
- 颜色：`text-primary`
- 骨架屏：`bg-[rgba(92,225,255,0.04)] animate-pulse rounded-xl`

### Empty State 空状态

- 图标：Lucide 对应图标（非 emoji），`text-[#5a6d82]` 大尺寸
- 主文本：`text-[#94a8c0]`
- 副文本：`text-[#5a6d82]`
- CTA 按钮：`.btn-primary`

## 检查清单

新增或修改任何 UI 组件时对照：

- [ ] 颜色全部来自项目色板？无 `gray-*`、`blue-*` 等内置色？
- [ ] 圆角符合规范（12px / 8px / 999px）？
- [ ] `<select>` 已去除浏览器默认箭头并自定义？
- [ ] 原生表单控件已设置 `accent-color: #5ce1ff`？
- [ ] Hover/Focus/Active 态均有定义？
- [ ] 与相邻组件视觉一致（间距、对齐、色调）？
- [ ] 弹窗/下拉使用毛玻璃背景而非纯色？
