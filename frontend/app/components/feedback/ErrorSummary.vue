<script setup lang="ts">
import { useTemplateRef } from 'vue'
import { focusAndReveal } from '~/utils/focus'

const props = defineProps<{
  errors: Record<string, string>
  title?: string
  targets?: Record<string, string>
}>()

const summary = useTemplateRef<HTMLElement>('summary')

defineExpose({
  focus: () => focusAndReveal(summary.value),
})

const focusField = async (field: string) => {
  const targetId = props.targets?.[field] ?? field
  await focusAndReveal(document.getElementById(targetId))
}
</script>

<template>
  <section
    ref="summary"
    class="error-summary"
    tabindex="-1"
    role="alert"
    aria-labelledby="error-summary-title"
  >
    <h2 id="error-summary-title">{{ title ?? 'Check the highlighted fields' }}</h2>
    <ul>
      <li v-for="(message, field) in errors" :key="field">
        <a :href="`#${targets?.[field] ?? field}`" @click="focusField(field)">
          {{ message }}
        </a>
      </li>
    </ul>
  </section>
</template>
