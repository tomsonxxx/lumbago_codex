import React, { useEffect, useState } from 'react'
import api from '../../api'

export default function DuplicateFinderModal({ onClose }: any){
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<any[]>([])

  async function runFinder(){
    setRunning(true)
    try{
      // This would call backend /api/duplicates/find in real app
      const res = await api.post('/api/duplicates/find', { scope: 'library' })
      setResults(res.data || [])
    }catch(e){
      console.error(e)
    }finally{ setRunning(false) }
  }

  useEffect(()=>{ runFinder() }, [])

  return (
    <div className='p-4 bg-slate-900 text-slate-100 rounded shadow-lg w-full max-w-3xl'>
      <h3 className='text-lg font-semibold'>Duplicate Finder</h3>
      {running && <p>Scanning library for duplicates...</p>}
      {!running && results.length===0 && <p>No duplicates found.</p>}
      {!running && results.map((g:any, idx:number)=> (
        <div key={idx} className='mt-3 p-2 bg-slate-800 rounded'>
          <div className='text-sm text-slate-400'>Group {idx+1} — {g.tracks.length} items</div>
          <ul className='mt-2 text-sm'>
            {g.tracks.map((t:any,i:number)=> (
              <li key={i}>{t.title} — {t.artist}</li>
            ))}
          </ul>
        </div>
      ))}
      <div className='mt-3 flex justify-end'>
        <button className='px-3 py-1 bg-slate-700 rounded mr-2' onClick={onClose}>Close</button>
      </div>
    </div>
  )
}
