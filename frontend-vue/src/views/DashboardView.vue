<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getHealth, getRagStatus, listUsers, listTickets, listFaqs } from '@/api'
import type { Health, RagStatus } from '@/api/types'

const health = ref<Health | null>(null)
const rag = ref<RagStatus | null>(null)
const counts = ref({ users: 0, tickets: 0, faqs: 0 })
const loading = ref(true)

onMounted(async () => {
  try {
    const [h, r, users, tickets, faqs] = await Promise.all([
      getHealth(),
      getRagStatus(),
      listUsers(),
      listTickets(),
      listFaqs(),
    ])
    health.value = h
    rag.value = r
    counts.value = { users: users.length, tickets: tickets.length, faqs: faqs.length }
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <div class="header">
      <h2 class="page-title">系统总览</h2>
      <p class="page-sub">运维数字员工门户运行状态一览</p>
    </div>

    <div v-loading="loading" class="stats">
      <el-card class="stat">
        <div class="stat-num">{{ counts.users }}</div>
        <div class="stat-label">运维账号</div>
      </el-card>
      <el-card class="stat">
        <div class="stat-num">{{ counts.tickets }}</div>
        <div class="stat-label">申告工单</div>
      </el-card>
      <el-card class="stat">
        <div class="stat-num">{{ counts.faqs }}</div>
        <div class="stat-label">FAQ 知识条目</div>
      </el-card>
    </div>

    <div class="info">
      <el-card header="后端服务">
        <p><span class="k">状态</span>{{ health?.status ?? '-' }}</p>
        <p><span class="k">服务</span>{{ health?.service ?? '-' }}</p>
      </el-card>
      <el-card header="RAG 知识库">
        <p><span class="k">模式</span>{{ rag?.mode ?? '-' }}</p>
        <p><span class="k">打分器</span>{{ rag?.scorer ?? '-' }}</p>
        <p><span class="k">检索管线</span>{{ rag?.vector_store ?? '-' }}</p>
        <p><span class="k">大模型</span>{{ rag?.llm_provider ?? '-' }}</p>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.header {
  margin-bottom: 18px;
}
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 18px;
}
.stat {
  text-align: center;
}
.stat-num {
  font-size: 38px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--primary);
}
.stat-label {
  margin-top: 4px;
  color: var(--muted);
  font-size: 14px;
}
.info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.info p {
  margin: 6px 0;
  font-size: 14px;
  display: flex;
  gap: 12px;
}
.k {
  color: var(--muted);
  min-width: 76px;
}
@media (max-width: 860px) {
  .stats,
  .info {
    grid-template-columns: 1fr;
  }
}
</style>
