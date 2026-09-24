<template>
  <el-card shadow="hover" class="contract-card">
    <template #header>
      <div class="card-header">
        <strong>合同 #{{ contract.id }} · {{ contract.community }}</strong>
        <el-tag :type="contractTagType">{{ contract.status }}</el-tag>
      </div>
    </template>

    <p class="line">{{ contract.layout }} · 房东 {{ contract.landlordName }} · 租客 {{ contract.tenantName }}</p>
    <p class="line">租期：{{ contract.startDate }} 至 {{ contract.endDate }}</p>
    <p class="rent">月租 ¥{{ contract.rent }}，押金 ¥{{ contract.deposit }}</p>
    <p v-if="contract.renewedContractId" class="next-hint">
      已由下一份合同 #{{ contract.renewedContractId }} 接续，本合同不再更改。
    </p>

    <div v-if="renewal" class="renewal-panel">
      <div class="renewal-head">
        <el-tag :type="renewalTagType" size="small">{{ renewal.status }}</el-tag>
        <span class="renewal-term">
          续租 {{ renewal.newStartDate }} 至 {{ renewal.newEndDate }}，报价 ¥{{ renewal.proposedRent }}/月
        </span>
      </div>
      <p v-if="renewal.message" class="renewal-message">租客附言：{{ renewal.message }}</p>
      <p v-if="renewal.createdContractId" class="next-hint">续租成功，已生成下一份合同 #{{ renewal.createdContractId }}。</p>

      <RenewalConflictAlert v-if="conflicts.length" :conflicts="conflicts" />

      <div class="actions">
        <template v-if="canRenew">
          <el-button type="primary" size="small" @click="openStart">发起续租</el-button>
        </template>
        <template v-else-if="renewal.status === '待房东处理'">
          <template v-if="isLandlord">
            <el-button type="success" size="small" :loading="loading" @click="act('accept')">接受</el-button>
            <el-button type="warning" size="small" @click="counterDialog?.open()">还价</el-button>
            <el-button size="small" @click="reject">拒绝</el-button>
          </template>
          <template v-else>
            <span class="waiting">等待房东处理…</span>
            <el-button size="small" @click="cancelRenewal">取消续租</el-button>
          </template>
        </template>
        <template v-else-if="renewal.status === '待租客确认'">
          <template v-if="isTenant">
            <el-button type="primary" size="small" :loading="loading" @click="act('confirm')">确认续租</el-button>
            <el-button size="small" @click="cancelRenewal">取消续租</el-button>
          </template>
          <span v-else class="waiting">已还价 ¥{{ renewal.proposedRent }}，等待租客确认…</span>
        </template>
      </div>

      <el-collapse v-if="renewal.events.length" class="history">
        <el-collapse-item title="处理记录">
          <RenewalTimeline :events="renewal.events" />
        </el-collapse-item>
      </el-collapse>
    </div>

    <RenewalStartDialog
      v-if="contract"
      ref="startDialog"
      :contract="contract"
      @submitted="onChanged"
    />
    <RenewalCounterDialog
      v-if="renewal"
      ref="counterDialog"
      :renewal="renewal"
      @done="onChanged"
    />
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ApiError, renewalAction } from '../../api/client';
import { currentIdentity } from '../../state/identity';
import type { ContractItem, RenewalConflict, RenewalRequest } from '../../types/domain';
import RenewalStartDialog from './RenewalStartDialog.vue';
import RenewalCounterDialog from './RenewalCounterDialog.vue';
import RenewalTimeline from './RenewalTimeline.vue';
import RenewalConflictAlert from './RenewalConflictAlert.vue';

const props = defineProps<{ contract: ContractItem }>();
const emit = defineEmits<{ changed: [] }>();

const startDialog = ref<InstanceType<typeof RenewalStartDialog> | null>(null);
const counterDialog = ref<InstanceType<typeof RenewalCounterDialog> | null>(null);
const loading = ref(false);
const conflicts = ref<RenewalConflict[]>([]);

const renewal = computed(() => props.contract.renewal);
const isTenant = computed(() => currentIdentity.role === 'tenant');
const isLandlord = computed(() => currentIdentity.role === 'landlord');

// 仅有效合同、且没有进行中或已完成的续租协商时，卡片才提供发起入口
const canRenew = computed(
  () =>
    isTenant.value &&
    props.contract.status === '有效' &&
    (!renewal.value || renewal.value.status === '已取消'),
);

const contractTagType = computed(() =>
  props.contract.status === '有效' ? 'success' : 'info',
);
const renewalTagType = computed(() => {
  switch (renewal.value?.status) {
    case '待房东处理':
    case '待租客确认':
      return 'warning';
    case '已续租':
      return 'success';
    default:
      return 'info';
  }
});

function openStart() {
  conflicts.value = [];
  startDialog.value?.open();
}

async function onChanged() {
  conflicts.value = [];
  emit('changed');
}

async function promptNote(title: string): Promise<string> {
  try {
    const { value } = await ElMessageBox.prompt('备注（选填）', title, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputType: 'textarea',
    });
    return value?.trim() ?? '';
  } catch {
    return '__cancel__';
  }
}

async function act(action: 'accept' | 'confirm') {
  if (!renewal.value) return;
  loading.value = true;
  try {
    await renewalAction(renewal.value.id, action);
    ElMessage.success(action === 'accept' ? '房东已接受，续租完成' : '已确认，续租完成');
    await onChanged();
  } catch (error) {
    handleActionError(error);
  } finally {
    loading.value = false;
  }
}

async function reject() {
  const note = await promptNote('拒绝续租');
  if (note === '__cancel__') return;
  await runWithGuard('reject', { note }, '已拒绝');
}

async function cancelRenewal() {
  const note = await promptNote('取消续租');
  if (note === '__cancel__') return;
  await runWithGuard('cancel', { note }, '已取消续租');
}

async function runWithGuard(
  action: 'reject' | 'cancel',
  body: Record<string, unknown>,
  okText: string,
) {
  if (!renewal.value) return;
  try {
    await renewalAction(renewal.value.id, action, body);
    ElMessage.success(okText);
    await onChanged();
  } catch (error) {
    handleActionError(error);
  }
}

function handleActionError(error: unknown) {
  if (error instanceof ApiError) {
    if (error.code === 'RENEWAL_CONFLICT' && error.data?.conflicts) {
      conflicts.value = error.data.conflicts;
      ElMessage.error('新租期与其他有效合同重叠');
    } else {
      ElMessage.error(error.message);
    }
    emit('changed');
    return;
  }
  ElMessage.error('操作失败，请稍后重试');
}
</script>

<style scoped>
.contract-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.line { margin: 4px 0; color: #475467; }
.rent { color: #d4380d; font-weight: 700; margin: 8px 0; }
.next-hint { color: #667085; font-size: 13px; margin: 6px 0; }
.renewal-panel { margin-top: 12px; padding: 12px; border: 1px dashed #d0d5dd; border-radius: 8px; background: #fafbfc; }
.renewal-head { display: flex; align-items: center; gap: 10px; }
.renewal-term { font-weight: 600; }
.renewal-message { color: #475467; font-size: 13px; margin: 8px 0 0; }
.actions { margin-top: 12px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.waiting { color: #b54708; font-size: 13px; }
.history { margin-top: 10px; }
</style>
