import type {
  CandidateDetails,
  ExperienceData,
  ExperienceEntry,
  UploadedDocumentMetadata,
} from '~/types/domain'

export type FieldErrors = Record<string, string>

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const phonePattern = /^[+()\d\s-]{7,30}$/

export const validateCandidateDetails = (details: CandidateDetails): FieldErrors => {
  const errors: FieldErrors = {}
  if (!details.fullName.trim()) errors.fullName = 'Enter your full name.'
  if (!emailPattern.test(details.email.trim())) {
    errors.email = 'Enter an email address in the format name@example.com.'
  }
  if (details.phone.trim() && !phonePattern.test(details.phone.trim())) {
    errors.phone = 'Enter a phone number using numbers and common phone symbols.'
  }
  if (details.profileUrl.trim()) {
    try {
      const url = new URL(details.profileUrl)
      if (url.protocol !== 'https:') errors.profileUrl = 'Add a secure link starting with https://.'
    } catch {
      errors.profileUrl = 'Add a valid link starting with https://.'
    }
  }
  if (!details.preferredContactMethod) {
    errors.preferredContactMethod = 'Choose a preferred contact method.'
  }
  if (details.preferredContactMethod === 'phone' && !details.phone.trim()) {
    errors.phone = 'Add a phone number before choosing phone contact.'
  }
  return errors
}

export const validateExperience = (
  experience: ExperienceData,
  document: UploadedDocumentMetadata | null,
): FieldErrors => {
  const errors: FieldErrors = {}
  if (!experience.experienceLevel) errors.experienceLevel = 'Choose your experience level.'
  if (experience.skills.length === 0) errors.skills = 'Add at least one relevant skill.'
  if (!document) errors.document = 'Upload a PDF CV under 5 MB.'
  if (!experience.consentAcknowledged) {
    errors.consentAcknowledged = 'Review the privacy acknowledgement before continuing.'
  }
  return errors
}

const monthPattern = /^[0-9]{4}-(0[1-9]|1[0-2])$/

export const validateExperienceEntry = (entry: ExperienceEntry): FieldErrors => {
  const errors: FieldErrors = {}
  if (!entry.organization.trim()) errors.organization = 'Enter the organization name.'
  if (!entry.roleTitle.trim()) errors.roleTitle = 'Enter your role title.'
  if (!monthPattern.test(entry.startMonth)) errors.startMonth = 'Enter a start month in YYYY-MM.'
  if (!entry.isCurrent && !monthPattern.test(entry.endMonth)) {
    errors.endMonth = 'Enter an end month in YYYY-MM, or mark the role current.'
  }
  if (
    entry.startMonth &&
    entry.endMonth &&
    !entry.isCurrent &&
    monthPattern.test(entry.startMonth) &&
    monthPattern.test(entry.endMonth) &&
    entry.endMonth < entry.startMonth
  ) {
    errors.endMonth = 'Choose an end month that is the same as or after the start month.'
  }
  return errors
}

export const formatFileSize = (bytes: number) => `${(bytes / 1024 / 1024).toFixed(1)} MB`
