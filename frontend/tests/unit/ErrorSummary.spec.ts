import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ErrorSummary from '~/components/feedback/ErrorSummary.vue'

describe('ErrorSummary', () => {
  afterEach(() => {
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  it('links each error to its field and can receive focus', async () => {
    const wrapper = mount(ErrorSummary, {
      attachTo: document.body,
      props: { errors: { email: 'Enter a valid email.', fullName: 'Enter your name.' } },
    })
    expect(wrapper.get('a[href="#email"]').text()).toBe('Enter a valid email.')
    await wrapper.vm.focus()
    await wrapper.vm.$nextTick()
    expect(document.activeElement).toBe(wrapper.element)
    wrapper.unmount()
  })

  it('moves focus from a summary link to a grouped field destination', async () => {
    const fieldset = document.createElement('fieldset')
    fieldset.id = 'preferredContactMethod'
    fieldset.tabIndex = -1
    document.body.append(fieldset)
    const wrapper = mount(ErrorSummary, {
      attachTo: document.body,
      props: {
        errors: { preferredContactMethod: 'Choose a contact method.' },
      },
    })

    await wrapper.get('a[href="#preferredContactMethod"]').trigger('click')

    expect(document.activeElement).toBe(fieldset)
    wrapper.unmount()
  })

  it('rechecks a focused summary after layout and reveals it without animated motion', async () => {
    const wrapper = mount(ErrorSummary, {
      attachTo: document.body,
      props: { errors: { email: 'Enter an email address.' } },
    })
    const scrollIntoView = vi.fn()
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((callback) => {
      callback(0)
      return 1
    })
    Object.defineProperty(wrapper.element, 'scrollIntoView', { value: scrollIntoView })
    vi.spyOn(wrapper.element, 'getBoundingClientRect').mockReturnValue({
      bottom: window.innerHeight + 100,
      height: 100,
      left: 0,
      right: 100,
      top: window.innerHeight,
      width: 100,
      x: 0,
      y: window.innerHeight,
      toJSON: () => ({}),
    })

    await wrapper.vm.focus()

    expect(scrollIntoView).toHaveBeenCalledTimes(2)
    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'auto', block: 'start' })
    wrapper.unmount()
  })
})
