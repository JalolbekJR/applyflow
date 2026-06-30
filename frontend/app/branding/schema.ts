export type ApplicationLayoutVariant = 'standard' | 'compact'
export type HeaderVariant = 'standard' | 'minimal'
export type VacancyListVariant = 'cards' | 'compact'
export type ProgressVariant = 'steps' | 'summary'

export interface BrandLink {
  label: string
  href: string
}

export interface BrandThemeTokens {
  pageBackground: string
  surface: string
  surfaceMuted: string
  text: string
  textMuted: string
  border: string
  borderStrong: string
  primary: string
  primaryHover: string
  primaryActive: string
  primaryText: string
  focus: string
  danger: string
  warning: string
  success: string
  pending: string
  bodyFont: string
  headingFont: string
}

export interface BrandExperienceConfig {
  applicationLayout: ApplicationLayoutVariant
  headerVariant: HeaderVariant
  vacancyListVariant: VacancyListVariant
  progressVariant: ProgressVariant
  showOptionalPortfolio: boolean
  emphasizeEmploymentEntries: boolean
  finalSubmission: false
  statusLookup: false
}

export interface BrandConfig {
  productName: string
  shortName: string
  logoText: string
  logoAlt: string
  faviconHref: string
  supportContactText: string
  legalLinks: BrandLink[]
  accessibilityLink: BrandLink
  pageTitleSuffix: string
  publicCopy: {
    homeEyebrow: string
    homeTitle: string
    homeIntro: string
    vacancyListIntro: string
    footerNote: string
  }
  companyDescriptor?: string
  theme: BrandThemeTokens
  experience: BrandExperienceConfig
}

const safeColor = /^#[0-9a-f]{6}$/i
const forbiddenText = /<[^>]*>|javascript:|data:/i

const isSafeText = (value: string) => value.trim().length > 0 && !forbiddenText.test(value)

export const validateBrandLink = (link: BrandLink): BrandLink => {
  if (!isSafeText(link.label)) throw new Error('Brand link label is unsafe.')
  if (link.href.startsWith('/')) return link
  let url: URL
  try {
    url = new URL(link.href)
  } catch (error) {
    throw new Error('Brand link must be a relative path or HTTPS URL.', { cause: error })
  }
  if (url.protocol !== 'https:' || url.username || url.password) {
    throw new Error('Brand external links must be explicit HTTPS URLs without credentials.')
  }
  return link
}

export const validateBrandConfig = (config: BrandConfig): BrandConfig => {
  const textValues = [
    config.productName,
    config.shortName,
    config.logoText,
    config.logoAlt,
    config.supportContactText,
    config.pageTitleSuffix,
    config.publicCopy.homeEyebrow,
    config.publicCopy.homeTitle,
    config.publicCopy.homeIntro,
    config.publicCopy.vacancyListIntro,
    config.publicCopy.footerNote,
    config.companyDescriptor ?? 'company',
  ]
  if (!textValues.every(isSafeText)) throw new Error('Brand text must be plain safe text.')
  for (const value of Object.values(config.theme)) {
    if (value.startsWith('#') && !safeColor.test(value)) throw new Error('Brand color is invalid.')
    if (forbiddenText.test(value)) throw new Error('Brand theme token is unsafe.')
  }
  config.legalLinks.forEach(validateBrandLink)
  validateBrandLink(config.accessibilityLink)
  if (config.experience.finalSubmission !== false || config.experience.statusLookup !== false) {
    throw new Error('Phase 4 capabilities cannot be enabled by brand configuration.')
  }
  return config
}
