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
      const now = Math.max(ctx.currentTime, 0.001)
      const safeVol = Math.max(0.05, Math.min(1, volume))

      const masterGain = ctx.createGain()
      masterGain.gain.setValueAtTime(safeVol, now)
      masterGain.connect(ctx.destination)

      if (type === 'chime') {
        // Digital Chime (清脆金铃): 4 ascending notes
        const notes = [523.25, 659.25, 783.99, 1046.5] // C5, E5, G5, C6
        notes.forEach((freq, idx) => {
          const startTime = now + idx * 0.12
          const osc = ctx.createOscillator()
          const noteGain = ctx.createGain()

          osc.type = 'sine'
          osc.frequency.setValueAtTime(freq, startTime)

          noteGain.gain.setValueAtTime(0.65, startTime)
          noteGain.gain.setTargetAtTime(0, startTime + 0.02, 0.12)

          osc.connect(noteGain)
          noteGain.connect(masterGain)

          osc.start(startTime)
          osc.stop(startTime + 0.7)
        })
      } else if (type === 'marimba') {
        // Soft Marimba (柔和木鱼/木琴)
        const notes = [440, 554.37, 659.25]
        notes.forEach((freq, idx) => {
          const startTime = now + idx * 0.14
          const osc = ctx.createOscillator()
          const noteGain = ctx.createGain()

          osc.type = 'triangle'
          osc.frequency.setValueAtTime(freq, startTime)

          noteGain.gain.setValueAtTime(0.75, startTime)
          noteGain.gain.setTargetAtTime(0, startTime + 0.01, 0.09)

          osc.connect(noteGain)
          noteGain.connect(masterGain)

          osc.start(startTime)
          osc.stop(startTime + 0.55)
        })
      } else if (type === 'cyber') {
        // Cyber Pulse (科技和声)
        const startTime = now
        const osc = ctx.createOscillator()
        const noteGain = ctx.createGain()

        osc.type = 'sawtooth'
        osc.frequency.setValueAtTime(261.63, startTime)
        osc.frequency.exponentialRampToValueAtTime(880, startTime + 0.3)

        noteGain.gain.setValueAtTime(0.45, startTime)
        noteGain.gain.setTargetAtTime(0, startTime + 0.04, 0.08)

        osc.connect(noteGain)
        noteGain.connect(masterGain)

        osc.start(startTime)
        osc.stop(startTime + 0.45)
      } else if (type === 'beep') {
        // Beep Alert (警报哔哔)
        [0, 0.18, 0.36].forEach((timeOffset) => {
          const startTime = now + timeOffset
          const osc = ctx.createOscillator()
          const noteGain = ctx.createGain()

          osc.type = 'square'
          osc.frequency.setValueAtTime(880, startTime)

          noteGain.gain.setValueAtTime(0.35, startTime)
          noteGain.gain.setValueAtTime(0, startTime + 0.1)

          osc.connect(noteGain)
          noteGain.connect(masterGain)

          osc.start(startTime)
          osc.stop(startTime + 0.12)
        })
      }
    } catch (e) {
      console.warn('Audio Synthesis failed:', e)
    }
  }
}

export const soundPlayer = new SoundSynth()
