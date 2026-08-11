// Web Audio API Synthesizer for Notifications & Alarms
export type SoundType = 'chime' | 'marimba' | 'cyber' | 'beep'

class SoundSynth {
  private ctx: AudioContext | null = null

  private getContext(): AudioContext {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
      this.ctx = new AudioCtx()
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume()
    }
    return this.ctx
  }

  public play(type: SoundType = 'chime', volume: number = 0.8) {
    try {
      const ctx = this.getContext()
      const now = ctx.currentTime

      const gain = ctx.createGain()
      gain.gain.setValueAtTime(volume, now)
      gain.connect(ctx.destination)

      if (type === 'chime') {
        // Digital Chime (清脆金铃)
        const notes = [523.25, 659.25, 783.99, 1046.5] // C5, E5, G5, C6
        notes.forEach((freq, idx) => {
          const osc = ctx.createOscillator()
          osc.type = 'sine'
          osc.frequency.setValueAtTime(freq, now + idx * 0.1)
          osc.connect(gain)

          gain.gain.setValueAtTime(volume * 0.6, now + idx * 0.1)
          gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.1 + 0.6)

          osc.start(now + idx * 0.1)
          osc.stop(now + idx * 0.1 + 0.6)
        })
      } else if (type === 'marimba') {
        // Soft Marimba (柔和木鱼/木琴)
        const notes = [440, 554.37, 659.25]
        notes.forEach((freq, idx) => {
          const osc = ctx.createOscillator()
          osc.type = 'triangle'
          osc.frequency.setValueAtTime(freq, now + idx * 0.12)
          osc.connect(gain)

          gain.gain.setValueAtTime(volume * 0.8, now + idx * 0.12)
          gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.12 + 0.4)

          osc.start(now + idx * 0.12)
          osc.stop(now + idx * 0.12 + 0.4)
        })
      } else if (type === 'cyber') {
        // Cyber Pulse (科技和声)
        const osc = ctx.createOscillator()
        osc.type = 'sawtooth'
        osc.frequency.setValueAtTime(220, now)
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.3)
        osc.connect(gain)

        gain.gain.setValueAtTime(volume * 0.5, now)
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35)

        osc.start(now)
        osc.stop(now + 0.35)
      } else if (type === 'beep') {
        // Beep Alert (警报哔哔)
        [0, 0.18, 0.36].forEach((timeOffset) => {
          const osc = ctx.createOscillator()
          osc.type = 'square'
          osc.frequency.setValueAtTime(880, now + timeOffset)
          osc.connect(gain)

          gain.gain.setValueAtTime(volume * 0.4, now + timeOffset)
          gain.gain.linearRampToValueAtTime(0.001, now + timeOffset + 0.1)

          osc.start(now + timeOffset)
          osc.stop(now + timeOffset + 0.1)
        })
      }
    } catch (e) {
      console.warn('Audio Synthesis failed:', e)
    }
  }
}

export const soundPlayer = new SoundSynth()
