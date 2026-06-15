<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listAdminTickets, getTicket, updateTicket, resolveTicket } from '@/api'
import type { Ticket, TicketStatus, Priority } from '@/api/types'

const statusMap: Record<string, string> = {
  open: '待处理', in_progress: '处理中', resolved: '已解决', closed: '已关闭',
}
const priorityMap: Record<string, string> = {
  low: '低', normal: '普通', high: '高', urgent: '紧急',
}
function statusTag(s: TicketStatus) {
  return s === 'resolved' ? 'success' : s === 'open' ? 'danger' : s === 'closed' ? 'info' : 'warning'
}
function priorityTag(p: Priority) {
  return p === 'urgent' || p === 'high' ? 'danger' : p === 'normal' ? 'warning' : 'info'
}

const tickets = ref<Ticket[]>([])
const loading = ref(false)
const filter = reactive({ status: '', keyword: '' })

const selected = ref<Ticket | null>(null)
const form = reactive({
  resolver: 'admin',
  resolution_note: '',
  callback_note: '',
  add_to_kb: false,
  kb_answer: '',
})
const resolving = ref(false)

async function load() {
  loading.value = true
  try {
    tickets.value = await listAdminTickets({
      status: filter.status || undefined,
      keyword: filter.keyword.trim() || undefined,
    })
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

function rowClass({ row }: { row: Ticket }) {
  return selected.value?.id === row.id ? 'sel-row' : ''
}

async function pick(row: Ticket) {
  if (selected.value?.id === row.id) {
    selected.value = null
    return
  }
  const t = await getTicket(row.id)
  selected.value = t
  form.resolver = t.resolver || 'admin'
  form.resolution_note = t.answer || '已核验身份，按标准运维流程处理并完成回访。'
  form.callback_note = t.callback_note || '已电话回访，报障人确认问题解决。'
  form.add_to_kb = false
  form.kb_answer = ''
}

async function markInProgress() {
  if (!selected.value) return
  try {
    const next: TicketStatus = selected.value.status === 'in_progress' ? 'open' : 'in_progress'
    const t = await updateTicket(selected.value.id, { status: next, resolver: form.resolver })
    selected.value = t
    ElMessage.success(next === 'in_progress' ? '已标记处理中' : '已恢复待处理')
    load()
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}

async function doResolve() {
  if (!selected.value) return
  resolving.value = true
  try {
    const t = await resolveTicket(selected.value.id, {
      resolution_note: form.resolution_note.trim(),
      resolver: form.resolver.trim() || 'admin',
      add_to_kb: form.add_to_kb,
      kb_answer: form.add_to_kb ? form.kb_answer.trim() : '',
      callback_status: 'contacted',
      callback_note: form.callback_note.trim(),
    })
    selected.value = t
    ElMessage.success(form.add_to_kb ? '工单已解决并沉淀到知识库' : '工单已解决')
    load()
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    resolving.value = false
  }
}

async function closeTicket() {
  if (!selected.value) return
  const id = selected.value.id
  try {
    await ElMessageBox.confirm(`确定关闭工单 #${id} 吗？关闭后将不可再处理。`, '关闭工单', {
      type: 'warning',
      confirmButtonText: '确定关闭',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    const t = await updateTicket(id, { status: 'closed' })
    selected.value = t
    ElMessage.success('工单已关闭')
    load()
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}

onMounted(load)
</script>
<template>
  <div>
    <div class="header">
      <h2 class="page-title">申告工单处理</h2>
      <p class="page-sub">查询、处理、回访工单，并可将处理结果沉淀到知识库</p>
    </div>

    <div class="layout">
      <!-- Ticket list -->
      <el-card class="list-card">
        <template #header>
          <div class="filters">
            <el-select v-model="filter.status" placeholder="全部状态" clearable style="width: 130px">
              <el-option label="待处理" value="open" />
              <el-option label="处理中" value="in_progress" />
              <el-option label="已解决" value="resolved" />
              <el-option label="已关闭" value="closed" />
            </el-select>
            <el-input v-model="filter.keyword" placeholder="关键词搜索" clearable style="width: 180px" @keyup.enter="load" />
            <el-button type="primary" :loading="loading" @click="load">查询</el-button>
          </div>
        </template>

        <el-table
          :data="tickets"
          v-loading="loading"
          empty-text="暂无工单"
          size="small"
          highlight-current-row
          :row-class-name="rowClass"
          @row-click="pick"
          style="width: 100%; cursor: pointer"
        >
          <el-table-column prop="id" label="#" width="54" />
          <el-table-column label="问题 / 处理结果" min-width="200">
            <template #default="{ row }">
              <div>{{ row.question }}</div>
              <small class="muted">{{ row.answer || '待处理' }}</small>
            </template>
          </el-table-column>
          <el-table-column label="报障人" width="120">
            <template #default="{ row }">
              {{ row.user }}<br /><small class="muted">{{ row.contact || '-' }}</small>
            </template>
          </el-table-column>
          <el-table-column label="优先级" width="80">
            <template #default="{ row }">
              <el-tag :type="priorityTag(row.priority)" size="small">{{ priorityMap[row.priority] || row.priority }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="statusTag(row.status)" size="small">{{ statusMap[row.status] || row.status }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- Resolve panel -->
      <el-card class="detail-card" header="工单处理">
        <div v-if="!selected" class="empty-detail">从左侧列表选择一个工单进行处理</div>
        <div v-else>
          <div class="detail-head">
            <span class="tid">工单 #{{ selected.id }}</span>
            <el-tag :type="statusTag(selected.status)" size="small">{{ statusMap[selected.status] }}</el-tag>
          </div>
          <p class="q">{{ selected.question }}</p>

          <el-form label-position="top" size="default">
            <el-form-item label="处理人">
              <el-input v-model="form.resolver" />
            </el-form-item>
            <el-form-item label="处理记录（内部，不写入知识库）">
              <el-input v-model="form.resolution_note" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="回访记录">
              <el-input v-model="form.callback_note" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="form.add_to_kb">沉淀到知识库 FAQ</el-checkbox>
            </el-form-item>
            <el-form-item v-if="form.add_to_kb" label="知识库答案">
              <el-input v-model="form.kb_answer" type="textarea" :rows="2" placeholder="留空则不沉淀" />
            </el-form-item>
          </el-form>

          <div class="actions">
            <el-button :type="selected.status === 'in_progress' ? 'warning' : 'default'" @click="markInProgress">
              {{ selected.status === 'in_progress' ? '恢复待处理' : '标记处理中' }}
            </el-button>
            <el-button type="primary" :loading="resolving" @click="doResolve">解决工单</el-button>
            <el-button type="danger" plain @click="closeTicket">关闭工单</el-button>
          </div>
        </div>
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
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: 16px;
}
.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.muted {
  color: var(--muted);
}
.detail-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.tid {
  font-size: 17px;
  font-weight: 600;
}
.q {
  margin: 0 0 14px;
  color: var(--text);
  font-size: 14px;
}
.empty-detail {
  color: var(--muted);
  text-align: center;
  padding: 40px 0;
}
.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
:deep(.sel-row) {
  background: rgba(10, 132, 255, 0.1) !important;
}
@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
