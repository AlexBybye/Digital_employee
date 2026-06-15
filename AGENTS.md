# AGENTS.md

## 项目说明

这是一个运维数字员工示例项目，用于演示：

- 本地 RAG 知识库问答
- AI 低置信度自动创建工单
- 管理员处理工单、填写回访记录后自动沉淀 FAQ
- 运维账号 CRUD、冻结、解冻和多条件查询
- RPA 重置密码、创建账号、冻结账号模拟

## 开发约定

- 后端入口固定为 `backend/main.py`。
- API 路由放在 `backend/api/`。
- Pydantic 模型放在 `backend/models/`。
- 业务逻辑放在 `backend/services/`。
- RAG 检索逻辑放在 `backend/rag/`。
- SQLite 和 JSON 数据访问放在 `backend/database/`。
- FAQ 数据文件固定为 `data/faq.json`。
- 工单数据库固定为 `data/tickets.db`。
- 接口设计文档放在 `docs/API.md`。
- 课程设计说明放在 `docs/COURSE_DESIGN.md`。

## 运行命令

```bash
cd backend
uvicorn main:app --reload --port 8001
```

## 注意事项

- 当前版本没有实现登录鉴权，方便本地演示和接口测试。
- `/users/login` 仅用于课程设计演示，返回临时 token，不做生产级鉴权。
- `services/llm_service.py` 是本地 LLM 占位实现，后续可替换为 Ollama、LM Studio 或其他本地模型 API。
- `rag/retriever.py` 使用词袋余弦相似度模拟向量检索，后续可替换为 FAISS。
