import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import Login from '../Login.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

describe('Login', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    push.mockReset()
  })

  it('submits admin credentials and navigates to dashboard', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({ username: 'root' }),
    }))
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = mount(Login)
    await wrapper.find('input[name="username"]').setValue('root')
    await wrapper.find('input[name="password"]').setValue('Dl960513.')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith('/api/auth/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'root', password: 'Dl960513.' }),
    })
    expect(push).toHaveBeenCalledWith('/')
  })

  it('shows a clear error when login fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: false,
        text: async () => JSON.stringify({ detail: '用户名或密码错误' }),
      })),
    )

    const wrapper = mount(Login)
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(wrapper.text()).toContain('用户名或密码错误')
  })
})
