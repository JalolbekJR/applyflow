<script setup lang="ts">
import { ApplyFlowApiError } from '~/api/errors'
import type { ExperienceData, ExperienceEntry, UploadedDocumentMetadata } from '~/types/domain'
import { mapExperienceApiErrors, mapExperienceEntryApiErrors } from '~/utils/api-field-errors'
import { cloneData } from '~/utils/clone-data'
import { validateExperience, validateExperienceEntry, type FieldErrors } from '~/utils/validation'

const route = useRoute()
const { vacancy } = await useVacancyPage({ activeOnly: true })
const {
  draft,
  enterApplicationStep,
  saveState,
  updateDocument,
  saveExperience,
  saveExperienceEntry,
  removeExperienceEntry,
  uploadDocument,
  deleteDocument,
} = useApplicationDraft()
if (vacancy.value) await enterApplicationStep(vacancy.value.slug)
const form = reactive<ExperienceData>(cloneData(draft.value.experience))
const skillsText = ref(form.skills.join(', '))
const errors = ref<FieldErrors>({})
const entryErrors = ref<FieldErrors>({})
const serverError = ref('')
const errorSummary = useTemplateRef<{ focus: () => Promise<void> }>('errorSummary')
const saveFailure = useTemplateRef<{ focus: () => Promise<void> }>('saveFailure')
const entryFormElement = useTemplateRef<HTMLElement>('entryFormElement')

useSeoMeta({
  title: () =>
    vacancy.value ? `Apply for ${vacancy.value.title} - Experience` : 'Application unavailable',
})

const setDocument = (metadata: UploadedDocumentMetadata | null) => {
  updateDocument(metadata)
  if (metadata) delete errors.value.document
}

const uploadError = ref('')
const uploadProgress = ref<number | null>(null)
const uploadAbort = ref<AbortController | null>(null)
const uploadSelectedDocument = async (file: File) => {
  uploadError.value = ''
  uploadProgress.value = null
  uploadAbort.value?.abort()
  uploadAbort.value = new AbortController()
  try {
    await uploadDocument(file, {
      signal: uploadAbort.value.signal,
      onProgress: (loaded, total) => {
        uploadProgress.value = total ? Math.min(100, Math.round((loaded / total) * 100)) : null
      },
    })
    delete errors.value.document
  } catch (error) {
    uploadError.value =
      error instanceof ApplyFlowApiError
        ? (error.fields.file?.[0] ?? error.message)
        : 'The upload did not finish. Your answers are still visible.'
  } finally {
    uploadAbort.value = null
    uploadProgress.value = null
  }
}

const cancelUpload = () => {
  uploadAbort.value?.abort()
}

const removeDocument = async () => {
  uploadError.value = ''
  if (!draft.value.document) {
    setDocument(null)
    return
  }
  try {
    await deleteDocument()
  } catch (error) {
    uploadError.value =
      error instanceof ApplyFlowApiError
        ? error.message
        : 'The CV could not be removed. The uploaded document is still visible.'
  }
}

const blankEntry = (): ExperienceEntry => ({
  id: 'new',
  organization: '',
  roleTitle: '',
  startMonth: '',
  endMonth: '',
  isCurrent: false,
  summary: '',
  position: Math.min(draft.value.experienceEntries.length, 4),
})

const entryForm = reactive<ExperienceEntry>(blankEntry())
const editingEntryId = ref<string | null>(null)

const resetEntryForm = () => {
  Object.assign(entryForm, blankEntry())
  editingEntryId.value = null
  entryErrors.value = {}
}

const editEntry = async (entry: ExperienceEntry) => {
  Object.assign(entryForm, cloneData(entry))
  editingEntryId.value = entry.id
  entryErrors.value = {}
  await nextTick()
  entryFormElement.value?.focus()
}

const submitEntry = async () => {
  entryErrors.value = validateExperienceEntry(entryForm)
  if (Object.keys(entryErrors.value).length) return
  try {
    await saveExperienceEntry(cloneData(entryForm))
    resetEntryForm()
  } catch (error) {
    if (error instanceof ApplyFlowApiError && Object.keys(error.fields).length) {
      entryErrors.value = mapExperienceEntryApiErrors(error.fields)
    }
    serverError.value = error instanceof ApplyFlowApiError ? error.code : 'save_failed'
    await nextTick()
    await saveFailure.value?.focus()
  }
}

const deleteEntry = async (entry: ExperienceEntry) => {
  try {
    await removeExperienceEntry(entry.id)
    if (editingEntryId.value === entry.id) resetEntryForm()
  } catch (error) {
    serverError.value = error instanceof ApplyFlowApiError ? error.code : 'save_failed'
    await nextTick()
    await saveFailure.value?.focus()
  }
}

