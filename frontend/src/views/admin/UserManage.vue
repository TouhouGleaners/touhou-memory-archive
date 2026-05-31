<template>
  <div class="user-manage">
    <div class="header">
      <h3>用户管理</h3>
      <Button label="添加用户" icon="pi pi-plus" @click="showCreate = true" />
    </div>
    <Toast />
    <ConfirmDialog />

    <DataTable :value="users" :loading="loading" stripedRows emptyMessage="暂无用户">
      <Column field="id" header="ID" style="width: 60px" />
      <Column field="username" header="用户名" />
      <Column field="role" header="角色" style="width: 120px">
        <template #body="{ data }">
          <Tag :value="roleLabel(data.role)" :severity="data.role === AdminRole.SUPERADMIN ? 'success' : 'info'" />
        </template>
      </Column>
      <Column field="is_active" header="状态" style="width: 100px">
        <template #body="{ data }">
          <Tag :value="data.is_active ? '启用' : '禁用'" :severity="data.is_active ? 'success' : 'danger'" />
        </template>
      </Column>
      <Column header="操作" style="width: 200px">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" text size="small" @click="startEdit(data)" />
          <Button
            :icon="data.is_active ? 'pi pi-ban' : 'pi pi-check'"
            text
            size="small"
            :severity="data.is_active ? 'danger' : 'success'"
            :disabled="togglingId === data.id"
            @click="toggleActive(data)"
          />
          <Button icon="pi pi-trash" text size="small" severity="danger" @click="confirmDelete(data)" />
        </template>
      </Column>
    </DataTable>

    <!-- 创建用户对话框 -->
    <Dialog v-model:visible="showCreate" modal header="添加用户" :style="{ width: '360px' }">
      <div class="form-grid">
        <label>用户名</label>
        <InputText v-model="form.username" fluid />
        <label>密码</label>
        <Password v-model="form.password" :feedback="false" toggleMask fluid />
        <label>角色</label>
        <Select v-model="form.role" :options="roleOptions" optionLabel="label" optionValue="value" fluid />
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" text @click="showCreate = false" />
        <Button label="创建" :loading="saving" @click="handleCreate" />
      </template>
    </Dialog>

    <!-- 编辑用户对话框 -->
    <Dialog v-model:visible="showEdit" modal header="编辑用户" :style="{ width: '360px' }">
      <div class="form-grid">
        <label>用户名</label>
        <InputText :modelValue="editingUser?.username" disabled fluid />
        <label>角色</label>
        <Select v-model="editForm.role" :options="roleOptions" optionLabel="label" optionValue="value" fluid />
        <label>新密码（留空不修改）</label>
        <Password v-model="editForm.password" :feedback="false" toggleMask fluid />
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" text @click="showEdit = false" />
        <Button label="保存" :loading="saving" @click="handleEdit" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import { apiGet, apiPost, apiPatch, apiDelete } from '../../api/client'

interface AdminUser {
  id: number
  username: string
  role: AdminRole
  is_active: boolean
  created_at: number
}

// 与后端 AdminRole IntEnum 保持一致
enum AdminRole {
  SUPERADMIN = 1,
  ADMIN = 2,
}

const toast = useToast()
const confirm = useConfirm()
const users = ref<AdminUser[]>([])
const loading = ref(true)
const saving = ref(false)
const togglingId = ref<number | null>(null)

const showCreate = ref(false)
const showEdit = ref(false)
const editingUser = ref<AdminUser | null>(null)

const form = ref({ username: '', password: '', role: AdminRole.ADMIN })
const editForm = ref({ role: AdminRole.ADMIN, password: '' })

const roleOptions = [
  { label: '超级管理员', value: AdminRole.SUPERADMIN },
  { label: '管理员', value: AdminRole.ADMIN },
]

function roleLabel(role: number) {
  return role === AdminRole.SUPERADMIN ? '超级管理员' : '管理员'
}

async function loadUsers() {
  loading.value = true
  try {
    users.value = await apiGet<AdminUser[]>('/admin/users')
  } catch (e) {
    toast.add({ severity: 'error', summary: '加载失败', detail: e instanceof Error ? e.message : '未知错误', life: 5000 })
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  saving.value = true
  try {
    await apiPost('/admin/users', form.value)
    toast.add({ severity: 'success', summary: '创建成功', life: 3000 })
    showCreate.value = false
    form.value = { username: '', password: '', role: AdminRole.ADMIN }
    await loadUsers()
  } catch (e) {
    toast.add({ severity: 'error', summary: '创建失败', detail: e instanceof Error ? e.message : '未知错误', life: 5000 })
  } finally {
    saving.value = false
  }
}

function startEdit(user: AdminUser) {
  editingUser.value = user
  editForm.value = { role: user.role, password: '' }
  showEdit.value = true
}

async function handleEdit() {
  if (!editingUser.value) return
  saving.value = true
  try {
    const body: { role?: number; password?: string } = { role: editForm.value.role }
    if (editForm.value.password) body.password = editForm.value.password
    await apiPatch(`/admin/users/${editingUser.value.id}`, body)
    toast.add({ severity: 'success', summary: '修改成功', life: 3000 })
    showEdit.value = false
    await loadUsers()
  } catch (e) {
    toast.add({ severity: 'error', summary: '修改失败', detail: e instanceof Error ? e.message : '未知错误', life: 5000 })
  } finally {
    saving.value = false
  }
}

async function toggleActive(user: AdminUser) {
  if (togglingId.value) return
  togglingId.value = user.id
  try {
    await apiPatch(`/admin/users/${user.id}`, { is_active: !user.is_active })
    toast.add({ severity: 'success', summary: user.is_active ? '已禁用' : '已启用', life: 3000 })
    await loadUsers()
  } catch (e) {
    toast.add({ severity: 'error', summary: '操作失败', detail: e instanceof Error ? e.message : '未知错误', life: 5000 })
  } finally {
    togglingId.value = null
  }
}

function confirmDelete(user: AdminUser) {
  confirm.require({
    message: `确定要删除用户 ${user.username} 吗？`,
    header: '确认删除',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: '取消',
    acceptLabel: '删除',
    rejectClass: 'p-button-secondary p-button-outlined',
    acceptClass: 'p-button-danger',
    accept: () => handleDelete(user),
  })
}

async function handleDelete(user: AdminUser) {
  try {
    await apiDelete(`/admin/users/${user.id}`)
    toast.add({ severity: 'success', summary: '已删除', life: 3000 })
    await loadUsers()
  } catch (e) {
    toast.add({ severity: 'error', summary: '删除失败', detail: e instanceof Error ? e.message : '未知错误', life: 5000 })
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.header h3 {
  margin: 0;
  color: var(--text-color);
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-grid label {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
  margin-top: 0.5rem;
}
</style>
