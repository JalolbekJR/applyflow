<script setup lang="ts">
import { ref, useTemplateRef, watch } from 'vue'
import type { UploadedDocumentMetadata } from '~/types/domain'
import { formatFileSize } from '~/utils/validation'

const props = defineProps<{
  metadata: UploadedDocumentMetadata | null
  error?: string
  progress?: number | null
  canCancel?: boolean
}>()

const emit = defineEmits<{
  'update:metadata': [value: UploadedDocumentMetadata | null]
  upload: [value: File]
  cancel: []
  remove: []
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
  emit('upload', file)
}

const removeFile = () => {
  if (input.value) input.value.value = ''
  localError.value = ''
  status.value = 'idle'
  emit('remove')
}

const cancelUpload = () => {
  emit('cancel')
}

watch(
  () => props.metadata,
  (metadata) => {
    status.value = metadata ? 'uploaded' : 'idle'
  },
  { immediate: true },
)

watch(
  () => props.error,
  (error) => {
    if (error) status.value = 'rejected'
  },
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
        <p id="document-hint">PDF only. Maximum 5 MB. The backend verifies every upload.</p>
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
        <span>{{ formatFileSize(metadata.size) }} - uploaded to the protected draft</span>
      </div>
      <div class="inline-actions">
        <button class="text-button" type="button" @click="chooseFile">Replace</button>
        <button class="text-button text-button--danger" type="button" @click="removeFile">
          Remove
        </button>
      </div>
    </div>
    <div v-else class="upload-empty">
      <div v-if="status === 'uploading'" class="upload-progress" aria-live="polite">
        <p v-if="typeof progress === 'number'">Uploading CV... {{ progress }}%</p>
        <p v-else>Uploading CV...</p>
        <progress
          v-if="typeof progress === 'number'"
          :value="progress"
          max="100"
          aria-label="CV upload progress"
        />
        <progress v-else aria-label="CV upload progress" />
        <button
          v-if="canCancel"
          class="text-button text-button--danger"
          type="button"
          @click="cancelUpload"
        >
          Cancel upload
        </button>
      </div>
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
