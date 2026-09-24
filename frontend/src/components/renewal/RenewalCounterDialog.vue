<template>
  <el-dialog v-model="visible" title="房东还价" width="400px" @closed="onClosed">
    <el-form v-if="renewal" label-width="92px">
      <el-form-item label="租客报价">
        <span>¥{{ renewal.proposedRent }}/月（现租金 ¥{{ renewal.currentRent }}）</span>
      </el-form-item>
      <el-form-item label="新租期">
        <span>{{ renewal.newStartDate }} 至 {{ renewal.newEndDate }}</span>
      </el-form-item>
      <el-form-item label="还价月租" required>
        <el-input-number v-model="rent" :min="100" :step="100" :max="100000" />
        <span class="unit">元/月</span>
      </el-form-item>
      <el-form-item label="说明">
        <el-input v-model="note" maxlength="200" placeholder="还价理由（选填）" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="warning" :loading="submitting" @click="submit">发出还价</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { renewalAction } from '../../api/client';
import type { RenewalRequest } from '../../types/domain';

const props = defineProps<{ renewal: RenewalRequest | null }>();
const emit = defineEmits<{ done: [renewal: RenewalRequest] }>();

const visible = ref(false);
const submitting = ref(false);
const rent = ref(0);
const note = ref('');

function open() {
  if (!props.renewal) return;
  rent.value = props.renewal.proposedRent;
  note.value = '';
  visible.value = true;
}

defineExpose({ open });

async function submit() {
  if (!props.renewal) return;
  submitting.value = true;
  try {
    const renewal = await renewalAction(props.renewal.id, 'counter', {
      proposedRent: rent.value,
      note: note.value || undefined,
    });
    ElMessage.success('已还价，等待租客确认');
    visible.value = false;
    emit('done', renewal);
  } finally {
    submitting.value = false;
  }
}

function onClosed() {
  note.value = '';
}
</script>

<style scoped>
.unit { margin-left: 8px; color: #667085; }
</style>
