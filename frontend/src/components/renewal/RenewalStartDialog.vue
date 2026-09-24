<template>
  <el-dialog v-model="visible" title="发起续租" width="420px" @closed="onClosed">
    <el-form v-if="contract" label-width="92px">
      <el-form-item label="当前合同">
        <span>{{ contract.community }} · {{ contract.layout }}，月租 ¥{{ contract.rent }}</span>
      </el-form-item>
      <el-form-item label="新租期" required>
        <el-date-picker
          v-model="startDate" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" class="date"
        />
        <span class="dash">至</span>
        <el-date-picker
          v-model="endDate" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" class="date"
        />
      </el-form-item>
      <el-form-item label="期望月租" required>
        <el-input-number v-model="rent" :min="100" :step="100" :max="100000" />
        <span class="unit">元/月</span>
      </el-form-item>
      <el-form-item label="附言">
        <el-input v-model="message" maxlength="200" placeholder="想对房东说的话（选填）" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">提交续租申请</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { startRenewal } from '../../api/client';
import type { ContractItem, RenewalRequest } from '../../types/domain';

const props = defineProps<{ contract: ContractItem | null }>();
const emit = defineEmits<{ submitted: [renewal: RenewalRequest] }>();

const visible = ref(false);
const submitting = ref(false);
const startDate = ref('');
const endDate = ref('');
const rent = ref(0);
const message = ref('');

function open() {
  if (!props.contract) return;
  startDate.value = '';
  endDate.value = '';
  rent.value = props.contract.rent;
  message.value = '';
  visible.value = true;
}

defineExpose({ open });

async function submit() {
  if (!props.contract) return;
  if (!startDate.value || !endDate.value) {
    ElMessage.warning('请填写新租期');
    return;
  }
  if (startDate.value >= endDate.value) {
    ElMessage.warning('租期结束日期需晚于开始日期');
    return;
  }
  submitting.value = true;
  try {
    const renewal = await startRenewal(props.contract.id, {
      newStartDate: startDate.value,
      newEndDate: endDate.value,
      proposedRent: rent.value,
      message: message.value || undefined,
    });
    ElMessage.success('续租申请已发给房东');
    visible.value = false;
    emit('submitted', renewal);
  } finally {
    submitting.value = false;
  }
}

function onClosed() {
  startDate.value = '';
  endDate.value = '';
}
</script>

<style scoped>
.date { width: 150px; }
.dash { margin: 0 8px; color: #667085; }
.unit { margin-left: 8px; color: #667085; }
</style>
