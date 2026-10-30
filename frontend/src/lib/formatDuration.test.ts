import { describe, expect, it } from 'vitest'
import { formatDuration } from './formatDuration'

describe('formatDuration', () => {
  it('pads seconds to two digits', () => {
    expect(formatDuration(65)).toBe('1:05')
  })

  it('formats durations under a minute', () => {
    expect(formatDuration(9)).toBe('0:09')
  })

  it('keeps counting minutes past an hour', () => {
    expect(formatDuration(3725)).toBe('62:05')
  })
})
