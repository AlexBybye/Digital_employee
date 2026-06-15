<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value.trim(), password.value.trim())
    ElMessage.success('登录成功')
    const redirect = route.query.redirect as string | undefined
    if (redirect) {
      router.push(redirect)
    } else if (auth.role === 'viewer') {
      router.push({ name: 'self-service' })
    } else {
      router.push({ name: 'dashboard' })
    }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <div class="login-card glass glass-strong">
      <div class="head">
        <span class="logo">🤖</span>
        <h1>运维数字员工</h1>
        <p>请登录以访问系统</p>
      </div>

      <el-form @submit.prevent="submit" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="username" placeholder="请输入用户名" size="large" clearable />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            @keyup.enter="submit"
          />
        </el-form-item>

        <p v-if="error" class="error">{{ error }}</p>

        <el-button
          type="primary"
          size="large"
          round
          style="width: 100%"
          :loading="loading"
          @click="submit"
        >
          登 录
        </el-button>
      </el-form>

      <div class="hint">
        <p>演示账号</p>
        <code>admin / admin</code>
        <code>ops01 / ops1234</code>
        <code>viewer01 / viewer123</code>
      </div>

      <RouterLink to="/" class="back">← 返回前台自助服务</RouterLink>
    </div>
  </div>
</template>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.login-card {
  width: 100%;
  max-width: 380px;
  padding: 36px 32px 28px;
}
.head {
  text-align: center;
  margin-bottom: 22px;
}
.logo {
  font-size: 44px;
}
.head h1 {
  margin: 10px 0 4px;
  font-size: 22px;
  font-weight: 600;
}
.head p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}
.error {
  color: var(--danger);
  font-size: 13px;
  margin: 0 0 12px;
}
.hint {
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.07);
  text-align: center;
}
.hint p {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--muted);
}
.hint code {
  display: inline-block;
  margin: 0 4px 4px;
  padding: 3px 10px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  font-size: 12px;
}
.back {
  display: block;
  text-align: center;
  margin-top: 18px;
  color: var(--primary);
  text-decoration: none;
  font-size: 13px;
}
</style>
