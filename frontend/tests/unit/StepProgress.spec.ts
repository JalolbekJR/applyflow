import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StepProgress from '~/components/application/StepProgress.vue'

describe('StepProgress', () => {
  it('exposes the current step in text and aria-current', () => {
    const wrapper = mount(StepProgress, { props: { current: 3 } })
    expect(wrapper.text()).toContain('Step 3 of 4 - Experience')
    expect(wrapper.get('[aria-current="step"]').text()).toContain('Experience')
    expect(wrapper.findAll('li')).toHaveLength(4)
  })
})
