import React, { useEffect, useState } from 'react'
import axios from 'axios'

export default function LibraryBrowser(){
  const [tracks, setTracks] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(()=>{ fetchTracks() }, [])

  async function fetchTracks(){
    setLoading(true)
    try{
      const res = await axios.get(((import.meta as any).env.VITE_API_URL||'http://localhost:8000') + '/api/tracks')
      setTracks(res.data)
    }catch(e){
      console.error(e)
    }finally{
      setLoading(false)
    }
  }

  return (
    <div className='p-4'>
      <div className='mb-4 flex items-center justify-between'>
        <h2 className='text-lg font-semibold'>Library</h2>
        <div>
          <button className='px-3 py-1 bg-slate-700 rounded mr-2'>Import</button>
          <button className='px-3 py-1 bg-slate-700 rounded'>Scan</button>
        </div>
      </div>
      <div className='bg-slate-800 rounded shadow overflow-hidden'>
        <table className='w-full text-left'>
          <thead className='text-slate-400 text-sm'>
            <tr>
              <th className='p-3'>Title</th>
              <th className='p-3'>Artist</th>
              <th className='p-3'>BPM</th>
              <th className='p-3'>Key</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={4} className='p-4'>Loading...</td></tr>}
            {!loading && tracks.length===0 && <tr><td colSpan={4} className='p-4'>No tracks</td></tr>}
            {!loading && tracks.map((t:any)=>(
              <tr key={t.id} className='border-t border-slate-700'>
                <td className='p-3'>{t.title}</td>
                <td className='p-3'>{t.artist||'-'}</td>
                <td className='p-3'>{t.bpm||'-'}</td>
                <td className='p-3'>{t.key||'-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}