<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, createUser, updateUser, setUserStatus, deleteUser } from '@/api'
import type { User, Role, AccountStatus } from '@/api/types'

const roleMap: Record<string, string> = { admin: '管理员', operator: '运维员', viewer: '观察员' }

const users = ref<User[]>([])
const loading = ref(false)
const filter = reactive({ keyword: '', role: '', status: '' })

const emptyForm = () => ({
  id: 0,
  username: '',
  password: '',
  role: 'operator' as Role,
  full_name: '',
  department: '',
  phone: '',
  email: '',
  status: 'active' as AccountStatus,
})
const form = reactive(emptyForm())
const editing = ref(false)
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    users.value = await listUsers({
      keyword: filter.keyword.trim() || undefined,
      role: filter.role || undefined,
      status: filter.status || undefined,
    })
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form, emptyForm())
  editing.value = false
}

function edit(row: User) {
  Object.assign(form, { ...row, password: '' })
  editing.value = true
}

async function save() {
  if (!form.username) {
    ElMessage.warning('用户名不能为空')
    return
  }
  if (!editing.value && !form.password) {
    ElMessage.warning('新建账号必须设置密码')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      const payload: Record<string, unknown> = {
        username: form.username, role: form.role, full_name: form.full_name,
        department: form.department, phone: form.phone, email: form.email, status: form.status,
      }
      if (form.password) payload.password = form.password
      await updateUser(form.id, payload)
      ElMessage.success('账号已更新')
    } else {
      await createUser({
        username: form.username, password: form.password, role: form.role,
        full_name: form.full_name, department: form.department,
        phone: form.phone, email: form.email, status: form.status,
      })
      ElMessage.success('账号已创建')
    }
    resetForm()
    load()
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: User) {
  const next: AccountStatus = row.status === 'active' ? 'frozen' : 'active'
  try {
    await setUserStatus(row.id, next)
    ElMessage.success(next === 'frozen' ? '账号已冻结' : '账号已解冻')
    load()
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}

async function remove(row: User) {
  try {
    await ElMessageBox.confirm(`确定删除账号 ${row.username} (#${row.id}) 吗？`, '删除账号', {
      type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteUser(row.id)
    ElMessage.success('账号已删除')
    if (form.id === row.id) resetForm()
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
      <h2 class="page-title">运维账号管理</h2>
      <p class="page-sub">账号增删改查、冻结与解冻、多条件查询</p>
    </div>

    <div class="layout">
      <el-card class="list-card">
        <template #header>
          <div class="filters">
            <el-input v-model="filter.keyword" placeholder="用户名/姓名/部门" clearable style="width: 170px" @keyup.enter="load" />
            <el-select v-model="filter.role" placeholder="全部角色" clearable style="width: 120px">
              <el-option label="管理员" value="admin" />
              <el-option label="运维员" value="operator" />
              <el-option label="观察员" value="viewer" />
            </el-select>
            <el-select v-model="filter.status" placeholder="全部状态" clearable style="width: 110px">
              <el-option label="正常" value="active" />
              <el-option label="冻结" value="frozen" />
            </el-select>
            <el-button type="primary" :loading="loading" @click="load">查询</el-button>
          </div>
        </template>

        <el-table :data="users" v-loading="loading" empty-text="暂无账号" size="small" style="width: 100%">
          <el-table-column prop="id" label="#" width="50" />
          <el-table-column label="账号" min-width="140">
            <template #default="{ row }">
              {{ row.username }}<br /><small class="muted">{{ row.email || '-' }}</small>
            </template>
          </el-table-column>
          <el-table-column label="姓名 / 部门" min-width="140">
            <template #default="{ row }">
              {{ row.full_name || '-' }}<br /><small class="muted">{{ row.department || '-' }} · {{ row.phone || '-' }}</small>
            </template>
          </el-table-column>
          <el-table-column label="角色" width="84">
            <template #default="{ row }">
              <el-tag size="small">{{ roleMap[row.role] || row.role }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="76">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
                {{ row.status === 'active' ? '正常' : '冻结' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="190">
            <template #default="{ row }">
              <el-button text size="small" type="primary" @click="edit(row)">编辑</el-button>
              <el-button text size="small" @click="toggleStatus(row)">
                {{ row.status === 'active' ? '冻结' : '解冻' }}
              </el-button>
              <el-button text size="small" type="danger" @click="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="form-card" :header="editing ? `编辑账号 #${form.id}` : '新建账号'">
        <el-form label-position="top" size="default">
          <el-form-item label="用户名">
            <el-input v-model="form.username" :disabled="editing" />
          </el-form-item>
          <el-form-item :label="editing ? '密码（留空则不修改）' : '初始密码'">
            <el-input v-model="form.password" type="password" show-password />
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="form.role" style="width: 100%">
              <el-option label="管理员" value="admin" />
              <el-option label="运维员" value="operator" />
              <el-option label="观察员" value="viewer" />
            </el-select>
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="form.full_name" />
          </el-form-item>
          <el-form-item label="部门">
            <el-input v-model="form.department" />
          </el-form-item>
          <el-form-item label="电话">
            <el-input v-model="form.phone" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="form.email" />
          </el-form-item>
          <el-form-item label="状态">
            <el-radio-group v-model="form.status">
              <el-radio value="active">正常</el-radio>
              <el-radio value="frozen">冻结</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
        <div class="actions">
          <el-button type="primary" :loading="saving" @click="save">
            {{ editing ? '保存修改' : '创建账号' }}
          </el-button>
          <el-button @click="resetForm">清空</el-button>
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
  grid-template-columns: minmax(0, 1.7fr) minmax(0, 1fr);
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
.actions {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}
@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
