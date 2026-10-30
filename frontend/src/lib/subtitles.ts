export interface Cue {
  start: number
  end: number
  text: string
  color?: string
}

function parseStamp(value: string): number {
  const [clock, fraction = '0'] = value.trim().replace(',', '.').split('.')
  const parts = clock.split(':').map(Number)
  const [hours, minutes, seconds] = parts.length === 3 ? parts : [0, ...parts]
  return hours * 3600 + minutes * 60 + seconds + Number(`0.${fraction}`)
}

const FONT_COLOR = /<font\s+color="(#[0-9a-fA-F]{3,8})"[^>]*>/i

function stripSrtMarkup(raw: string): { text: string; color?: string } {
  const color = raw.match(FONT_COLOR)?.[1]
  const text = raw.replace(/<\/?font[^>]*>/gi, '').trim()
  return color ? { text, color } : { text }
}

export function parseSrt(raw: string): Cue[] {
  const cues: Cue[] = []
  for (const block of raw.replace(/\r/g, '').trim().split(/\n\n+/)) {
    const lines = block.split('\n').filter(Boolean)
    const timingIndex = lines.findIndex((line) => line.includes('-->'))
    if (timingIndex === -1) continue
    const [start, end] = lines[timingIndex]
      .split('-->')
      .map((part) => parseStamp(part.trim().split(' ')[0]))
    const body = lines.slice(timingIndex + 1).join('\n').trim()
    if (!body) continue
    cues.push({ start, end, ...stripSrtMarkup(body) })
  }
  return cues
}

export function activeCue(cues: Cue[], time: number): Cue | undefined {
  return cues.find((cue) => time >= cue.start && time < cue.end)
}
