<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { chat, listTickets } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { Ticket } from '@/api/types'

interface ChatMsg {
  id: number
  text: string
  isUser: boolean
  meta?: string
}

const auth = useAuthStore()
const messages = ref<ChatMsg[]>([
  {
    id: 0,
    text: '您好，我是运维数字员工。请描述您遇到的问题，我会查询知识库为您解答；无法回答时会自动为您创建工单。',
    isUser: false,
  },
])
const input = ref('')
const sending = ref(false)
const listRef = ref<HTMLElement>()
let seq = 1

const statusMap: Record<string, string> = {
  open: '待处理',
  in_progress: '处理中',
  resolved: '已解决',
  closed: '已关闭',
}

const myTickets = ref<Ticket[]>([])
const loadingTickets = ref(false)

async function scrollToBottom() {
  await nextTick()
  if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return

  // Build conversation history (recent turns) for multi-turn query rewrite.
  // Only real exchanged messages, excluding the greeting and any typing stub.
  const history = messages.value
    .filter((m) => m.text && m.text !== '正在思考...')
    .slice(-6)
    .map((m) => ({ role: (m.isUser ? 'user' : 'assistant') as 'user' | 'assistant', text: m.text }))

  messages.value.push({ id: seq++, text, isUser: true })
  input.value = ''
  sending.value = true
  const typingId = seq++
  messages.value.push({ id: typingId, text: '正在思考...', isUser: false })
  await scrollToBottom()

  try {
    const res = await chat(text, history)
    const idx = messages.value.findIndex((m) => m.id === typingId)
    if (idx !== -1) messages.value.splice(idx, 1)

    let meta = ''
    if (res.intent === 'knowledge' && res.confidence != null) {
      meta = `知识库匹配度 ${(res.confidence * 100).toFixed(0)}%`
    } else if (res.ticket_id) {
      meta = `📋 已创建工单 #${res.ticket_id}`
    }
    messages.value.push({ id: seq++, text: res.content || '暂无回复', isUser: false, meta })

    // Refresh my tickets if a ticket was just created.
    if (res.ticket_id && auth.isLoggedIn) loadMyTickets()
  } catch (e) {
    const idx = messages.value.findIndex((m) => m.id === typingId)
    if (idx !== -1) messages.value.splice(idx, 1)
    messages.value.push({
      id: seq++,
      text: `出错了：${(e as Error).message}`,
      isUser: false,
      meta: '⚠️ 错误',
    })
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

async function loadMyTickets() {
  if (!auth.isLoggedIn) return
  loadingTickets.value = true
  try {
    myTickets.value = await listTickets({ user: auth.username })
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    loadingTickets.value = false
  }
}

onMounted(() => {
  if (auth.isLoggedIn) loadMyTickets()
})
</script>

<template>
  <div class="self-service">
    <section class="chat glass glass-strong">
      <div ref="listRef" class="messages">
        <div
          v-for="m in messages"
          :key="m.id"
          class="msg"
          :class="{ user: m.isUser }"
        >
          <div class="avatar">{{ m.isUser ? '👤' : '🤖' }}</div>
          <div class="bubble">
            <div class="text">{{ m.text }}</div>
            <div v-if="m.meta" class="meta">{{ m.meta }}</div>
          </div>
        </div>
      </div>

      <div class="input-bar">
        <el-input
          v-model="input"
          placeholder="请输入您的问题，按回车发送"
          size="large"
          :disabled="sending"
          @keyup.enter="send"
        />
        <el-button type="primary" size="large" round :loading="sending" @click="send">
          发送
        </el-button>
      </div>
    </section>

    <section v-if="auth.isLoggedIn" class="my-tickets glass">
      <div class="mt-head">
        <h3>我的工单</h3>
        <el-button text :loading="loadingTickets" @click="loadMyTickets">刷新</el-button>
      </div>
      <el-table :data="myTickets" empty-text="暂无工单" size="small" style="width: 100%">
        <el-table-column prop="id" label="#" width="60" />
        <el-table-column prop="question" label="问题" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'resolved' ? 'success' : row.status === 'open' ? 'danger' : 'warning'" size="small">
              {{ statusMap[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="answer" label="处理结果" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="170" />
      </el-table>
    </section>

    <p v-else class="login-tip glass">
      登录后可查看您提交的工单进度。<RouterLink to="/login">去登录 →</RouterLink>
    </p>
  </div>
</template>

<style scoped>
.self-service {
  display: flex;
  flex-direction: column;
  gap: 18px;
  flex: 1;
}
.chat {
  display: flex;
  flex-direction: column;
  height: 60vh;
  min-height: 420px;
  overflow: hidden;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.msg {
  display: flex;
  gap: 10px;
  max-width: 78%;
}
.msg.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.bubble {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 16px 16px 16px 4px;
  padding: 11px 15px;
  font-size: 14.5px;
  line-height: 1.6;
}
.msg.user .bubble {
  background: var(--primary);
  color: #fff;
  border-radius: 16px 16px 4px 16px;
}
.text {
  white-space: pre-wrap;
  word-break: break-word;
}
.meta {
  font-size: 11px;
  opacity: 0.65;
  margin-top: 5px;
}
.input-bar {
  display: flex;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.07);
}
.my-tickets {
  padding: 18px 20px;
}
.mt-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.mt-head h3 {
  margin: 0;
  font-size: 16px;
}
.login-tip {
  padding: 16px 20px;
  font-size: 13px;
  color: var(--muted);
  border-radius: var(--radius);
}
.login-tip a {
  color: var(--primary);
  text-decoration: none;
}
</style>
