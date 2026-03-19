import React, { useState, useEffect } from 'react'
import { useStore } from '../store'

export default function FilterPanel(){
  const filters = useStore(s=>s.filters)
  const setFilters = useStore(s=>s.setFilters)
  const [q, setQ] = useState(filters.q || '')
  const [bmin, setBmin] = useState(filters.bpm_min || '')
  const [bmax, setBmax] = useState(filters.bpm_max || '')
  const [key, setKey] = useState(filters.key || '')

  useEffect(()=>{
    // on mount, sync
    setQ(filters.q || '')
    setBmin(filters.bpm_min || '')
    setBmax(filters.bpm_max || '')
    setKey(filters.key || '')
  }, [])

  function apply(){
    setFilters({ q: q || '', bpm_min: bmin ? Number(bmin): null, bpm_max: bmax ? Number(bmax): null, key: key || '' })
  }

  return (
    <div className='w-72 p-4 border-r border-slate-700'>
      <h4 className='text-sm font-semibold mb-2 text-slate-300'>Filters</h4>
      <div className='mb-3'>
        <label className='text-xs text-slate-400'>Search</label>
        <input className='w-full p-1 bg-slate-800 rounded mt-1' value={q} onChange={e=>setQ(e.target.value)} placeholder='artist, title, genre' />
      </div>
      <div className='mb-3'>
        <label className='text-xs text-slate-400'>BPM Range</label>
        <div className='flex space-x-2 mt-1'>
          <input className='w-1/2 p-1 bg-slate-800 rounded' value={bmin} onChange={e=>setBmin(e.target.value)} placeholder='min' />
          <input className='w-1/2 p-1 bg-slate-800 rounded' value={bmax} onChange={e=>setBmax(e.target.value)} placeholder='max' />
        </div>
      </div>
      <div className='mb-3'>
        <label className='text-xs text-slate-400'>Key</label>
        <select className='w-full p-1 bg-slate-800 rounded mt-1' value={key} onChange={e=>setKey(e.target.value)}>
          <option value=''>Any</option>
          <option>9A</option>
          <option>10A</option>
        </select>
      </div>
      <div className='flex space-x-2'>
        <button className='px-3 py-1 bg-slate-700 rounded' onClick={apply}>Apply</button>
        <button className='px-3 py-1 bg-slate-700 rounded' onClick={()=>{ setQ(''); setBmin(''); setBmax(''); setKey(''); setFilters({ q:'', bpm_min:null, bpm_max:null, key:'' })}}>Clear</button>
      </div>
    </div>
  )
}
