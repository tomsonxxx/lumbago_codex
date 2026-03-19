import React, { useEffect, useState } from 'react'
import api from '../../api'
import { useStore } from '../../store'

interface TrackListProps {
  tracks?: any[]
  onSelect?: (id: number) => void
}

export default function TrackList({ tracks: propsTracks, onSelect }: TrackListProps = {}){
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(0)
  const [limit, setLimit] = useState(25)
  const [sort, setSort] = useState('created_at')
  const [q, setQ] = useState('')
  const setTracks = useStore(s=>s.setTracks)
  const storeTracks = useStore(s=>s.tracks)
  
  const tracks = propsTracks || storeTracks

  useEffect(()=>{ 
    if (!propsTracks) fetch() 
  }, [page, limit, sort, q, propsTracks])

  async function fetch(){
    setLoading(true)
    try{
      const res = await api.get('/api/tracks', { params: { skip: page*limit, limit, sort, q } })
      setTracks(res.data)
    }catch(e){ console.error(e) }
    setLoading(false)
  }

  return (
    <div className='p-4'>
      {!propsTracks && (
      <div className='flex items-center justify-between mb-3'>
        <div className='flex items-center space-x-2'>
          <input value={q} onChange={(e)=>setQ(e.target.value)} className='px-2 py-1 bg-slate-800 rounded' placeholder='Search...'/>
          <select value={sort} onChange={(e)=>setSort(e.target.value)} className='px-2 py-1 bg-slate-800 rounded'>
            <option value='created_at'>Newest</option>
            <option value='title'>Title</option>
            <option value='bpm'>BPM</option>
          </select>
        </div>
        <div>
          <button className='px-3 py-1 bg-slate-700 rounded mr-2' onClick={()=>setPage(Math.max(0,page-1))}>Prev</button>
          <button className='px-3 py-1 bg-slate-700 rounded' onClick={()=>setPage(page+1)}>Next</button>
        </div>
      </div>
      )}

      <div className='bg-slate-800 rounded'>
        <table className='w-full text-left'>
          <thead className='text-slate-400 text-sm'>
            <tr>
              <th className='p-2'>Title</th>
              <th className='p-2'>Artist</th>
              <th className='p-2'>BPM</th>
              <th className='p-2'>Key</th>
              <th className='p-2'>Duration</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={5} className='p-4'>Loading...</td></tr>}
            {!loading && tracks.length===0 && <tr><td colSpan={5} className='p-4'>No tracks</td></tr>}
            {!loading && tracks.map((t:any)=> (
              <tr 
                key={t.id} 
                className='border-t border-slate-700 hover:bg-slate-700 cursor-pointer'
                onClick={() => onSelect && onSelect(t.id)}
              >
                <td className='p-2'>{t.title}</td>
                <td className='p-2'>{t.artist || '-'}</td>
                <td className='p-2'>{t.bpm || '-'}</td>
                <td className='p-2'>{t.key || '-'}</td>
                <td className='p-2'>{t.duration ? new Date(t.duration*1000).toISOString().substr(14,5) : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}