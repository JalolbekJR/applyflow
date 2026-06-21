import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import CredentialBlock from '~/components/application/CredentialBlock.vue'

describe('CredentialBlock', () => {
  const writeText = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.useFakeTimers()
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } })
    writeText.mockClear()
  })

  it('copies the credential and announces temporary feedback', async () => {
    const wrapper = mount(CredentialBlock, {
      props: { label: 'Private status secret', value: 'slk_example' },
    })
    await wrapper.get('button').trigger('click')
    expect(writeText).toHaveBeenCalledWith('slk_example')
    expect(wrapper.get('[aria-live="polite"]').text()).toBe('Copied')
    await vi.runAllTimersAsync()
    expect(wrapper.get('[aria-live="polite"]').text()).toBe('')
  })

  it('keeps the credential visible and explains manual recovery when copying fails', async () => {
    writeText.mockRejectedValueOnce(new Error('Clipboard unavailable'))
    const wrapper = mount(CredentialBlock, {
      props: { label: 'Application reference', value: 'AF-EXAMPLE' },
    })

    await wrapper.get('button').trigger('click')

    expect(wrapper.get('strong').text()).toBe('AF-EXAMPLE')
    expect(wrapper.get('[aria-live="polite"]').text()).toBe(
      'Copy failed. Select the value above and copy it manually.',
    )
  })
})
