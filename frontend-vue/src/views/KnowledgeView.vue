<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listFaqs, createFaq, updateFaq, deleteFaq } from '@/api'
import type { Faq } from '@/api/types'

const faqs = ref<Faq[]>([])
const loading = ref(false)

const emptyForm = () => ({ id: 0, question: '', answer: '', tags: '' })
const form = reactive(emptyForm())
const editing = ref(false)
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    faqs.value = await listFaqs()
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

function edit(row: Faq) {
  Object.assign(form, { id: row.id, question: row.question, answer: row.answer, tags: row.tags.join(', ') })
  editing.value = true
}

function parseTags(raw: string): string[] {
  return raw.split(',').map((t) => t.trim()).filter(Boolean)
}

async function save() {
  if (form.question.trim().length < 3 || form.answer.trim().length < 3) {
    ElMessage.warning('问题和答案至少 3 个字符')
    return
  }
  saving.value = true
  try {
    const payload = { question: form.question.trim(), answer: form.answer.trim(), tags: parseTags(form.tags) }
    if (editing.value) {
      await updateFaq(form.id, payload)
      ElMessage.success('FAQ 已更新')
    } else {
      await createFaq(payload)
      ElMessage.success('FAQ 已创建')
    }
    resetForm()
    load()
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    saving.value = false
  }
}

async function remove(row: Faq) {
  try {
    await ElMessageBox.confirm(`确定删除 FAQ #${row.id} 吗？`, '删除 FAQ', {
      type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteFaq(row.id)
    ElMessage.success('FAQ 已删除')
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
      <h2 class="page-title">私有知识库</h2>
      <p class="page-sub">维护 FAQ 问答对，修改后向量索引会自动重建</p>
    </div>

    <div class="layout">
      <el-card class="list-card">
        <template #header>
          <div class="card-head">
            <span>FAQ 列表（{{ faqs.length }}）</span>
            <el-button text :loading="loading" @click="load">刷新</el-button>
          </div>
        </template>
        <el-table :data="faqs" v-loading="loading" empty-text="暂无 FAQ" size="small" style="width: 100%">
          <el-table-column prop="id" label="#" width="50" />
          <el-table-column prop="question" label="问题" min-width="160" show-overflow-tooltip />
          <el-table-column prop="answer" label="答案" min-width="200" show-overflow-tooltip />
          <el-table-column label="标签" width="150">
            <template #default="{ row }">
              <el-tag v-for="t in row.tags" :key="t" size="small" class="tag">{{ t }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="130">
            <template #default="{ row }">
              <el-button text size="small" type="primary" @click="edit(row)">编辑</el-button>
              <el-button text size="small" type="danger" @click="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="form-card" :header="editing ? `编辑 FAQ #${form.id}` : '新建 FAQ'">
        <el-form label-position="top">
          <el-form-item label="问题">
            <el-input v-model="form.question" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="答案">
            <el-input v-model="form.answer" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item label="标签（英文逗号分隔）">
            <el-input v-model="form.tags" placeholder="账号, 网络, VPN" />
          </el-form-item>
        </el-form>
        <div class="actions">
          <el-button type="primary" :loading="saving" @click="save">
            {{ editing ? '保存修改' : '创建 FAQ' }}
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
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tag {
  margin: 0 4px 4px 0;
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
