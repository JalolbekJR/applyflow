<script setup lang="ts">
import { ApplyFlowApiError } from '~/api/errors'
import type { CandidateDetails } from '~/types/domain'
import { mapCandidateApiErrors } from '~/utils/api-field-errors'
import { cloneData } from '~/utils/clone-data'
import { validateCandidateDetails, type FieldErrors } from '~/utils/validation'

const route = useRoute()
const { vacancy } = await useVacancyPage({ activeOnly: true })
const { draft, enterApplicationStep, saveState, saveCandidate } = useApplicationDraft()
if (vacancy.value) await enterApplicationStep(vacancy.value.slug)
const form = reactive<CandidateDetails>(cloneData(draft.value.candidate))
const errors = ref<FieldErrors>({})
const serverError = ref('')
const errorSummary = useTemplateRef<{ focus: () => Promise<void> }>('errorSummary')
const saveFailure = useTemplateRef<{ focus: () => Promise<void> }>('saveFailure')

useSeoMeta({
  title: () =>
    vacancy.value
      ? `Apply for ${vacancy.value.title} - Candidate details`
      : 'Application unavailable',
})

const submit = async () => {
  errors.value = validateCandidateDetails(form)
  serverError.value = ''
  if (Object.keys(errors.value).length) {
    await nextTick()
    await errorSummary.value?.focus()
    return
  }

  try {
    await saveCandidate(form)
    const destination = route.query.return === 'review' ? 'review' : 'experience'
    await navigateTo(`/apply/${vacancy.value?.slug}/${destination}`)
  } catch (error) {
    if (error instanceof ApplyFlowApiError && Object.keys(error.fields).length) {
      errors.value = mapCandidateApiErrors(error.fields)
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
    :current-step="2"
    title="Candidate details"
    intro="Add the contact information Northline Studio would need to respond. Optional fields are marked."
    :save-state="saveState"
  >
    <FeedbackErrorSummary v-if="Object.keys(errors).length" ref="errorSummary" :errors="errors" />
    <ApplicationSaveFailure v-if="serverError" ref="saveFailure" />

    <form novalidate @submit.prevent="submit">
      <div class="form-stack">
        <div class="field">
          <div class="field-heading">
            <label for="fullName">Full name</label><span class="required-note">Required</span>
          </div>
          <p id="fullName-hint" class="field-hint">
            Use the name you want us to use when contacting you.
          </p>
          <input
            id="fullName"
            v-model="form.fullName"
            autocomplete="name"
            :aria-invalid="Boolean(errors.fullName)"
            :aria-describedby="`fullName-hint${errors.fullName ? ' fullName-error' : ''}`"
          />
          <p v-if="errors.fullName" id="fullName-error" class="field-error">
            {{ errors.fullName }}
          </p>
        </div>

        <div class="field">
          <div class="field-heading">
            <label for="email">Email address</label><span class="required-note">Required</span>
          </div>
          <p id="email-hint" class="field-hint">
            Used for contact and duplicate-submission checks later.
          </p>
          <input
            id="email"
            v-model="form.email"
            type="email"
            autocomplete="email"
            inputmode="email"
            :aria-invalid="Boolean(errors.email)"
            :aria-describedby="`email-hint${errors.email ? ' email-error' : ''}`"
          />
          <p v-if="errors.email" id="email-error" class="field-error">{{ errors.email }}</p>
        </div>

        <div class="field">
          <div class="field-heading">
            <label for="phone">Phone number</label><span class="required-note">Optional</span>
          </div>
          <p id="phone-hint" class="field-hint">Add it only if phone contact is okay.</p>
          <input
            id="phone"
            v-model="form.phone"
            type="tel"
            autocomplete="tel"
            inputmode="tel"
            :aria-invalid="Boolean(errors.phone)"
            :aria-describedby="`phone-hint${errors.phone ? ' phone-error' : ''}`"
          />
          <p v-if="errors.phone" id="phone-error" class="field-error">{{ errors.phone }}</p>
        </div>

        <div class="field">
          <div class="field-heading">
            <label for="profileUrl">Portfolio, GitHub, or LinkedIn</label
            ><span class="required-note">Optional</span>
          </div>
          <p id="profileUrl-hint" class="field-hint">
            Add one secure link that best represents your work.
          </p>
          <input
            id="profileUrl"
            v-model="form.profileUrl"
            type="url"
            inputmode="url"
            placeholder="https://"
            :aria-invalid="Boolean(errors.profileUrl)"
            :aria-describedby="`profileUrl-hint${errors.profileUrl ? ' profileUrl-error' : ''}`"
          />
          <p v-if="errors.profileUrl" id="profileUrl-error" class="field-error">
            {{ errors.profileUrl }}
          </p>
        </div>

        <fieldset
          id="preferredContactMethod"
          class="field"
          tabindex="-1"
          :aria-invalid="Boolean(errors.preferredContactMethod)"
          :aria-describedby="`contact-hint${errors.preferredContactMethod ? ' preferredContactMethod-error' : ''}`"
        >
          <legend class="fieldset-label">
            Preferred contact method <span aria-hidden="true">*</span>
          </legend>
          <p id="contact-hint" class="field-hint">Choose how you would rather hear from us.</p>
          <div class="radio-list">
            <label
              ><input
                v-model="form.preferredContactMethod"
                type="radio"
                name="preferredContactMethod"
                value="email"
              />
              Email</label
            >
            <label
              ><input
                v-model="form.preferredContactMethod"
                type="radio"
                name="preferredContactMethod"
                value="phone"
              />
              Phone</label
            >
          </div>
          <p
            v-if="errors.preferredContactMethod"
            id="preferredContactMethod-error"
            class="field-error"
          >
            {{ errors.preferredContactMethod }}
          </p>
        </fieldset>
      </div>

      <ApplicationSaveStatus :state="saveState" />
      <div class="application-actions">
        <NuxtLink class="button button--secondary" :to="`/apply/${vacancy.slug}`">Back</NuxtLink>
        <button class="button" type="submit" :disabled="saveState === 'saving'">
          {{
            saveState === 'saving'
              ? 'Saving...'
              : saveState === 'error'
                ? 'Try saving again'
                : route.query.return === 'review'
                  ? 'Save and return to review'
                  : 'Continue to experience'
          }}
        </button>
      </div>
    </form>
  </ApplicationShell>
  <ApplicationUnavailable v-else />
</template>
