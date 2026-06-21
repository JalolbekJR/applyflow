<script setup lang="ts">
defineProps<{
  current: 1 | 2 | 3 | 4
}>()

const steps = ['Position', 'Candidate details', 'Experience', 'Review']
</script>

<template>
  <nav class="step-progress" aria-label="Application progress">
    <p class="step-progress__current">Step {{ current }} of 4 - {{ steps[current - 1] }}</p>
    <ol>
      <li
        v-for="(step, index) in steps"
        :key="step"
        :class="{ 'is-complete': index + 1 < current }"
        :aria-current="index + 1 === current ? 'step' : undefined"
      >
        <span class="step-progress__number">{{ index + 1 }}</span>
        <span class="step-progress__label">{{ step }}</span>
      </li>
    </ol>
  </nav>
</template>
