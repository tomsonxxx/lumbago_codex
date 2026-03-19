import React, { useEffect, useState } from 'react'
import api from '../../api'
import { useStore } from '../../store'

interface TrackDetailPanelProps {
  selectedId?: number | null
}

export default function TrackDetailPanel({ selectedId }: TrackDetailPanelProps = {}){
  const tracks = useStore(s=>s.tracks)
  const [current, setCurrent] = useState<any>(null)
  
  useEffect(() => {
    async function resolveTrack() {
      if (selectedId) {
        const found = tracks.find((t: any) => t.id === selectedId)
        if (found) {
          setCurrent(found)
        } else {
          try {
            const r = await api.get(`/api/tracks/${selectedId}`)
            setCurrent(r.data)
          } catch(e) { console.error(e) }
        }
      } else {
        setCurrent(tracks.length > 0 ? tracks[0] : null)
      }
    }
    resolveTrack()
  }, [selectedId, tracks])

  const [waveformUrl, setWaveformUrl] = useState(null)

  useEffect(()=>{
    if(!current) return
    setWaveformUrl(current.waveform_path || null)
    if(!current.waveform_path && current.id) fetchWaveform(current.id)
  }, [current])

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
        {waveformUrl ? <img src={waveformUrl} alt='waveform'/> : <p className='text-xs text-slate-400'>Waveform not available</p>}
        <p className='text-xs text-slate-400'>BPM: {current.bpm || '-'}</p>
        <p className='text-xs text-slate-400'>Key: {current.key || '-'}</p>
      </div>
    </div>
  )
}