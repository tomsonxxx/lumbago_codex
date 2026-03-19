import create from 'zustand'

interface Track { id?: number; title?: string; artist?: string; bpm?: number; key?: string; duration?: number; waveform_path?: string }

interface AppState {
  tracks: Track[]
  setTracks: (t: Track[]) => void
  currentTrack: Track | null
  setCurrentTrack: (t: Track | null) => void
  filters: any
  setFilters: (f: any) => void
}

export const useStore = create<AppState>((set)=>({
  tracks: [],
  setTracks: (t)=> set({tracks: t}),
  currentTrack: null,
  setCurrentTrack: (t)=> set({currentTrack: t}),
  filters: { q: '', bpm_min: null, bpm_max: null, key: '' },
  setFilters: (f)=> set({filters: {...f}})
}))
