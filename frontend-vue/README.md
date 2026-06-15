# 运维数字员工 · Vue 前端

基于 Vue 3 + TypeScript + Vite + Element Plus 的前端，采用苹果玻璃拟态（glassmorphism）风格。与旧版静态前端 `../frontend/` 并存，二者均可独立运行。

## 技术栈

- Vue 3 `<script setup>` + TypeScript
- Vite 6（开发与构建）
- Pinia（状态管理）+ Vue Router（hash 路由）
- Element Plus（组件库，已重写为玻璃风格）
- axios（API 请求，自动注入 Bearer token）

## 运行

```bash
cd frontend-vue
npm install
npm run dev          # 开发服务器 http://127.0.0.1:5173
npm run build        # 类型检查 + 生产构建到 dist/
npm run preview      # 预览生产构建
```

后端地址通过 `.env` 配置：

```
VITE_API_BASE=http://127.0.0.1:8001
```

需先启动后端（见 `../backend`）。

## 页面

| 路由 | 页面 | 权限 |
| --- | --- | --- |
| `/` | 前台自助服务（AI 对话 + 我的工单） | 公开 |
| `/login` | 登录 | 公开 |
| `/admin/dashboard` | 系统总览 | 登录（viewer 除外） |
| `/admin/tickets` | 申告工单处理 | 登录（viewer 除外） |
| `/admin/users` | 运维账号管理 | 登录（viewer 除外） |
| `/admin/knowledge` | 私有知识库 | 登录（viewer 除外） |
| `/admin/rpa` | RPA 自动化 | 登录（viewer 除外） |

演示账号：`admin/admin`、`ops01/ops1234`、`viewer01/viewer123`。

## 目录结构

```text
frontend-vue/
├── src/
│   ├── api/          # axios 实例、TS 类型（对齐后端 schemas）、接口封装
│   ├── stores/       # Pinia auth store（token/user/role，localStorage 持久化）
│   ├── router/       # 路由 + 登录/角色守卫
│   ├── layouts/      # AdminLayout（玻璃侧边栏）+ PublicLayout
│   ├── views/        # 7 个页面组件
│   └── styles/       # 玻璃主题 + Element Plus 覆盖样式
├── .env              # VITE_API_BASE
└── vite.config.ts
```
