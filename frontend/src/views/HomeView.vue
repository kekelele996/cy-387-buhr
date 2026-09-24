<template>
  <main class="page">
    <section class="toolbar">
      <div>
        <h1>RentFind 租房平台</h1>
        <p>房源搜索、合同续租协商和物业报修集中处理。当前身份：<strong>{{ currentIdentity.label }}</strong></p>
      </div>
      <el-segmented v-model="tab" :options="['房源', '合同续租']" />
    </section>

    <template v-if="tab === '房源'">
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

      <section v-if="mode === '地图视图'" class="map-panel">
        高德地图区域：按经纬度展示房源点位，当前示例加载 {{ filtered.length }} 套房源。
      </section>
      <div class="view-switch">
        <el-segmented v-model="mode" :options="['列表视图', '地图视图']" size="small" />
      </div>
      <section class="grid">
        <PropertyCard v-for="item in filtered" :key="item.id" :item="item" />
      </section>

      <section class="repair">
        <h2 class="repair-title">物业报修</h2>
        <el-select v-model="faultType">
          <el-option v-for="type in repairTypes" :key="type" :label="type" :value="type" />
        </el-select>
        <el-input v-model="description" placeholder="描述故障情况" />
        <el-button type="success" @click="submitRepair">提交工单</el-button>
        <span>{{ notice }}</span>
      </section>
    </template>

    <ContractWorkbench v-else />
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import PropertyCard from '../components/PropertyCard.vue';
import ContractWorkbench from './ContractWorkbench.vue';
import { createRepair, getProperties } from '../api/client';
import { currentIdentity } from '../state/identity';
import type { PropertyItem } from '../types/domain';
import { REPAIR_TYPES } from '../constants/repair';

const properties = ref<PropertyItem[]>([]);
const tab = ref('房源');
const mode = ref('列表视图');
const region = ref('');
const maxRent = ref(7000);
const layout = ref('全部');
const faultType = ref(REPAIR_TYPES[0]);
const repairTypes = REPAIR_TYPES;
const description = ref('');
const notice = ref('等待提交');

onMounted(async () => {
  try {
    properties.value = await getProperties();
  } catch {
    ElMessage.error('房源加载失败');
  }
});

const filtered = computed(() => properties.value.filter((item) => {
  const hitRegion = !region.value || item.region.includes(region.value);
  const hitRent = item.rent <= maxRent.value;
  const hitLayout = layout.value === '全部' || item.layout === layout.value;
  return hitRegion && hitRent && hitLayout;
}));

async function submitRepair() {
  try {
    const ticket = await createRepair({ faultType: faultType.value, description: description.value });
    notice.value = `工单 ${ticket.id} 已提交：${ticket.status}`;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '报修提交失败');
  }
}
</script>
