import { describe, expect, it } from 'vitest'
import {
  mapCandidateApiErrors,
  mapExperienceApiErrors,
  mapExperienceEntryApiErrors,
} from '~/utils/api-field-errors'

describe('API field error mapping', () => {
  it('maps backend candidate field names to existing UI control names', () => {
    expect(
      mapCandidateApiErrors({
        full_name: ['Enter a name.'],
        portfolio_url: ['Enter a valid HTTP or HTTPS link.'],
        preferred_contact_method: ['Choose one.'],
      }),
    ).toEqual({
      fullName: 'Enter a name.',
      profileUrl: 'Enter a valid HTTP or HTTPS link.',
      preferredContactMethod: 'Choose one.',
    })
  })

  it('maps experience summary and employment entry fields without changing server messages', () => {
    expect(
      mapExperienceApiErrors({
        experience_level: ['Choose a level.'],
        consent_acknowledged: ['Review the acknowledgement.'],
      }),
    ).toEqual({
      experienceLevel: 'Choose a level.',
      consentAcknowledged: 'Review the acknowledgement.',
    })

    expect(
      mapExperienceEntryApiErrors({
        role_title: ['Enter a role.'],
        end_month: ['Add an end month.'],
      }),
    ).toEqual({
      roleTitle: 'Enter a role.',
      endMonth: 'Add an end month.',
    })
  })
})
