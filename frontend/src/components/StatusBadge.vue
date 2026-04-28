<template>
  <span :class="['badge', status]">
    <span class="dot"></span>
    {{ status }}
  </span>
</template>

<script setup>
defineProps({
  status: String
})
</script>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
  border: 1px solid var(--border);
  background: #0b0f19;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.success {
  color: var(--green);
  border-color: var(--green);
}
.success .dot {
  background: var(--green);
}

.failed {
  color: var(--red);
  border-color: var(--red);
}
.failed .dot {
  background: var(--red);
}

.running {
  color: var(--yellow);
  border-color: var(--yellow);
}
.running .dot {
  background: var(--yellow);
}

/* PENDING */
.pending {
  color: var(--muted);
}
.pending .dot {
  background: var(--muted);
}
</style>
