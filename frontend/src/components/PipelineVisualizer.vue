<template>
  <div class="pipeline">
    <div
      v-for="(stage, index) in stages"
      :key="index"
      class="stage"
      :class="stage.status"
    >
      <div class="icon">
        <span v-if="stage.status === 'success'">✔</span>
        <span v-else-if="stage.status === 'failed'">✖</span>
        <span v-else>⏳</span>
      </div>

      <div class="name">{{ stage.name }}</div>

      <div v-if="index !== stages.length - 1" class="line"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  stages: Array
})
</script>

<style scoped>
.pipeline {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
  overflow-x: auto;
}

.stage {
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.icon {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  border: 1px solid var(--border);
  background: var(--panel);
}

.stage.success .icon {
  color: var(--green);
  border-color: var(--green);
}

.stage.failed .icon {
  color: var(--red);
  border-color: var(--red);
}

.stage.running .icon {
  color: var(--yellow);
  border-color: var(--yellow);
}

.name {
  font-size: 13px;
  color: var(--muted);
}

.line {
  width: 40px;
  height: 2px;
  background: var(--border);
  margin-left: 6px;
}
</style>
