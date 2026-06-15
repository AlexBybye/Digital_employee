<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const router = useRouter()

function goAdmin() {
  if (!auth.isLoggedIn) {
    router.push({ name: 'login' })
    return
  }
  if (auth.role === 'viewer') {
    ElMessage.warning('viewer 角色无权访问后台')
    return
  }
  router.push({ name: 'dashboard' })
}

function logout() {
  auth.logout()
  ElMessage.success('已退出登录')
}
</script>

<template>
  <div class="public-layout">
    <header class="topbar glass glass-strong">
      <div class="brand">
        <span class="logo">🤖</span>
        <div>
          <h1>运维数字员工</h1>
          <p>智能自助服务</p>
        </div>
      </div>
      <div class="actions">
        <template v-if="auth.isLoggedIn">
          <span class="user">👤 {{ auth.username }}</span>
          <el-button v-if="auth.role !== 'viewer'" type="primary" plain round @click="goAdmin">
            进入后台
          </el-button>
          <el-button text round @click="logout">退出</el-button>
        </template>
        <el-button v-else type="primary" round @click="router.push({ name: 'login' })">
          登录
        </el-button>
      </div>
    </header>

    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.public-layout {
  max-width: 980px;
  margin: 0 auto;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 100vh;
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 22px;
  border-radius: var(--radius);
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.logo {
  font-size: 30px;
}
.brand h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}
.brand p {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--muted);
}
.actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.user {
  font-size: 13px;
  color: var(--muted);
}
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
