import React, { useEffect, useState } from 'react'
import api from '../../api'
import { useStore } from '../../store'
import { useQuery } from '@tanstack/react-query'

function fetchTracks(params:any){
  return api.get('/api/tracks', { params }).then(r=>r.data)
}

export default function EnhancedTrackList(){
  const [page, setPage] = useState(0)
  const [limit] = useState(50)
  const setTracks = useStore(s=>s.setTracks)
  const tracks = useStore(s=>s.tracks)
  const filters = useStore(s=>s.filters)
  const setCurrentTrack = useStore(s=>s.setCurrentTrack)
  const [debouncedFilters, setDebouncedFilters] = useState(filters)

  // debounce filters
  useEffect(()=>{
    const t = setTimeout(()=> setDebouncedFilters(filters), 350)
    return ()=> clearTimeout(t)
  }, [filters])

  const { data, isLoading, refetch } = useQuery(['tracks', debouncedFilters, page], ()=> fetchTracks({ ...debouncedFilters, skip: page*limit, limit }), { keepPreviousData: true })

  useEffect(()=>{ if(data) setTracks(data) }, [data])

  function onRowClick(t:any){ setCurrentTrack(t) }

  return (
    <div className='bg-slate-800 rounded p-3 mb-4'>
      <div className='flex items-center justify-between mb-2'>
        <div className='flex items-center space-x-2'>
          <label className='text-sm text-slate-400'>Sort:</label>
          <select className='bg-slate-700 p-1 rounded text-sm'>
            <option value='title'>Title</option>
            <option value='artist'>Artist</option>
            <option value='bpm'>BPM</option>
          </select>
        </div>
        <div>
          <button className='px-3 py-1 bg-slate-700 rounded'>Import</button>
          <button className='px-3 py-1 bg-slate-700 rounded ml-2'>Scan</button>
        </div>
      </div>

      <table className='w-full text-left'>
        <thead className='text-slate-400 text-sm'>
          <tr>
            <th className='p-2'>Title</th>
            <th className='p-2'>Artist</th>
            <th className='p-2'>BPM</th>
            <th className='p-2'>Key</th>
          </tr>
        </thead>
        <tbody>
          {isLoading && <tr><td colSpan={4} className='p-4'>Loading...</td></tr>}
          {!isLoading && (!tracks || tracks.length===0) && <tr><td colSpan={4} className='p-4'>No tracks</td></tr>}
          {!isLoading && tracks && tracks.map((t:any)=> (
            <tr key={t.id} className='border-t border-slate-700 hover:bg-slate-900 cursor-pointer' onClick={()=>onRowClick(t)}>
              <td className='p-2'>{t.title}</td>
              <td className='p-2'>{t.artist || '-'}</td>
              <td className='p-2'>{t.bpm || '-'}</td>
              <td className='p-2'>{t.key || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className='mt-3 flex justify-between'>
        <div className='text-sm text-slate-400'>Page {page+1}</div>
        <div>
          <button className='px-2 py-1 bg-slate-700 rounded mr-2' onClick={()=>setPage(p=>Math.max(0,p-1))}>Prev</button>
          <button className='px-2 py-1 bg-slate-700 rounded' onClick={()=>setPage(p=>p+1)}>Next</button>
        </div>
      </div>
    </div>
  )
}
