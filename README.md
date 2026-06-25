# 运维数字员工系统

本项目对应"课题六：运维数字员工的建设"，实现一个基于 AI + RAG + RPA 思路的课程设计原型系统。

## 快速开始

```powershell
# 一键初始化 + 启动服务
双击 scripts/setup.bat
```

打开 http://127.0.0.1:5173/self-service.html 即可使用前台自助服务。

> 后台管理页面（系统总览、工单、账号、知识库、RPA）需先登录：
> - **admin** / **admin**（管理员）
> - **ops01** / **ops1234**（运维人员）
> - **viewer01** / **viewer123**（只读观察员）

## 系统架构

```text
用户输入一句话
       |
  AI 统一入口（/ai/chat）
       |
  +--- 检索 FAQ（BGE 向量 + BoW 关键词加权评分）
  +--- 高置信度(≥0.70)：直接返回 FAQ 答案
  +--- 中信度(0.40-0.70, BoW≥0.10)：DeepSeek 结合 FAQ 上下文生成回答
  +--- 低置信度/无关键词重叠：自动创建工单 → 后台人工处理 → 沉淀 FAQ
  +--- 操作类指令 → AI RPA 调度 → 自动执行并记录审计
```

## 已实现功能

### AI 智能对话（统一入口）
- 自然语言输入，AI 自动判断意图：知识问答 / 执行操作 / 创建工单
- 对话式气泡界面，输入即问即答

### 本地 RAG 知识库
- 基于 `data/faq.json` 的 FAQ 检索
- **向量检索**：BGE-small-zh-v1.5 中文嵌入模型（512 维）+ numpy 向量库
- **关键词检索**：中文分词 + 二元组 + 标点过滤 + 停用词
- **加权评分**：`综合得分 = 0.7 × 向量相似度 + 0.3 × BoW 相似度`
- **三层路由**：
  - 综合得分 ≥ 0.55：直接返回 FAQ 答案（不调大模型）
  - 0.40 ≤ 综合得分 < 0.70 且 BoW ≥ 0.10：DeepSeek 结合 FAQ 上下文推理
  - 否则：自动创建工单转人工

### 本地大模型推理
- Ollama + DeepSeek-R1:1.5B 本地部署，无需联网
- `services/llm_service.py` 为适配层，可替换为其他模型

### 工单处理闭环
- AI 无法回答时自动创建工单
- 后台查询、处理、回访
- 处理结果与知识库答案分离（内部记录 vs 沉淀 FAQ）
- 支持选择是否沉淀到知识库
- 工单关闭需要二次确认弹窗

### 运维账号管理
- 账号 CRUD：新增、查询、修改、删除（含确认弹窗）
- 冻结 / 解冻
- 多条件过滤查询

### AI 智能 RPA
- 自然语言驱动自动化（如"重置ops01的密码为Temp1234"）
- 支持操作：重置密码、创建账号、冻结账号、解冻账号
- 三层安全防护：垃圾输入过滤、LLM 意图过滤、受保护账号拦截
- 所有操作自动记录审计日志，历史可追溯

### 登录鉴权
- 后台管理页面需登录才能访问
- 前台自助服务无需登录，面向普通用户

### 自学习闭环
- 工单解决后可沉淀到 FAQ 知识库
- FAQ 支持新增、修改、删除

## 目录结构

```text
│  .gitignore
│  AGENTS.md
│  README.md
│  VERSION
│  
├─backend
│  │  auth.py
│  │  main.py
│  │  requirements.txt
│  │          
│  ├─api
│  │      admin.py
│  │      ai.py
│  │      health.py
│  │      rpa.py
│  │      tickets.py
│  │      users.py
│  │      __init__.py
│  │      
│  ├─database
│  │      db.py
│  │      __init__.py
│  │      
│  ├─eval
│  │      dataset.json
│  │      run_eval.py
│  │      __init__.py
│  │      
│  ├─models
│  │      schemas.py
│  │      __init__.py
│  │      
│  ├─rag
│  │      chroma_store.py
│  │      chunker.py
│  │      config.py
│  │      doc_store.py
│  │      ingest.py
│  │      query_rewrite.py
│  │      reranker.py
│  │      retriever.py
│  │      __init__.py
│  │      
│  ├─reports
│  │      rag_v1_baseline.md
│  │      rag_v1_vs_v2.md
│  │      rag_v2.md
│  │      rag_v2_docs.md
│  │      
│  ├─services
│  │      ai_rpa_service.py
│  │      ai_service.py
│  │      chat_service.py
│  │      llm_service.py
│  │      rpa_service.py
│  │      ticket_service.py
│  │      __init__.py
│  │      
│  └─tests
│          test_gen2_rag.py
│          test_retriever.py
│          
├─data
│  │  faq.json
│  │  
│  └─models
│      └─bge-small-zh-v1.5
│          │  .gitattributes
│          │  config.json
│          │  config_sentence_transformers.json
│          │  model.safetensors
│          │  modules.json
│          │  sentence_bert_config.json
│          │  special_tokens_map.json
│          │  tokenizer.json
│          │  tokenizer_config.json
│          │  vocab.txt
│          │  
│          └─1_Pooling
│                  config.json
│                  
├─frontend-vue
│  │  .gitignore
│  │  env.d.ts
│  │  index.html
│  │  package-lock.json
│  │  package.json
│  │  README.md
│  │  tsconfig.json
│  │  tsconfig.node.json
│  │  tsconfig.node.tsbuildinfo
│  │  tsconfig.tsbuildinfo
│  │  vite.config.d.ts
│  │  vite.config.ts
│  │  
│  └─src
│      │  App.vue
│      │  main.ts
│      │  
│      ├─api
│      │      client.ts
│      │      index.ts
│      │      types.ts
│      │      
│      ├─layouts
│      │      AdminLayout.vue
│      │      PublicLayout.vue
│      │      
│      ├─router
│      │      index.ts
│      │      
│      ├─stores
│      │      auth.ts
│      │      
│      ├─styles
│      │      element-overrides.css
│      │      theme.css
│      │      
│      └─views
│              DashboardView.vue
│              KnowledgeView.vue
│              LoginView.vue
│              RpaView.vue
│              SelfServiceView.vue
│              TicketsView.vue
│              UsersView.vue
│              
└─scripts
        setup.bat
        setup.sh
        setup_ollama.ps1
```

