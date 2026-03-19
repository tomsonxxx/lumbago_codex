import React, { useState } from 'react'
import { useStore } from '../store'
import api from '../api'

export default function TrackDetailPanel(){
  const current = useStore(s=>s.currentTrack)
  const setCurrent = useStore(s=>s.setCurrentTrack)
  const [loading, setLoading] = useState(false)

  if(!current) return <div className='w-80 p-4'>No track selected</div>

  async function genWave(){
    setLoading(true)
    try{
      const res = await api.post('/api/waveform/generate', { track_id: current.id })
      // expect { waveform_path }
      if(res.data && res.data.waveform_path){
        setCurrent({ ...current, waveform_path: res.data.waveform_path })
      }
    }catch(e){ console.error(e) }
    setLoading(false)
  }

  return (
    <div className='w-80 p-4 border-l border-slate-700'>
      <h3 className='font-semibold'>{current.title}</h3>
      <p className='text-sm text-slate-400'>{current.artist}</p>
      <div className='mt-3'>
        <p className='text-xs text-slate-400'>BPM: {current.bpm || '-'}</p>
        <p className='text-xs text-slate-400'>Key: {current.key || '-'}</p>
        <p className='text-xs text-slate-400'>Duration: {current.duration || '-'}</p>
      </div>
      <div className='mt-3'>
        {current.waveform_path ? (
          <img src={current.waveform_path} alt='waveform' className='w-full h-24 object-cover' />
        ) : (
          <div className='w-full h-24 bg-slate-800 flex items-center justify-center text-slate-400'>No waveform</div>
        )}
      </div>
      <div className='mt-3'>
        <button className='px-3 py-1 bg-green-600 rounded mr-2' onClick={genWave} disabled={loading}>{loading? 'Generating...':'Generate waveform'}</button>
        <button className='px-3 py-1 bg-red-600 rounded' onClick={()=>setCurrent(null)}>Close</button>
      </div>
    </div>
  )
}
