import React from 'react'
import { useStore } from '../store'

export default function DockPlayer(){
  const current = useStore(s=>s.tracks[0])
  return (
    <div className='h-20 border-t border-slate-700 flex items-center px-4'>
      <div className='flex-1'>{current ? `${current.title} — ${current.artist}` : 'No track'}</div>
      <div>
        <button className='mx-2'>⏮</button>
        <button className='mx-2'>▶</button>
        <button className='mx-2'>⏭</button>
      </div>
    </div>
  )
}
