import { describe, expect, it } from 'vitest'
import { validateCandidateDetails, validateExperience } from '~/utils/validation'

describe('candidate validation', () => {
  it('reports required fields and cross-field phone requirements', () => {
    const errors = validateCandidateDetails({
      fullName: '',
      email: 'not-an-email',
      phone: '',
      profileUrl: '',
      preferredContactMethod: 'phone',
    })
    expect(errors.fullName).toBe('Enter your full name.')
    expect(errors.email).toContain('name@example.com')
    expect(errors.phone).toContain('phone number')
  })

  it('accepts a complete experience step', () => {
    const errors = validateExperience(
      {
        experienceLevel: 'mid-level',
        skills: ['Vue 3', 'TypeScript'],
        message: '',
        consentAcknowledged: true,
      },
      { name: 'avery-example-cv.pdf', size: 42_000, type: 'application/pdf' },
    )
    expect(errors).toEqual({})
  })
})