## 环境要求

| 项目 | 最低配置 | 推荐配置 |
| --- | --- | --- |
| 内存 | 8 GB | 16 GB |
| 硬盘 | 10 GB 可用空间 | 20 GB 以上 |
| 系统 | Windows 10+ | Windows 11 |
| Python | 3.9+ | 3.13+ |

> 模型文件（deepseek-r1:1.5b）约 1.1 GB，首次运行会自动下载。

## 一键初始化

在项目根目录，双击 `scripts/setup.bat`。

脚本会自动完成：
1. 检查 Python 环境
2. 安装 Ollama（如未安装）
3. 启动 Ollama 服务
4. 拉取 DeepSeek-R1:1.5B 模型
5. 安装 Python 依赖
6. 验证 Ollama API
7. 自动启动后端服务（新窗口）
8. 自动启动前端服务（新窗口）

## 手动运行

### 后端

```bash
cd ops-digital-employee/backend
pip install -r requirements.txt
uvicorn main:app --port 8001
```

后端地址：

```text
http://127.0.0.1:8001
```

接口文档：

```text
http://127.0.0.1:8001/docs
```

### 前端

```bash
cd ops-digital-employee/frontend
python -m http.server 5173 --bind 127.0.0.1
```

然后访问：

```text
http://127.0.0.1:5173/index.html
```

前端默认请求后端：

```text
http://127.0.0.1:8001
```

## 页面说明

| 页面 | 地址 | 说明 | 需登录 |
| --- | --- | --- | :---: |
| 前台自助服务 | /self-service.html | 统一 AI 对话入口：问答 / 操作 / 工单 | 否 |
| 系统总览 | /index.html | 查看系统状态和功能入口 | 是 |
| 申告工单处理 | /tickets.html | 查询、处理、回访、沉淀知识库 | 是 |
| 运维账号管理 | /users.html | 账号增删改查、冻结、解冻 | 是 |
| 私有知识库 | /knowledge.html | FAQ 新增、修改、删除 | 是 |
| RPA 自动化 | /rpa.html | AI 智能 RPA + 执行历史审计 | 是 |

## 示例账号

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| admin | admin | admin |
| ops01 | ops1234 | operator |
| viewer01 | viewer123 | viewer |

## 核心接口

### AI

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | /ai/chat | 统一对话入口，委托知识库问答（知识/RPA/工单分流） |
| POST | /ai/ask | 知识库问答，低置信度自动建工单 |
| GET | /ai/status | 查看 RAG/LLM 当前运行模式 |
| POST | /ai/rpa | AI 驱动 RPA，自然语言指令执行操作 |

### 工单

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /tickets | 查询申告工单 |
| POST | /tickets | 创建申告工单 |
| PATCH | /tickets/{ticket_id} | 更新工单状态 |
| GET | /admin/tickets | 后台查询工单（支持过滤） |
| PATCH | /admin/tickets/{ticket_id}/resolve | 解决工单（可选沉淀 FAQ） |

### 账号

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | /users/login | 登录 |
| GET | /users | 查询账号 |
| POST | /users | 新增账号 |
| PUT | /users/{user_id} | 修改账号 |
| PATCH | /users/{user_id}/status | 冻结或解冻 |
| DELETE | /users/{user_id} | 删除账号 |

### 知识库

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /admin/faqs | 查询 FAQ |
| POST | /admin/faqs | 新增 FAQ |
| PATCH | /admin/faqs/{faq_id} | 修改 FAQ |
| DELETE | /admin/faqs/{faq_id} | 删除 FAQ |

### RPA

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | /reset-password | RPA 模拟重置密码 |
| POST | /create-account | RPA 模拟创建账号 |
| POST | /freeze-account | RPA 模拟冻结账号 |
| POST | /unfreeze-account | RPA 模拟解冻账号 |
| GET | /rpa-jobs | RPA 执行历史 |

## 课程设计完成度

当前版本已经覆盖课题要求中的主要闭环：

```text
用户一句话
   |
AI 统一入口
   |
+-- 知识问答 -> RAG + DeepSeek -> 直接回答
+-- 操作指令 -> AI RPA -> 自动执行 + 审计日志
+-- 无法处理 -> 创建工单 -> 后台人工处理 -> 沉淀 FAQ
```

### 已满足的课题要求

| 课题要求 | 实现情况 |
| --- | --- |
| 大模型本地部署 | Ollama + DeepSeek-R1:1.5B |
| RAG 私有知识库 | 本地 FAQ 检索（BGE 中文向量 + BoW 关键词加权） + 大模型上下文增强 |
| AI 驱动 RPA | 自然语言指令自动执行运维操作 |
| 运维申告门户 | 前台统一对话 / 后台工单处理 |
| 账号增删改查 | 完整 CRUD + 冻结/解冻 + 登录鉴权 |
| 低置信度转人工 | 自动创建工单 |
| 回访与知识沉淀 | 工单解决后可选择沉淀 FAQ |
| 审计追溯 | RPA 执行历史完整记录 |
| 一键部署 | setup_ollama.ps1 自动化脚本 |
| 权限控制 | 后台登录鉴权，前台无需登录 |
