# API 接口设计

后端基于 FastAPI，启动后可访问 Swagger：

```text
http://127.0.0.1:8001/docs
```

## 1. AI 与 RAG

### `GET /ai/status`

查看当前本地 RAG、知识库数量和 LLM 占位状态。

### `POST /ai/ask`

用户前台自助咨询。系统会检索 `data/faq.json`，若置信度低于阈值则自动创建工单。

请求示例：

```json
{
  "question": "账号冻结怎么处理？",
  "user": "ops01",
  "contact": "13300000002",
  "category": "account",
  "priority": "normal"
}
```

响应核心字段：

```json
{
  "answer": "根据知识库 FAQ #1：...",
  "confidence": 0.42,
  "fallback": false,
  "ticket_id": null,
  "sources": []
}
```

## 2. 工单接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/tickets?status=open&keyword=账号` | 查询工单 |
| `POST` | `/tickets` | 创建工单 |
| `GET` | `/tickets/{ticket_id}` | 查看工单详情 |
| `PATCH` | `/tickets/{ticket_id}` | 更新工单 |

工单字段包含：

- `question`：申告内容
- `user`：报障人
- `contact`：联系方式
- `category`：类别
- `priority`：优先级
- `status`：处理状态
- `answer`：处理结果
- `callback_status`：回访状态
- `callback_note`：回访记录

## 3. 管理员接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/admin/tickets` | 后台查询工单 |
| `PATCH` | `/admin/tickets/{ticket_id}/resolve` | 解决工单 |
| `GET` | `/admin/faqs` | 查询 FAQ |
| `POST` | `/admin/faqs` | 新增 FAQ |
| `PATCH` | `/admin/faqs/{faq_id}` | 修改 FAQ |
| `DELETE` | `/admin/faqs/{faq_id}` | 删除 FAQ |

解决工单请求示例：

```json
{
  "answer": "已核验身份并按账号解冻流程处理。",
  "resolver": "admin",
  "add_to_kb": true,
  "callback_status": "contacted",
  "callback_note": "已电话回访，用户确认问题解决。"
}
```

当 `add_to_kb` 为 `true` 时，系统会将该工单的问题和处理结果写入 `data/faq.json`。

## 4. 运维账号接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/users/login` | 演示登录 |
| `GET` | `/users?keyword=ops&status=active` | 多条件查询账号 |
| `POST` | `/users` | 新增账号 |
| `GET` | `/users/{user_id}` | 查询账号详情 |
| `PUT` | `/users/{user_id}` | 修改账号 |
| `PATCH` | `/users/{user_id}/status` | 冻结或解冻账号 |
| `DELETE` | `/users/{user_id}` | 删除账号 |

账号字段包含：

- `username`
- `password`
- `role`
- `full_name`
- `department`
- `phone`
- `email`
- `status`

## 5. RPA 模拟接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/reset-password` | 自动化重置密码 |
| `POST` | `/create-account` | 自动化创建账号 |
| `POST` | `/freeze-account` | 自动化冻结清理账号 |

这些接口会在 `rpa_jobs` 表中记录自动化任务。
