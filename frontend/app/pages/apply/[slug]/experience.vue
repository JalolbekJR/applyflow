<script setup lang="ts">
import { fixtureApplicationService } from '~/services/application-service'
import type { ExperienceData, UploadedDocumentMetadata } from '~/types/domain'
import { cloneData } from '~/utils/clone-data'
import { validateExperience, type FieldErrors } from '~/utils/validation'

const route = useRoute()
const { vacancy } = await useVacancyPage({ activeOnly: true })
const { draft, enterApplicationStep, saveState, updateDocument, updateExperience } =
  useApplicationDraft()
if (vacancy.value) await enterApplicationStep(vacancy.value.slug)
const form = reactive<ExperienceData>(cloneData(draft.value.experience))
const skillsText = ref(form.skills.join(', '))
const errors = ref<FieldErrors>({})
const serverError = ref('')
const errorSummary = useTemplateRef<{ focus: () => Promise<void> }>('errorSummary')
const saveFailure = useTemplateRef<{ focus: () => Promise<void> }>('saveFailure')

useSeoMeta({
  title: () =>
    vacancy.value ? `Apply for ${vacancy.value.title} - Experience` : 'Application unavailable',
})

const setDocument = (metadata: UploadedDocumentMetadata | null) => {
  updateDocument(metadata)
  if (metadata) delete errors.value.document
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

  updateExperience(form)
  saveState.value = 'saving'
  try {
    await fixtureApplicationService.saveDraft(draft.value)
    saveState.value = 'saved'
    await navigateTo(`/apply/${vacancy.value?.slug}/review`)
  } catch {
    saveState.value = 'error'
    serverError.value = 'save_failed'
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
          :error="errors.document"
          @update:metadata="setDocument"
        />

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
