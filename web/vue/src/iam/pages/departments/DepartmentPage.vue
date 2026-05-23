<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { addDepartmentUser, removeDepartmentUser } from "@/iam/api/department";
import { useDepartmentStore } from "@/iam/stores/department";
import type { CreateDepartmentParams, Department, UpdateDepartmentParams } from "@/iam/types";
import { confirmAction, getErrorMessage, notifyError, notifySuccess } from "@/iam/utils/feedback";

const departmentStore = useDepartmentStore();

const dialogVisible = ref(false);
const dialogTitle = ref("");
const isEdit = ref(false);
const currentDepartmentId = ref<string | null>(null);
const leaderId = ref("");
const savingLeader = ref(false);
const usersLoading = ref(false);
const addUserId = ref("");
const addUserAsLeader = ref(false);
const addingUser = ref(false);
const removingUserId = ref<string | null>(null);

const form = ref<CreateDepartmentParams & UpdateDepartmentParams>({
  name: "",
  code: "",
  parent_id: undefined,
  sort_order: 0,
  leader_id: undefined,
});

const formRules = {
  name: [{ required: true, message: "请输入部门名称", trigger: "blur" }],
};

const formRef = ref();

const flattenDepartments = (departments: Department[]): Department[] =>
  departments.flatMap((dept) => [dept, ...flattenDepartments(dept.children || [])]);

const selectedDepartment = computed(() => {
  if (!currentDepartmentId.value) return null;
  return flattenDepartments(departmentStore.departmentTree).find(
    (dept) => dept.id === currentDepartmentId.value
  ) || null;
});

const loadDepartments = async () => {
  await departmentStore.fetchDepartmentTree();
};

const loadDepartmentUsers = async () => {
  if (!currentDepartmentId.value) return;

  usersLoading.value = true;
  try {
    await departmentStore.fetchUsers(currentDepartmentId.value);
  } finally {
    usersLoading.value = false;
  }
};

const handleNodeClick = async (data: Department) => {
  currentDepartmentId.value = data.id;
  leaderId.value = data.leader_id || "";
  addUserId.value = "";
  addUserAsLeader.value = false;
  await loadDepartmentUsers();
};

const handleAdd = () => {
  isEdit.value = false;
  dialogTitle.value = "新增部门";
  form.value = {
    name: "",
    code: "",
    parent_id: undefined,
    sort_order: 0,
    leader_id: undefined,
  };
  dialogVisible.value = true;
};

const handleEdit = () => {
  if (!selectedDepartment.value) return;

  const dept = selectedDepartment.value;
  isEdit.value = true;
  dialogTitle.value = "编辑部门";
  form.value = {
    name: dept.name,
    code: dept.code || "",
    parent_id: dept.parent_id,
    sort_order: dept.sort_order,
    leader_id: dept.leader_id,
  };
  dialogVisible.value = true;
};

const handleDelete = async () => {
  if (!currentDepartmentId.value) return;
  if (!confirmAction("确定要删除该部门吗？")) return;

  try {
    await departmentStore.removeDepartment(currentDepartmentId.value);
    currentDepartmentId.value = null;
    leaderId.value = "";
    departmentStore.departmentUsers = [];
    notifySuccess("删除成功");
  } catch (error) {
    notifyError(getErrorMessage(error, "删除失败"));
  }
};

const handleSubmit = async () => {
  const valid = await formRef.value?.validate();
  if (!valid) return;

  try {
    if (isEdit.value && currentDepartmentId.value) {
      await departmentStore.editDepartment(currentDepartmentId.value, form.value);
      leaderId.value = form.value.leader_id || "";
      notifySuccess("更新成功");
    } else {
      await departmentStore.addDepartment(form.value);
      notifySuccess("创建成功");
    }
    dialogVisible.value = false;
    await loadDepartments();
  } catch (error) {
    notifyError(getErrorMessage(error, "操作失败"));
  }
};

const handleSaveLeader = async () => {
  if (!currentDepartmentId.value) return;

  savingLeader.value = true;
  try {
    await departmentStore.updateLeader(currentDepartmentId.value, leaderId.value);
    await loadDepartments();
    notifySuccess("负责人保存成功");
  } catch (error) {
    notifyError(getErrorMessage(error, "负责人保存失败"));
  } finally {
    savingLeader.value = false;
  }
};

