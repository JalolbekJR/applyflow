import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import VacancyRow from '~/components/vacancies/VacancyRow.vue'
import { vacancyFixtures } from '~/data/vacancies'

describe('VacancyRow', () => {
  it('renders role content as an editorial row with a direct action', () => {
    const wrapper = mount(VacancyRow, {
      props: { vacancy: structuredClone(vacancyFixtures[0]!), index: 1 },
      global: {
        stubs: {
          NuxtLink: { template: '<a><slot /></a>' },
          VacanciesVacancyMeta: {
            template: '<ul aria-label="Vacancy details"><li>Hybrid</li></ul>',
          },
        },
      },
    })
    expect(wrapper.get('h2').text()).toBe('Frontend Developer')
    expect(wrapper.text()).toContain('Build fast, accessible Nuxt interfaces')
    expect(wrapper.text()).toContain('View role')
    expect(wrapper.classes()).toContain('vacancy-row')
  })
})
