<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, RouterView } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getRagStatus } from '@/api'

const auth = useAuthStore()
const router = useRouter()
const statusText = ref('正在连接后端...')

const navItems = [
  { name: 'dashboard', label: '系统总览', icon: 'Odometer' },
  { name: 'tickets', label: '申告工单处理', icon: 'Tickets' },
  { name: 'users', label: '运维账号管理', icon: 'User' },
  { name: 'knowledge', label: '私有知识库', icon: 'Collection' },
  { name: 'rpa', label: 'RPA 自动化', icon: 'MagicStick' },
]

function logout() {
  auth.logout()
  ElMessage.success('已退出登录')
  router.push({ name: 'login' })
}

onMounted(async () => {
  try {
    const rag = await getRagStatus()
    statusText.value = `后端已连接 · FAQ ${rag.faq_count} · ${rag.mode}`
  } catch (e) {
    statusText.value = `后端未连接：${(e as Error).message}`
  }
})
</script>

<template>
  <div class="admin-layout">
    <aside class="sidebar glass">
      <div class="brand">
        <h1>运维数字员工</h1>
        <p>AI · RAG · RPA</p>
      </div>
      <nav class="nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="nav-link"
          active-class="active"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </RouterLink>
        <RouterLink to="/" class="nav-link">
          <el-icon><ChatDotRound /></el-icon>
          <span>前台自助服务</span>
        </RouterLink>
      </nav>
      <div class="sidebar-footer">
        <div class="user-chip">
          <el-icon><UserFilled /></el-icon>
          <span>{{ auth.username }} · {{ auth.role }}</span>
        </div>
        <el-button text size="small" @click="logout">退出登录</el-button>
      </div>
    </aside>

    <main class="main">
      <div class="status-bar glass glass-strong">{{ statusText }}</div>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.admin-layout {
  display: grid;
  grid-template-columns: 256px minmax(0, 1fr);
  min-height: 100vh;
  gap: 18px;
  padding: 18px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  padding: 22px 16px;
  position: sticky;
  top: 18px;
  height: calc(100vh - 36px);
}

.brand {
  padding: 6px 10px 18px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.07);
}
.brand h1 {
  margin: 0;
  font-size: 19px;
  font-weight: 600;
  letter-spacing: -0.02em;
}
.brand p {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 16px;
  flex: 1;
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  color: var(--text);
  text-decoration: none;
  font-size: 14.5px;
  transition: background 0.18s ease;
}
.nav-link:hover {
  background: rgba(255, 255, 255, 0.6);
}
.nav-link.active {
  background: var(--primary);
  color: #fff;
  box-shadow: 0 4px 14px rgba(10, 132, 255, 0.35);
}

.sidebar-footer {
  border-top: 1px solid rgba(0, 0, 0, 0.07);
  padding-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--muted);
}

.main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.status-bar {
  padding: 10px 18px;
  font-size: 13px;
  color: var(--muted);
  border-radius: var(--radius-sm);
}

@media (max-width: 900px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }
  .sidebar {
    position: static;
    height: auto;
  }
}
</style>
