<template>
  <el-dialog title="发起续租" :model-value="modelValue" width="420px" @close="emit('update:modelValue', false)">
    <el-form label-width="92px">
      <el-form-item label="当前到期">
        <span>{{ contract.endDate }}</span>
      </el-form-item>
      <el-form-item label="新租期" required>
        <el-date-picker
          v-model="term"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :disabled-date="disableBeforeEnd"
        />
      </el-form-item>
      <el-form-item label="期望月租" required>
        <el-input-number v-model="expectedRent" :min="1" :step="100" :precision="0" />
        <span class="unit">元/月</span>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">提交续租申请</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { ContractItem, RenewalCreatePayload } from '../types/domain';

const props = defineProps<{ modelValue: boolean; contract: ContractItem }>();
const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  submit: [payload: RenewalCreatePayload];
}>();

const term = ref<[string, string] | null>(null);
const expectedRent = ref(props.contract.rent);
const submitting = ref(false);

function disableBeforeEnd(date: Date) {
  return date.getTime() < new Date(`${props.contract.endDate}T00:00:00`).getTime();
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      expectedRent.value = props.contract.rent;
      term.value = [props.contract.endDate, addMonths(props.contract.endDate, 6)];
    }
  },
);

function addMonths(dateText: string, months: number) {
  const date = new Date(`${dateText}T00:00:00`);
  date.setMonth(date.getMonth() + months);
  return date.toISOString().slice(0, 10);
}

async function submit() {
  if (!term.value) return;
  submitting.value = true;
  try {
    emit('submit', {
      startDate: term.value[0],
      endDate: term.value[1],
      expectedRent: expectedRent.value,
    });
    emit('update:modelValue', false);
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.unit {
  margin-left: 8px;
  color: #6b7280;
}
</style>
