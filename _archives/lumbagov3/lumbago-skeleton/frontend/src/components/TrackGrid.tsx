import React from 'react'
import { useStore } from '../store'

export default function TrackGrid(){
  const tracks = useStore(s=>s.tracks)
  return (
    <div className='p-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4'>
      {tracks.map((t:any)=> (
        <div key={t.id} className='bg-slate-800 rounded overflow-hidden'>
          <div className='h-40 flex items-center justify-center'>
            <div className='text-sm text-slate-400'>No Artwork</div>
          </div>
          <div className='p-2'>
            <div className='font-semibold text-sm'>{t.title}</div>
            <div className='text-xs text-slate-400'>{t.artist}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
