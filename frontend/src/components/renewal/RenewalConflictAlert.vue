<template>
  <el-alert type="error" :closable="false" show-icon class="conflict-alert">
    <template #title>无法确认：新租期与同一房源的其他有效合同重叠</template>
    <div class="conflict-body">
      <p v-for="conflict in conflicts" :key="conflict.id" class="conflict-line">
        合同 #{{ conflict.id }}（租客 {{ conflict.tenantName }}）：
        {{ conflict.startDate }} 至 {{ conflict.endDate }}，月租 ¥{{ conflict.rent }}
      </p>
      <p class="tip">同一套房不能在重叠时段签给两位租客，请调整租期后再发起。</p>
    </div>
  </el-alert>
</template>

<script setup lang="ts">
import type { RenewalConflict } from '../../types/domain';

defineProps<{ conflicts: RenewalConflict[] }>();
</script>

<style scoped>
.conflict-alert { margin-top: 12px; }
.conflict-body { margin: 4px 0 0; }
.conflict-line { margin: 2px 0; }
.tip { margin: 6px 0 0; color: #9f2d20; }
</style>
