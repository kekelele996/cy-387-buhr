<template>
  <el-timeline class="renewal-timeline">
    <el-timeline-item
      v-for="event in events"
      :key="event.id"
      :timestamp="`${event.time} · ${event.actorRole} ${event.actorName}`"
      :type="event.action === '租期冲突' ? 'danger' : event.action.includes('拒绝') || event.action.includes('取消') ? 'info' : 'primary'"
    >
      <span class="action">{{ event.action }}</span>
      <span v-if="event.note" class="note">（{{ event.note }}）</span>
    </el-timeline-item>
  </el-timeline>
</template>

<script setup lang="ts">
import type { RenewalEvent } from '../../types/domain';

defineProps<{ events: RenewalEvent[] }>();
</script>

<style scoped>
.renewal-timeline { margin-top: 8px; padding-left: 4px; }
.action { font-weight: 600; }
.note { color: #667085; }
</style>