const submit = async () => {
  form.skills = skillsText.value
    .split(',')
    .map((skill) => skill.trim())
    .filter(Boolean)
    .slice(0, 12)
  errors.value = validateExperience(form, draft.value.document)
  serverError.value = ''
  if (Object.keys(errors.value).length) {
    await nextTick()
    await errorSummary.value?.focus()
    return
  }

  try {
    await saveExperience(form)
    await navigateTo(`/apply/${vacancy.value?.slug}/review`)
  } catch (error) {
    if (error instanceof ApplyFlowApiError && Object.keys(error.fields).length) {
      errors.value = mapExperienceApiErrors(error.fields)
    }
    serverError.value = error instanceof ApplyFlowApiError ? error.code : 'save_failed'
    await nextTick()
    await saveFailure.value?.focus()
  }
}
</script>

<template>
  <ApplicationShell
    v-if="vacancy"
    :vacancy="vacancy"
    :current-step="3"
    title="Experience"
    intro="Share a small amount of structured context and let your CV carry the detail."
    :save-state="saveState"
  >
    <FeedbackErrorSummary v-if="Object.keys(errors).length" ref="errorSummary" :errors="errors" />
    <ApplicationSaveFailure v-if="serverError" ref="saveFailure" />

    <form novalidate @submit.prevent="submit">
      <div class="form-stack">
        <div class="field">
          <div class="field-heading">
            <label for="experienceLevel">Experience level</label
            ><span class="required-note">Required</span>
          </div>
          <p id="experienceLevel-hint" class="field-hint">
            Choose the closest practical description.
          </p>
          <select
            id="experienceLevel"
            v-model="form.experienceLevel"
            :aria-invalid="Boolean(errors.experienceLevel)"
            :aria-describedby="`experienceLevel-hint${errors.experienceLevel ? ' experienceLevel-error' : ''}`"
          >
            <option value="">Select one</option>
            <option value="early-career">Early career</option>
            <option value="mid-level">Mid-level</option>
            <option value="senior">Senior</option>
          </select>
          <p v-if="errors.experienceLevel" id="experienceLevel-error" class="field-error">
            {{ errors.experienceLevel }}
          </p>
        </div>

        <div class="field">
          <div class="field-heading">
            <label for="skills">Relevant skills</label><span class="required-note">Required</span>
          </div>
          <p id="skills-hint" class="field-hint">Add up to 12 skills, separated with commas.</p>
          <input
            id="skills"
            v-model="skillsText"
            :aria-invalid="Boolean(errors.skills)"
            :aria-describedby="`skills-hint${errors.skills ? ' skills-error' : ''}`"
            placeholder="Vue 3, TypeScript, accessibility"
          />
          <p v-if="errors.skills" id="skills-error" class="field-error">{{ errors.skills }}</p>
        </div>

        <FormsFileUpload
          :metadata="draft.document"
          :error="uploadError || errors.document"
          :progress="uploadProgress"
          :can-cancel="Boolean(uploadAbort)"
          @update:metadata="setDocument"
          @upload="uploadSelectedDocument"
          @cancel="cancelUpload"
          @remove="removeDocument"
        />

        <section
          ref="entryFormElement"
          class="field"
          tabindex="-1"
          aria-labelledby="experience-entry-heading"
        >
          <div class="field-heading">
            <div>
              <h2 id="experience-entry-heading" class="section-heading">Recent employment</h2>
              <p class="field-hint">
                Add up to five roles when they help explain your experience. This section is
                optional.
              </p>
            </div>
            <span class="required-note">Optional</span>
          </div>

          <div v-if="draft.experienceEntries.length" class="entry-list" aria-label="Saved roles">
            <article v-for="entry in draft.experienceEntries" :key="entry.id" class="entry-card">
              <div>
                <strong>{{ entry.roleTitle }}</strong>
                <span>{{ entry.organization }}</span>
                <small>
                  {{ entry.startMonth }} -
                  {{ entry.isCurrent ? 'Present' : entry.endMonth }}
                </small>
              </div>
              <div class="inline-actions">
                <button class="text-button" type="button" @click="editEntry(entry)">Edit</button>
                <button
                  class="text-button text-button--danger"
                  type="button"
                  @click="deleteEntry(entry)"
                >
                  Remove
                </button>
              </div>
            </article>
          </div>
          <p v-else class="field-hint">No employment entries have been added.</p>

          <div class="entry-form-grid">
            <div class="field">
              <label for="entryOrganization">Organization</label>
              <input
                id="entryOrganization"
                v-model="entryForm.organization"
                :aria-invalid="Boolean(entryErrors.organization)"
                :aria-describedby="entryErrors.organization ? 'entryOrganization-error' : undefined"
              />
              <p v-if="entryErrors.organization" id="entryOrganization-error" class="field-error">
                {{ entryErrors.organization }}
              </p>
            </div>
            <div class="field">
              <label for="entryRoleTitle">Role title</label>
              <input
                id="entryRoleTitle"
                v-model="entryForm.roleTitle"
                :aria-invalid="Boolean(entryErrors.roleTitle)"
                :aria-describedby="entryErrors.roleTitle ? 'entryRoleTitle-error' : undefined"
              />
              <p v-if="entryErrors.roleTitle" id="entryRoleTitle-error" class="field-error">
                {{ entryErrors.roleTitle }}
              </p>
            </div>
            <div class="field">
              <label for="entryStartMonth">Start month</label>
              <input
                id="entryStartMonth"
                v-model="entryForm.startMonth"
                type="month"
                :aria-invalid="Boolean(entryErrors.startMonth)"
                :aria-describedby="entryErrors.startMonth ? 'entryStartMonth-error' : undefined"
              />
              <p v-if="entryErrors.startMonth" id="entryStartMonth-error" class="field-error">
                {{ entryErrors.startMonth }}
              </p>
            </div>
            <div class="field">
              <label for="entryEndMonth">End month</label>
              <input
                id="entryEndMonth"
                v-model="entryForm.endMonth"
                type="month"
                :disabled="entryForm.isCurrent"
                :aria-invalid="Boolean(entryErrors.endMonth)"
                :aria-describedby="entryErrors.endMonth ? 'entryEndMonth-error' : undefined"
              />
              <p v-if="entryErrors.endMonth" id="entryEndMonth-error" class="field-error">
                {{ entryErrors.endMonth }}
              </p>
            </div>
          </div>
          <label class="check-row check-row--inline" for="entryIsCurrent">
            <input id="entryIsCurrent" v-model="entryForm.isCurrent" type="checkbox" />
            <span>This is my current role</span>
          </label>
          <div class="field">
            <label for="entrySummary">Role summary</label>
            <textarea id="entrySummary" v-model="entryForm.summary" maxlength="600" />
          </div>
          <div class="inline-actions">
            <button
              class="button button--secondary"
              type="button"
              :disabled="saveState === 'saving'"
              @click="submitEntry"
            >
              {{ editingEntryId ? 'Save role' : 'Add role' }}
            </button>
            <button v-if="editingEntryId" class="text-button" type="button" @click="resetEntryForm">
              Cancel edit
            </button>
          </div>
        </section>

        <div class="field">
          <div class="field-heading">
            <label for="message">Short message</label><span class="required-note">Optional</span>
          </div>
          <p id="message-hint" class="field-hint">
            Use this only for context that is not obvious in your CV.
          </p>
          <textarea
            id="message"
            v-model="form.message"
            maxlength="1200"
            aria-describedby="message-hint"
          />
          <span class="character-count">{{ form.message.length }} / 1200</span>
        </div>

        <fieldset
          class="field"
          :aria-describedby="errors.consentAcknowledged ? 'consentAcknowledged-error' : undefined"
        >
          <legend class="fieldset-label">Privacy acknowledgement</legend>
          <div class="check-row">
            <label for="consentAcknowledged">
              <input
                id="consentAcknowledged"
                v-model="form.consentAcknowledged"
                type="checkbox"
                :aria-invalid="Boolean(errors.consentAcknowledged)"
                :aria-describedby="
                  errors.consentAcknowledged ? 'consentAcknowledged-error' : undefined
                "
              />
              <span
                >I understand this frontend uses fictional data and that real recruitment use
                requires reviewed privacy and retention policies.</span
              >
            </label>
          </div>
          <p v-if="errors.consentAcknowledged" id="consentAcknowledged-error" class="field-error">
            {{ errors.consentAcknowledged }}
          </p>
        </fieldset>
      </div>

      <ApplicationSaveStatus :state="saveState" />
      <div class="application-actions">
        <NuxtLink class="button button--secondary" :to="`/apply/${vacancy.slug}/details`"
          >Back</NuxtLink
        >
        <button class="button" type="submit" :disabled="saveState === 'saving'">
          {{
            saveState === 'saving'
              ? 'Saving...'
              : saveState === 'error'
                ? 'Try saving again'
                : route.query.return === 'review'
                  ? 'Save and return to review'
                  : 'Continue to review'
          }}
        </button>
      </div>
    </form>
  </ApplicationShell>
  <ApplicationUnavailable v-else />
</template>
