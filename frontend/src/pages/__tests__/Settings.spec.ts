import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import Settings from '../Settings.vue'

describe('Settings', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads settings and shows secret configuration fields', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => ({
          pan115_cookie_masked: '',
          tmdb_api_key_masked: '',
          tmdb_language: 'zh-CN',
          default_source_dir: '0',
          default_target_dir: '0',
          default_recycle_dir: '0',
          allow_delete_old_files: false,
          recursive_scan: true,
        }),
      })),
    )

    const wrapper = mount(Settings)
    await flushPromises()

    expect(wrapper.text()).toContain('115 Cookie')
    expect(wrapper.text()).toContain('TMDB API Key')
  })
})
