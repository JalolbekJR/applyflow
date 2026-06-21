<script setup lang="ts">
import { ref, useTemplateRef, watch } from 'vue'
import type { UploadedDocumentMetadata } from '~/types/domain'
import { formatFileSize } from '~/utils/validation'

const props = defineProps<{
  metadata: UploadedDocumentMetadata | null
  error?: string
}>()

const emit = defineEmits<{
  'update:metadata': [value: UploadedDocumentMetadata | null]
}>()

const input = useTemplateRef<HTMLInputElement>('input')
const localError = ref('')
const status = ref<'idle' | 'uploading' | 'uploaded' | 'rejected'>('idle')

const chooseFile = () => input.value?.click()

const onFileChange = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  localError.value = ''
  if (!file) return

  const isPdf = file.name.toLowerCase().endsWith('.pdf') && file.type === 'application/pdf'
  if (!isPdf) {
    status.value = 'rejected'
    localError.value = 'Choose a PDF file.'
    if (input.value) input.value.value = ''
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    status.value = 'rejected'
    localError.value = 'Choose a PDF file under 5 MB.'
    if (input.value) input.value.value = ''
    return
  }

  status.value = 'uploading'
  await new Promise((resolve) => window.setTimeout(resolve, 220))
  emit('update:metadata', { name: file.name, size: file.size, type: file.type })
  status.value = 'uploaded'
}

const removeFile = () => {
  if (input.value) input.value.value = ''
  localError.value = ''
  status.value = 'idle'
  emit('update:metadata', null)
}

watch(
  () => props.metadata,
  (metadata) => {
    if (metadata && status.value === 'idle') status.value = 'uploaded'
  },
  { immediate: true },
)
</script>

<template>
  <section
    id="document"
    class="upload-field"
    :class="{ 'has-error': error || localError }"
    tabindex="-1"
    role="group"
    aria-label="CV upload field"
    :aria-describedby="`document-hint${error || localError ? ' document-error' : ''}`"
  >
    <div class="field-heading">
      <div>
        <label id="document-label" for="cv-upload">
          CV upload <span aria-hidden="true">*</span>
        </label>
        <p id="document-hint">PDF only. Maximum 5 MB. The backend will verify files later.</p>
      </div>
      <span class="required-note">Required</span>
    </div>
    <input
      id="cv-upload"
      ref="input"
      class="visually-hidden-file"
      type="file"
      accept=".pdf,application/pdf"
      :aria-describedby="`document-hint${error || localError ? ' document-error' : ''}`"
      :aria-invalid="Boolean(error || localError)"
      @change="onFileChange"
    />

    <div v-if="metadata" class="upload-result" aria-live="polite">
      <div>
        <strong>{{ metadata.name }}</strong>
        <span>{{ formatFileSize(metadata.size) }} - ready for this simulated application</span>
      </div>
      <div class="inline-actions">
        <button class="text-button" type="button" @click="chooseFile">Replace</button>
        <button class="text-button text-button--danger" type="button" @click="removeFile">
          Remove
        </button>
      </div>
    </div>
    <div v-else class="upload-empty">
      <p v-if="status === 'uploading'" aria-live="polite">Reading file details...</p>
      <template v-else>
        <p>Choose the PDF you want Northline Studio to review.</p>
        <button class="button button--secondary" type="button" @click="chooseFile">
          Choose PDF
        </button>
      </template>
    </div>
    <p v-if="error || localError" id="document-error" class="field-error">
      {{ localError || error }}
    </p>
  </section>
</template>
