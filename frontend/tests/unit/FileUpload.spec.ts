import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import FileUpload from '~/components/forms/FileUpload.vue'

describe('FileUpload', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('emits selected PDF metadata without retaining file contents', async () => {
    vi.useFakeTimers()
    const wrapper = mount(FileUpload, { props: { metadata: null } })
    const input = wrapper.get('input[type="file"]')
    const fixture = readFileSync(resolve(process.cwd(), 'tests/fixtures/avery-example-cv.pdf'))
    const file = new File([fixture], 'avery-example-cv.pdf', { type: 'application/pdf' })
    Object.defineProperty(input.element, 'files', { configurable: true, value: [file] })
    await input.trigger('change')
    await vi.runAllTimersAsync()
    const metadata = {
      name: 'avery-example-cv.pdf',
      size: file.size,
      type: 'application/pdf',
    }
    expect(wrapper.emitted('update:metadata')?.[0]?.[0]).toEqual(metadata)
    await wrapper.setProps({ metadata })
    expect(wrapper.get('.upload-result strong').text()).toBe('avery-example-cv.pdf')
  })

  it('rejects unsupported file extensions without removing existing metadata', async () => {
    const metadata = { name: 'avery-example-cv.pdf', size: 1024, type: 'application/pdf' }
    const wrapper = mount(FileUpload, { props: { metadata } })
    const input = wrapper.get('input[type="file"]')
    const file = new File(['fictional'], 'avery-example-cv.txt', { type: 'text/plain' })
    Object.defineProperty(input.element, 'files', { configurable: true, value: [file] })

    await input.trigger('change')

    expect(wrapper.text()).toContain('Choose a PDF file.')
    expect(wrapper.emitted('update:metadata')).toBeUndefined()
    expect(wrapper.text()).toContain('avery-example-cv.pdf')
  })

  it('tests the oversize metadata path without allocating a large file', async () => {
    const wrapper = mount(FileUpload, { props: { metadata: null } })
    const input = wrapper.get('input[type="file"]')
    const file = new File(['%PDF-1.4'], 'oversize-fixture.pdf', { type: 'application/pdf' })
    Object.defineProperty(file, 'size', { configurable: true, value: 5 * 1024 * 1024 + 1 })
    Object.defineProperty(input.element, 'files', { configurable: true, value: [file] })

    await input.trigger('change')

    expect(wrapper.text()).toContain('Choose a PDF file under 5 MB.')
    expect(wrapper.emitted('update:metadata')).toBeUndefined()
  })
})
