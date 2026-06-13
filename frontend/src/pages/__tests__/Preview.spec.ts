import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import Preview from '../Preview.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {} }),
}))

describe('Preview', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows preview confirmation and execute selected action', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => [],
      })),
    )

    const wrapper = mount(Preview)
    await flushPromises()

    expect(wrapper.text()).toContain('预览确认')
    expect(wrapper.text()).toContain('执行勾选项')
  })
})
