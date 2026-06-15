# 课程设计说明书：运维数字员工的建设

## 1. 课题背景

企业运维工作中存在大量重复性高、流程性强、规则清晰的任务，例如账号创建、密码重置、账号冻结、常见故障咨询、申告记录处理等。通过 AI + RAG + RPA 建设运维数字员工，可以提升一线处理效率，降低人工重复劳动，并将人工处理经验持续沉淀为知识库。

## 2. 设计目标

本系统围绕“运维数字员工”完成以下目标：

1. 构建本地私有 FAQ 知识库。
2. 通过 RAG 检索回答运维常见问题。
3. 当 AI 无法回答时，自动创建在线申告工单。
4. 后台运维人员处理工单并进行回访。
5. 工单解决后自动完善 FAQ，实现自学习闭环。
6. 提供运维账号增删改查、冻结、解冻能力。
7. 提供 RPA 自动化流程模拟，如重置密码、创建账号、冻结账号。

## 3. 总体架构

```text
前端门户
  ├─ 自助问答
  ├─ 在线申告
  ├─ 后台工单处理
  ├─ 账号维护
  └─ RPA 操作

FastAPI 后端
  ├─ api/       接口层
  ├─ services/ 业务服务层
  ├─ rag/      检索增强生成模块
  ├─ models/   请求和响应模型
  └─ database/ 数据访问层

数据层
  ├─ data/faq.json    私有 FAQ 知识库
  └─ data/tickets.db  SQLite 数据库
```

## 4. 功能模块

### 4.1 本地大模型 + RAG 私有知识库

当前课程设计版本使用本地占位 LLM 和词袋余弦相似度模拟向量检索，避免依赖外部云服务。模块边界已保留，后续可以替换为：

- DeepSeek 本地部署
- Ollama 本地模型 API
- AnythingLLM 私有知识库
- FAISS 向量数据库

相关文件：

- `backend/rag/retriever.py`
- `backend/services/llm_service.py`
- `backend/services/ai_service.py`
- `data/faq.json`

### 4.2 前台自助服务

用户在前端页面输入问题，系统调用 `/ai/ask`。如果知识库命中，直接返回答案；如果置信度低，系统自动创建工单并返回工单编号。

相关文件：

- `frontend/index.html`
- `frontend/app.js`
- `backend/api/ai.py`

### 4.3 在线申告与人工处理

工单记录报障人、联系方式、类别、优先级、处理状态、处理结果、回访状态和回访记录。后台可查询并处理这些记录。

相关文件：

- `backend/api/tickets.py`
- `backend/api/admin.py`
- `backend/services/ticket_service.py`

### 4.4 自学习闭环

管理员解决工单时，如果选择 `add_to_kb=true`，系统会把该工单的问题和答案追加到 `data/faq.json`。这样后续相似问题可以由 AI 自动回答。

### 4.5 运维账号维护

系统支持运维账号：

- 新增
- 查询
- 修改
- 删除
- 冻结
- 解冻

账号字段包含用户名、密码、角色、姓名、部门、电话、邮箱和状态。

相关文件：

- `backend/api/users.py`
- `backend/database/db.py`

### 4.6 RPA 模拟

系统提供三个自动化流程：

- `/reset-password`：重置密码
- `/create-account`：创建账号
- `/freeze-account`：冻结账号

相关文件：

- `backend/api/rpa.py`
- `backend/services/rpa_service.py`

## 5. 数据库设计

### 5.1 users 表

| 字段 | 说明 |
| --- | --- |
| `id` | 主键 |
| `username` | 用户名 |
| `password_hash` | 密码哈希 |
| `role` | 角色 |
| `full_name` | 姓名 |
| `department` | 部门 |
| `phone` | 电话 |
| `email` | 邮箱 |
| `status` | active/frozen |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### 5.2 tickets 表

| 字段 | 说明 |
| --- | --- |
| `id` | 主键 |
| `question` | 申告内容 |
| `user` | 报障人 |
| `contact` | 联系方式 |
| `category` | 问题类别 |
| `priority` | 优先级 |
| `status` | 工单状态 |
| `answer` | 处理结果 |
| `resolver` | 处理人 |
| `callback_status` | 回访状态 |
| `callback_note` | 回访记录 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |
| `resolved_at` | 解决时间 |

### 5.3 rpa_jobs 表

记录 RPA 模拟任务的动作、请求内容、状态和结果。

## 6. 测试环境

硬件要求参考课题要求：

- PC 机
- 4 核 CPU
- 8GB 内存
- 100GB 硬盘

软件环境：

- Python 3.10+
- FastAPI
- SQLite
- 浏览器

## 7. 运行与测试

启动后端：

```bash
cd backend
uvicorn main:app --reload --port 8001
```

打开前端：

```bash
cd ops-digital-employee
python -m http.server 5173 -d frontend
```

```text
http://127.0.0.1:5173/index.html
```

推荐测试流程：

1. 进入“前台自助服务”，输入“账号冻结怎么处理？”，验证知识库命中。
2. 输入一个知识库没有的问题，验证自动生成工单。
3. 进入“申告工单处理”，查询并选择工单。
4. 填写处理结果和回访记录，点击解决并沉淀知识库。
5. 进入“私有知识库”，确认新增知识。
6. 进入“运维账号管理”，测试账号新增、修改、查询、冻结、解冻、删除。
7. 进入“RPA 自动化”，测试重置密码、创建账号、冻结账号。

## 8. 后续扩展

本课程设计原型可以继续增强：

- 接入 DeepSeek/Ollama 本地大模型。
- 使用 FAISS 替换当前词袋检索。
- 增加 JWT 登录鉴权和角色权限控制。
- 使用 Vue3 重构前端后台。
- 增加工单导出、统计报表和知识库版本管理。
