import { describe, expect, it } from 'vitest'
import { errorMessage } from './api'

describe('API error display', () => {
  it('shows ordinary errors without losing their message', () => {
    expect(errorMessage(new Error('Connection failed'))).toBe('Connection failed')
  })
})
