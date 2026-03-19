import React, { useEffect, useState } from 'react'
import TrackList from './TrackList'
import TrackGrid from './TrackGrid'
import FilterPanel from './FilterPanel'
import TrackDetailPanel from './TrackDetailPanel'
import api from '../../api'

export default function LibraryBrowser(){
  const [view, setView] = useState<'list'|'grid'>('list')
  const [tracks, setTracks] = useState<any[]>([])
  const [filters, setFilters] = useState<any>({})
  const [selected, setSelected] = useState<number|null>(null)

  useEffect(()=>{ fetchTracks() }, [filters])

  async function fetchTracks(){
    try{
      const res = await api.get('/api/library/tracks', { params: filters })
      setTracks(res.data)
    }catch(e){ console.error(e) }
  }

  return (
    <div className='flex'>
      <FilterPanel setFilters={setFilters} />
      <div className='flex-1 p-4'>
        <div className='flex items-center justify-between mb-3'>
          <div>
            <button onClick={()=>setView('list')} className='px-2 py-1 mr-2 bg-slate-700 rounded'>List</button>
            <button onClick={()=>setView('grid')} className='px-2 py-1 bg-slate-700 rounded'>Grid</button>
          </div>
          <div>
            <input placeholder='Search' className='px-2 py-1 bg-slate-800 rounded' onChange={e=>setFilters({...filters, q: e.target.value})} />
          </div>
        </div>
        {view==='list' ? <TrackList tracks={tracks} onSelect={setSelected} /> : <TrackGrid tracks={tracks} onSelect={setSelected} />}
      </div>
      <TrackDetailPanel selectedId={selected} />
    </div>
  )
}
