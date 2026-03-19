import React from 'react'
import { useStore } from '../../store'

interface TrackGridProps {
  tracks?: any[]
  onSelect?: (id: number) => void
}

export default function TrackGrid({ tracks: propsTracks, onSelect }: TrackGridProps = {}){
  const storeTracks = useStore(s=>s.tracks)
  const tracks = propsTracks || storeTracks
  
  return (
    <div className='p-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4'>
      {tracks.map((t:any)=> (
        <div key={t.id} className='bg-slate-800 rounded overflow-hidden relative group'>
          <div className='h-40 flex items-center justify-center'>
            <div className='text-sm text-slate-400'>{t.metadata && t.metadata.artwork ? <img src={t.metadata.artwork} alt='' /> : 'No Artwork'}</div>
          </div>
          <div className='p-2'>
            <div className='font-semibold text-sm'>{t.title}</div>
            <div className='text-xs text-slate-400'>{t.artist}</div>
          </div>
          <div className='absolute inset-0 bg-black bg-opacity-30 opacity-0 group-hover:opacity-100 transition flex items-center justify-center space-x-2'>
            <button className='px-3 py-1 bg-white text-black rounded' onClick={() => onSelect && onSelect(t.id)}>Play</button>
            <button className='px-3 py-1 bg-white text-black rounded' onClick={() => onSelect && onSelect(t.id)}>Tag</button>
          </div>
        </div>
      ))}
    </div>
  )
}