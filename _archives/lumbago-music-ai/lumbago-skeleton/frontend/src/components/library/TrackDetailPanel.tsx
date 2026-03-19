import React, { useEffect, useState } from 'react'
import api from '../../api'
import { useStore } from '../../store'

interface TrackDetailPanelProps {
  selectedId?: number | null;
}

export default function TrackDetailPanel({ selectedId }: TrackDetailPanelProps){
  const tracks = useStore(s=>s.tracks)
  const [localTrack, setLocalTrack] = useState<any>(null)
  const [waveformUrl, setWaveformUrl] = useState<string|null>(null)

  // Use selectedId if provided to find the track in current store or fetch it, 
  // otherwise fallback to first track in store (original behavior)
  const current = selectedId 
    ? (tracks.find((t:any) => t.id === selectedId) || localTrack) 
    : tracks[0]

  useEffect(() => {
    if (selectedId && !tracks.find((t:any) => t.id === selectedId)) {
        // Fetch specific track if not in store
        fetchTrack(selectedId)
    } else {
        setLocalTrack(null)
    }
  }, [selectedId, tracks])

  useEffect(()=>{
    if(!current) return
    if(current.waveform_path) setWaveformUrl(current.waveform_path)
    else fetchWaveform(current.id)
  }, [current])

  async function fetchTrack(id: number) {
      try {
          const r = await api.get(`/api/tracks/${id}`)
          setLocalTrack(r.data)
      } catch (e) { console.error(e) }
  }

  async function fetchWaveform(id:number){
    try{
      const r = await api.get(`/api/tracks/${id}`)
      if(r.data && r.data.waveform_path) setWaveformUrl(r.data.waveform_path)
    }catch(e){ console.error(e) }
  }

  if(!current) return <div className='w-80 p-4'>No track selected</div>
  return (
    <div className='w-80 p-4 border-l border-slate-700'>
      <h3 className='font-semibold'>{current.title}</h3>
      <p className='text-sm text-slate-400'>{current.artist}</p>
      <div className='mt-3'>
        {waveformUrl ? <img src={waveformUrl} alt='waveform' className='w-full h-24 object-cover'/> : <p className='text-xs text-slate-400'>Waveform not available</p>}
        <p className='text-xs text-slate-400'>BPM: {current.bpm || '-'}</p>
        <p className='text-xs text-slate-400'>Key: {current.key || '-'}</p>
      </div>
    </div>
  )
}