import React, { useState } from 'react'
import api from '../api'

export default function TopbarSearch(){
  const [q, setQ] = useState('')
  const [suggestions, setSuggestions] = useState([])

  async function onChange(val:string){
    setQ(val)
    if(val.length < 2) { setSuggestions([]); return }
    try{
      const r = await api.get('/api/tracks', { params: { q: val, limit: 10 } })
      setSuggestions(r.data)
    }catch(e){ console.error(e) }
  }

  return (
    <div className='flex items-center space-x-2'>
      <input value={q} onChange={(e)=>onChange(e.target.value)} className='px-2 py-1 bg-slate-800 rounded' placeholder='Search library...'/>
      {suggestions.length>0 && (
        <div className='absolute mt-10 bg-slate-800 rounded shadow p-2'>
          {suggestions.map((s:any)=> <div key={s.id} className='p-1 text-sm'>{s.title} — {s.artist}</div>)}
        </div>
      )}
    </div>
  )
}
