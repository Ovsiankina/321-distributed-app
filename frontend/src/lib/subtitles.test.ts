import { describe, expect, it } from 'vitest'
import { activeCue, parseSrt } from './subtitles'

const srt = `1
00:00:01,000 --> 00:00:03,500
Bonjour

2
00:00:04,250 --> 00:00:06,000 X1:0
<font color="#ffcc00">Deux</font>
lignes

3
00:00:07,000 --> 00:00:08,000
`

describe('parseSrt', () => {
  it('parses timings, multi-line text and font colors, skipping empty cues', () => {
    expect(parseSrt(srt)).toEqual([
      { start: 1, end: 3.5, text: 'Bonjour' },
      { start: 4.25, end: 6, text: 'Deux\nlignes', color: '#ffcc00' },
    ])
  })

  it('accepts CRLF line endings and timestamps without hours', () => {
    expect(parseSrt('1\r\n01:02.5 --> 01:03.0\r\nSalut\r\n')).toEqual([
      { start: 62.5, end: 63, text: 'Salut' },
    ])
  })

  it('returns no cue for an empty file', () => {
    expect(parseSrt('')).toEqual([])
  })
})

describe('activeCue', () => {
  const cues = parseSrt(srt)

  it('returns the cue covering the given time', () => {
    expect(activeCue(cues, 2)?.text).toBe('Bonjour')
  })

  it('treats the end time as exclusive', () => {
    expect(activeCue(cues, 3.5)).toBeUndefined()
  })
})
