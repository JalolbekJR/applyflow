import { describe, expect, it } from 'vitest'
import { alternateTestBrand, defaultBrand } from '~/branding/default-brand'
import { validateBrandConfig } from '~/branding/schema'

describe('brand configuration', () => {
  it('keeps the default ApplyFlow identity and phase capabilities locked', () => {
    expect(defaultBrand.shortName).toBe('Northline Studio')
    expect(defaultBrand.experience.finalSubmission).toBe(false)
    expect(defaultBrand.experience.statusLookup).toBe(false)
  })

  it('supports a fictional alternate brand without changing API security capability flags', () => {
    expect(alternateTestBrand.shortName).toBe('Riverbend Labs')
    expect(alternateTestBrand.experience.applicationLayout).toBe('compact')
    expect(alternateTestBrand.experience.finalSubmission).toBe(false)
    expect(alternateTestBrand.experience.statusLookup).toBe(false)
  })

  it('rejects unsafe text, JavaScript links, and capability escalation', () => {
    expect(() =>
      validateBrandConfig({
        ...defaultBrand,
        publicCopy: { ...defaultBrand.publicCopy, homeTitle: '<strong>Unsafe</strong>' },
      }),
    ).toThrow(/plain safe text/)
    expect(() =>
      validateBrandConfig({
        ...defaultBrand,
        legalLinks: [{ label: 'Unsafe', href: 'javascript:alert(1)' }],
      }),
    ).toThrow(/HTTPS/)
    expect(() =>
      validateBrandConfig({
        ...defaultBrand,
        experience: { ...defaultBrand.experience, finalSubmission: true as false },
      }),
    ).toThrow(/Phase 4/)
  })
})
