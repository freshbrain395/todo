// Web Audio API Synthesizer for Notifications & Alarms
export type SoundType = 'chime' | 'marimba' | 'cyber' | 'beep'

class SoundSynth {
  private ctx: AudioContext | null = null

  private initContext(): AudioContext {
    if (!this.ctx || this.ctx.state === 'closed') {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
      this.ctx = new AudioCtx()
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {})
    }
    return this.ctx
  }

  public async play(type: SoundType = 'chime', volume: number = 0.8) {
    try {
      const ctx = this.initContext()
      if (ctx.state === 'suspended') {
        await ctx.resume().catch(() => {})
      }
      const now = ctx.currentTime
      const safeVol = Math.max(0.01, Math.min(1, volume))

      const masterGain = ctx.createGain()
      masterGain.gain.setValueAtTime(safeVol, now)
      masterGain.connect(ctx.destination)

      if (type === 'chime') {
        // Digital Chime (清脆金铃): 4 ascending notes
        const notes = [523.25, 659.25, 783.99, 1046.5] // C5, E5, G5, C6
        notes.forEach((freq, idx) => {
          const startTime = now + idx * 0.12
          const duration = 0.6

          const osc = ctx.createOscillator()
          const noteGain = ctx.createGain()

          osc.type = 'sine'
          osc.frequency.setValueAtTime(freq, startTime)

          noteGain.gain.setValueAtTime(0.0001, startTime)
          noteGain.gain.linearRampToValueAtTime(0.6, startTime + 0.02)
          noteGain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration)

          osc.connect(noteGain)
          noteGain.connect(masterGain)

          osc.start(startTime)
          osc.stop(startTime + duration + 0.05)
        })
      } else if (type === 'marimba') {
        // Soft Marimba (柔和木鱼/木琴)
        const notes = [440, 554.37, 659.25]
        notes.forEach((freq, idx) => {
          const startTime = now + idx * 0.14
          const duration = 0.45

          const osc = ctx.createOscillator()
          const noteGain = ctx.createGain()

          osc.type = 'triangle'
          osc.frequency.setValueAtTime(freq, startTime)

          noteGain.gain.setValueAtTime(0.0001, startTime)
          noteGain.gain.linearRampToValueAtTime(0.8, startTime + 0.01)
          noteGain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration)

          osc.connect(noteGain)
          noteGain.connect(masterGain)

          osc.start(startTime)
          osc.stop(startTime + duration + 0.05)
        })
      } else if (type === 'cyber') {
        // Cyber Pulse (科技和声)
        const startTime = now
        const duration = 0.4

        const osc = ctx.createOscillator()
        const noteGain = ctx.createGain()

        osc.type = 'sawtooth'
        osc.frequency.setValueAtTime(261.63, startTime)
        osc.frequency.exponentialRampToValueAtTime(880, startTime + duration)

        noteGain.gain.setValueAtTime(0.0001, startTime)
        noteGain.gain.linearRampToValueAtTime(0.5, startTime + 0.03)
        noteGain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration)

        osc.connect(noteGain)
        noteGain.connect(masterGain)

        osc.start(startTime)
        osc.stop(startTime + duration + 0.05)
      } else if (type === 'beep') {
        // Beep Alert (警报哔哔)
        [0, 0.2, 0.4].forEach((timeOffset) => {
          const startTime = now + timeOffset
          const duration = 0.12

          const osc = ctx.createOscillator()
          const noteGain = ctx.createGain()

          osc.type = 'square'
          osc.frequency.setValueAtTime(880, startTime)

          noteGain.gain.setValueAtTime(0.0001, startTime)
          noteGain.gain.linearRampToValueAtTime(0.5, startTime + 0.01)
          noteGain.gain.linearRampToValueAtTime(0.0001, startTime + duration)

          osc.connect(noteGain)
          noteGain.connect(masterGain)

          osc.start(startTime)
          osc.stop(startTime + duration + 0.05)
        })
      }
    } catch (e) {
      console.warn('Audio Synthesis failed:', e)
    }
  }
}

export const soundPlayer = new SoundSynth()