const handleAddDepartmentUser = async () => {
  if (!currentDepartmentId.value || !addUserId.value.trim()) return;

  addingUser.value = true;
  try {
    await addDepartmentUser(
      currentDepartmentId.value,
      addUserId.value.trim(),
      addUserAsLeader.value
    );
    addUserId.value = "";
    addUserAsLeader.value = false;
    await Promise.all([loadDepartmentUsers(), loadDepartments()]);
    notifySuccess("添加部门用户成功");
  } catch (error) {
    notifyError(getErrorMessage(error, "添加部门用户失败"));
  } finally {
    addingUser.value = false;
  }
};

const handleRemoveDepartmentUser = async (userId: string) => {
  if (!currentDepartmentId.value) return;
  if (!confirmAction("确定要从该部门移除用户吗？")) return;

  removingUserId.value = userId;
  try {
    await removeDepartmentUser(currentDepartmentId.value, userId);
    await Promise.all([loadDepartmentUsers(), loadDepartments()]);
    notifySuccess("移除部门用户成功");
  } catch (error) {
    notifyError(getErrorMessage(error, "移除部门用户失败"));
  } finally {
    removingUserId.value = null;
  }
};

onMounted(() => {
  loadDepartments();
});
</script>

<template>
  <div class="department-page">
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <div class="tree-header">
              <span>部门结构</span>
              <el-button type="primary" size="small" @click="handleAdd">新增</el-button>
            </div>
          </template>

          <el-tree
            :data="departmentStore.departmentTree"
            :props="{ children: 'children', label: 'name' }"
            node-key="id"
            default-expand-all
            @node-click="handleNodeClick"
          />
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <span>部门详情</span>
          </template>

          <template v-if="selectedDepartment">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="部门名称">
                {{ selectedDepartment.name }}
              </el-descriptions-item>
              <el-descriptions-item label="部门编码">
                {{ selectedDepartment.code || "-" }}
              </el-descriptions-item>
              <el-descriptions-item label="排序号">
                {{ selectedDepartment.sort_order }}
              </el-descriptions-item>
              <el-descriptions-item label="负责人">
                {{ selectedDepartment.leader_id || "未设置" }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="dept-actions">
              <el-button type="primary" @click="handleEdit">编辑</el-button>
              <el-button type="danger" @click="handleDelete">删除</el-button>
            </div>

            <el-divider />

            <div class="leader-section">
              <div class="section-title">负责人设置</div>
              <el-input
                v-model="leaderId"
                placeholder="请输入负责人用户 ID"
                clearable
                class="leader-input"
              />
              <el-button type="primary" :loading="savingLeader" @click="handleSaveLeader">
                保存负责人
              </el-button>
            </div>

            <el-divider />

            <div class="users-section">
              <div class="section-header">
                <div>
                  <div class="section-title">部门用户</div>
                  <div class="section-desc">展示当前部门用户，支持添加、移除和刷新用户列表。</div>
                </div>
                <el-button :loading="usersLoading" @click="loadDepartmentUsers">刷新</el-button>
              </div>

              <div class="add-user-form">
                <el-input
                  v-model="addUserId"
                  placeholder="请输入用户 ID"
                  clearable
                  class="user-id-input"
                />
                <el-checkbox v-model="addUserAsLeader">设为负责人</el-checkbox>
                <el-button
                  type="primary"
                  :loading="addingUser"
                  :disabled="!addUserId.trim()"
                  @click="handleAddDepartmentUser"
                >
                  添加用户
                </el-button>
              </div>

              <el-table
                :data="departmentStore.departmentUsers"
                stripe
                v-loading="usersLoading"
                class="users-table"
              >
                <el-table-column prop="username" label="用户名" min-width="140" />
                <el-table-column prop="nickname" label="昵称" min-width="140">
                  <template #default="{ row }">
                    {{ row.nickname || "-" }}
                  </template>
                </el-table-column>
                <el-table-column label="负责人" width="100">
                  <template #default="{ row }">
                    <el-tag v-if="row.id === selectedDepartment?.leader_id" type="success">是</el-tag>
                    <el-tag v-else type="info">否</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button
                      type="danger"
                      link
                      :loading="removingUserId === row.id"
                      @click="handleRemoveDepartmentUser(row.id)"
                    >
                      移除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>

          <el-empty v-else description="请选择部门" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="部门编码" prop="code">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item label="排序号" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.department-page {
  padding: 16px;
}

.tree-header,
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.dept-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.leader-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.leader-input {
  max-width: 360px;
}

.section-title {
  font-size: 15px;
  font-weight: 500;
}

.section-desc {
  margin-top: 4px;
  color: #909399;
  font-size: 13px;
}

.users-table {
  margin-top: 12px;
}

.add-user-form {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.user-id-input {
  max-width: 320px;
}
</style>
