<template>
  <el-card shadow="hover" class="contract-card">
    <template #header>
      <div class="card-header">
        <strong>{{ contract.community }} · 合同 {{ contract.id }}</strong>
        <el-tag :type="contractTagType">{{ contract.status }}</el-tag>
      </div>
    </template>

    <p class="line">{{ contract.tenantName }}（租客） / {{ contract.landlordName }}（房东）</p>
    <p class="line">{{ contract.startDate }} 至 {{ contract.endDate }}</p>
    <p class="rent">¥{{ contract.rent }}/月</p>
    <p v-if="contract.renewedFromId" class="from">由合同 {{ contract.renewedFromId }} 续租生成</p>

    <div v-if="contract.renewal" class="renewal">
      <div class="renewal-head">
        <el-tag size="small" :type="renewalTagType">{{ contract.renewal.status }}</el-tag>
        <span class="term">
          新租期 {{ contract.renewal.startDate }} ~ {{ contract.renewal.endDate }}
        </span>
      </div>
      <p class="rent-negotiation">
        期望月租 ¥{{ contract.renewal.expectedRent }}
        <span v-if="contract.renewal.rent !== contract.renewal.expectedRent">
          → 当前协商月租 <b>¥{{ contract.renewal.rent }}</b>
        </span>
      </p>

      <el-alert
        v-if="contract.renewal.status === '已续租' && contract.renewal.newContractId"
        type="success"
        :closable="false"
        :title="`续租成功，已生成下一份合同 #${contract.renewal.newContractId}`"
        class="alert"
      />

      <el-timeline class="timeline">
        <el-timeline-item
          v-for="event in contract.renewal.events"
          :key="event.id"
          :timestamp="`${event.actorRole} · ${event.createdAt}`"
          placement="top"
        >
          {{ event.action }}<template v-if="event.rent">（¥{{ event.rent }}/月）</template>
          <span v-if="event.note" class="note">{{ event.note }}</span>
        </el-timeline-item>
      </el-timeline>

      <!-- 租客视角 -->
      <template v-if="role === '租客'">
        <template v-if="contract.renewal.status === '待租客确认'">
          <el-alert
            type="info"
            :closable="false"
            :title="`房东还价 ¥${contract.renewal.rent}/月，请确认是否接受`"
            class="alert"
          />
          <el-button type="primary" @click="emit('confirm-renewal', { id: contract.renewal!.id, action: 'confirm' })">
            确认接受
          </el-button>
          <el-button @click="emit('confirm-renewal', { id: contract.renewal!.id, action: 'cancel' })">
            取消续租
          </el-button>
        </template>
        <el-button
          v-else-if="contract.renewal.status === '待房东处理'"
          @click="emit('confirm-renewal', { id: contract.renewal!.id, action: 'cancel' })"
        >
          取消申请
        </el-button>
      </template>

      <!-- 房东视角 -->
      <template v-else-if="role === '房东' && contract.renewal.status === '待房东处理'">
        <el-button type="primary" @click="accept">接受</el-button>
        <el-popover :width="260" trigger="click" @show="counterRent = contract.renewal!.rent">
          <template #reference>
            <el-button type="warning">还价</el-button>
          </template>
          <div class="counter">
            <p>新的期望月租（元/月）</p>
            <el-input-number v-model="counterRent" :min="1" :step="100" :precision="0" />
            <div class="counter-actions">
              <el-button size="small" @click="sendCounter">提交还价</el-button>
            </div>
          </div>
        </el-popover>
        <el-button type="danger" @click="emit('respond', { id: contract.renewal!.id, action: 'reject' })">
          拒绝
        </el-button>
      </template>
    </div>

    <!-- 租客从合同卡片发起续租 -->
    <el-button
      v-else-if="role === '租客' && canStartRenewal"
      type="primary"
      class="full"
      @click="emit('start-renewal', contract)"
    >
      发起续租
    </el-button>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { ContractItem, Renewal } from '../types/domain';

const props = defineProps<{ contract: ContractItem; role: '房东' | '租客' }>();
const emit = defineEmits<{
  'start-renewal': [contract: ContractItem];
  respond: [payload: { id: number; action: 'accept' | 'counter' | 'reject'; rent?: number }];
  'confirm-renewal': [payload: { id: number; action: 'confirm' | 'cancel' }];
}>();

const counterRent = ref(0);

const canStartRenewal = computed(
  () => props.contract.status === '生效中' && props.contract.renewal === null,
);

const renewalTagType = computed(() => {
  const map: Record<Renewal['status'], 'primary' | 'warning' | 'success' | 'info'> = {
    待房东处理: 'warning',
    待租客确认: 'primary',
    已续租: 'success',
    已取消: 'info',
  };
  return props.contract.renewal ? map[props.contract.renewal.status] : 'info';
});

const contractTagType = computed(() => {
  const map: Record<ContractItem['status'], 'primary' | 'info' | 'success' | 'danger'> = {
    生效中: 'primary',
    已到期: 'info',
    已续租: 'success',
    已取消: 'danger',
  };
  return map[props.contract.status];
});

function accept() {
  emit('respond', { id: props.contract.renewal!.id, action: 'accept' });
}

function sendCounter() {
  emit('respond', { id: props.contract.renewal!.id, action: 'counter', rent: counterRent.value });
}
</script>

<style scoped>
.contract-card { margin-bottom: 16px; }
.line { margin: 4px 0; color: #4b5563; }
.rent { color: #d4380d; font-weight: 700; margin: 8px 0; }
.from { font-size: 12px; color: #16a34a; margin: 4px 0; }
.renewal { border-top: 1px dashed #d7dee8; margin-top: 12px; padding-top: 12px; }
.renewal-head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.term { font-size: 13px; color: #4b5563; }
.rent-negotiation { font-size: 13px; margin: 6px 0; }
.timeline { margin: 12px 0 12px 4px; }
.note { color: #6b7280; margin-left: 6px; }
.alert { margin: 10px 0; }
.counter p { margin: 0 0 8px; }
.counter-actions { margin-top: 10px; text-align: right; }
.full { width: 100%; margin-top: 12px; }
</style>
