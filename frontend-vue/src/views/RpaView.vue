<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { aiRpa, listRpaJobs } from '@/api'
import type { RpaCommandResponse, RpaJobHistoryItem } from '@/api/types'

const actionMap: Record<string, string> = {
  'reset-password': '重置密码',
  'create-account': '创建账号',
  'freeze-account': '冻结账号',
  'unfreeze-account': '解冻账号',
}

const command = ref('')
const running = ref(false)
const result = ref<RpaCommandResponse | null>(null)
const jobs = ref<RpaJobHistoryItem[]>([])
const loadingJobs = ref(false)

const examples = [
  '重置 ops01 的密码为 Temp1234',
  '冻结 ops01 账号',
  '解冻 ops01 账号',
]

async function execute() {
  const cmd = command.value.trim()
  if (!cmd) return
  running.value = true
  result.value = null
  try {
    result.value = await aiRpa(cmd)
    if (result.value.success) ElMessage.success('指令执行成功')
    else ElMessage.warning(result.value.message || '指令未执行')
    loadJobs()
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    running.value = false
  }
}

async function loadJobs() {
  loadingJobs.value = true
  try {
    jobs.value = await listRpaJobs()
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    loadingJobs.value = false
  }
}

onMounted(loadJobs)
</script>

<template>
  <div>
    <div class="header">
      <h2 class="page-title">RPA 自动化</h2>
      <p class="page-sub">用自然语言驱动运维操作，所有执行均记录审计日志</p>
    </div>

    <div class="layout">
      <el-card header="AI 智能 RPA">
        <el-input
          v-model="command"
          type="textarea"
          :rows="3"
          placeholder="例如：重置 ops01 的密码为 Temp1234"
        />
        <div class="examples">
          <span class="muted">示例：</span>
          <el-tag
            v-for="ex in examples"
            :key="ex"
            class="ex-tag"
            @click="command = ex"
          >
            {{ ex }}
          </el-tag>
        </div>
        <el-button type="primary" :loading="running" style="margin-top: 12px" @click="execute">
          执行指令
        </el-button>

        <div v-if="result" class="result glass">
          <p><span class="k">操作</span>{{ actionMap[result.action] || result.action || '-' }}</p>
          <p>
            <span class="k">状态</span>
            <el-tag :type="result.success ? 'success' : 'danger'" size="small">
              {{ result.success ? '成功' : '失败' }}
            </el-tag>
          </p>
          <p><span class="k">结果</span>{{ result.message }}</p>
          <div v-if="result.steps && result.steps.length" class="steps">
            <span class="k">步骤</span>
            <ol>
              <li v-for="(s, i) in result.steps" :key="i">{{ s }}</li>
            </ol>
          </div>
        </div>
      </el-card>

      <el-card>
        <template #header>
          <div class="card-head">
            <span>执行历史</span>
            <el-button text :loading="loadingJobs" @click="loadJobs">刷新</el-button>
          </div>
        </template>
        <el-table :data="jobs" v-loading="loadingJobs" empty-text="暂无执行记录" size="small" style="width: 100%">
          <el-table-column prop="created_at" label="时间" width="170" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">{{ actionMap[row.action] || row.action }}</template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' || row.status === 'success' ? 'success' : 'info'" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="result" label="结果" show-overflow-tooltip />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.header {
  margin-bottom: 18px;
}
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr);
  gap: 16px;
}
.examples {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.ex-tag {
  cursor: pointer;
}
.muted {
  color: var(--muted);
  font-size: 13px;
}
.result {
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: var(--radius-sm);
}
.result p {
  margin: 6px 0;
  font-size: 14px;
  display: flex;
  gap: 12px;
  align-items: center;
}
.k {
  color: var(--muted);
  min-width: 48px;
}
.steps {
  display: flex;
  gap: 12px;
  font-size: 14px;
}
.steps ol {
  margin: 4px 0;
  padding-left: 18px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
