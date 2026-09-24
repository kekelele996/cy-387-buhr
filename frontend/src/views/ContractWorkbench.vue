<template>
  <section class="contracts">
    <div class="bench-head">
      <div>
        <h2>{{ currentIdentity.role === 'tenant' ? '租客' : '房东' }}工作台 · 合同与续租</h2>
        <p>从合同卡片发起续租：房东可接受、还价或拒绝，改价后由租客确认。</p>
      </div>
      <el-radio-group :model-value="currentIdentity.label" size="small" @change="onSwitch">
        <el-radio-button v-for="identity in IDENTITIES" :key="identity.label" :label="identity.label">
          {{ identity.label }}
        </el-radio-button>
      </el-radio-group>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="hint"
      title="演示身份通过请求头模拟；同一身份在两个标签页里看到的合同与协商记录一致。"
    />

    <el-skeleton :loading="loading" :rows="6" animated>
      <el-empty v-if="!contracts.length" description="暂无合同" />
      <ContractCard
        v-for="contract in contracts"
        :key="contract.id"
        :contract="contract"
        @changed="fetchContracts"
      />
    </el-skeleton>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { getContracts } from '../api/client';
import { IDENTITIES, currentIdentity, switchIdentity } from '../state/identity';
import type { ContractItem } from '../types/domain';
import ContractCard from '../components/renewal/ContractCard.vue';

const contracts = ref<ContractItem[]>([]);
const loading = ref(false);

async function fetchContracts() {
  loading.value = true;
  try {
    contracts.value = await getContracts();
  } catch {
    ElMessage.error('合同加载失败');
  } finally {
    loading.value = false;
  }
}

function onSwitch(label: string | number | boolean) {
  const identity = IDENTITIES.find((item) => item.label === label);
  if (identity) {
    switchIdentity(identity);
    fetchContracts();
  }
}

onMounted(fetchContracts);
</script>

<style scoped>
.bench-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; margin-bottom: 16px; }
.hint { margin-bottom: 16px; }
</style>
