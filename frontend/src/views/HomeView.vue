<template>
  <main class="page">
    <section class="toolbar">
      <div>
        <h1>RentFind 租房平台</h1>
        <p>房源搜索、预约看房、合同管理和物业报修集中处理。</p>
      </div>
      <el-segmented v-model="mode" :options="['列表视图', '地图视图']" />
    </section>

    <section class="filters">
      <el-input v-model="region" placeholder="区域" />
      <el-input-number v-model="maxRent" :min="1000" :step="500" />
      <el-select v-model="layout" placeholder="户型">
        <el-option label="全部" value="全部" />
        <el-option label="一室一厅" value="一室一厅" />
        <el-option label="两室一厅" value="两室一厅" />
        <el-option label="三室两厅" value="三室两厅" />
      </el-select>
    </section>

    <section v-if="mode === '地图视图'" class="map-panel">高德地图区域：按经纬度展示房源点位，当前示例加载 {{ filtered.length }} 套房源。</section>
    <section class="grid">
      <PropertyCard v-for="item in filtered" :key="item.id" :item="item" />
    </section>

    <section class="renewal-section">
      <div class="section-head">
        <h2>合同续租</h2>
        <el-radio-group v-model="role" size="small">
          <el-radio-button value="租客">租客视角</el-radio-button>
          <el-radio-button value="房东">房东视角</el-radio-button>
        </el-radio-group>
      </div>
      <p class="hint">合同快到期时从卡片发起续租，房东可接受、还价或拒绝；新租期与同一房源其他有效合同重叠时会说明冲突。</p>
      <div class="contract-grid">
        <ContractCard
          v-for="contract in contracts"
          :key="contract.id"
          :contract="contract"
          :role="role"
          @start-renewal="openRenewalDialog"
          @respond="handleRespond"
          @confirm-renewal="handleConfirm"
        />
      </div>
    </section>

    <section class="repair">
      <h2>物业报修</h2>
      <el-select v-model="faultType">
        <el-option label="水电" value="水电" />
        <el-option label="门锁" value="门锁" />
        <el-option label="管道" value="管道" />
        <el-option label="家电" value="家电" />
        <el-option label="其他" value="其他" />
      </el-select>
      <el-input v-model="description" placeholder="描述故障情况" />
      <el-button type="success" @click="submitRepair">提交工单</el-button>
      <span>{{ notice }}</span>
    </section>

    <RenewalDialog
      v-if="activeContract"
      v-model="dialogVisible"
      :contract="activeContract"
      @submit="handleCreateRenewal"
    />
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import PropertyCard from '../components/PropertyCard.vue';
import ContractCard from '../components/ContractCard.vue';
import RenewalDialog from '../components/RenewalDialog.vue';
import { ApiError, confirmRenewal, createRenewal, createRepair, getContracts, getProperties, respondRenewal } from '../api/client';
import type { ContractItem, PropertyItem, RenewalCreatePayload } from '../types/domain';

const properties = ref<PropertyItem[]>([]);
const contracts = ref<ContractItem[]>([]);
const mode = ref('列表视图');
const region = ref('');
const maxRent = ref(7000);
const layout = ref('全部');
const faultType = ref('水电');
const description = ref('');
const notice = ref('等待提交');

// 演示用：在租客 / 房东视角间切换，真实环境由 JWT 用户角色决定
const role = ref<'租客' | '房东'>('租客');
const dialogVisible = ref(false);
const activeContract = ref<ContractItem | null>(null);

onMounted(async () => {
  await refresh();
});

async function refresh() {
  const [propertyList, contractList] = await Promise.all([getProperties(), getContracts()]);
  properties.value = propertyList;
  contracts.value = contractList;
}

const filtered = computed(() => properties.value.filter((item) => {
  const hitRegion = !region.value || item.region.includes(region.value);
  const hitRent = item.rent <= maxRent.value;
  const hitLayout = layout.value === '全部' || item.layout === layout.value;
  return hitRegion && hitRent && hitLayout;
}));

function openRenewalDialog(contract: ContractItem) {
  activeContract.value = contract;
  dialogVisible.value = true;
}

function showError(error: unknown) {
  if (error instanceof ApiError) {
    ElMessage.error(error.message);
  } else {
    ElMessage.error('网络异常，请稍后重试');
  }
}

async function handleCreateRenewal(payload: RenewalCreatePayload) {
  if (!activeContract.value) return;
  try {
    await createRenewal(activeContract.value.id, payload, role.value);
    ElMessage.success('续租申请已发起，等待房东处理');
    await refresh();
  } catch (error) {
    showError(error);
  } finally {
    activeContract.value = null;
  }
}

async function handleRespond(payload: { id: number; action: 'accept' | 'counter' | 'reject'; rent?: number }) {
  try {
    await respondRenewal(payload.id, payload, role.value);
    ElMessage.success(payload.action === 'accept' ? '已接受续租' : payload.action === 'counter' ? '已还价，等待租客确认' : '已拒绝续租');
    await refresh();
  } catch (error) {
    showError(error);
  }
}

async function handleConfirm(payload: { id: number; action: 'confirm' | 'cancel' }) {
  try {
    await confirmRenewal(payload.id, payload.action, role.value);
    ElMessage.success(payload.action === 'confirm' ? '已确认接受，续租成功' : '已取消续租');
    await refresh();
  } catch (error) {
    showError(error);
  }
}

async function submitRepair() {
  const ticket = await createRepair({ faultType: faultType.value, description: description.value });
  notice.value = `工单 ${ticket.id} 已提交：${ticket.status}`;
}
</script>
