import React, { useState } from 'react'
export default function FilterPanel({onApply}:any){
  const [bpmMin, setBpmMin] = useState('')
  const [bpmMax, setBpmMax] = useState('')
  const [key, setKey] = useState('')
  function apply(){
    onApply({bpm_min: bpmMin?parseInt(bpmMin):undefined, bpm_max: bpmMax?parseInt(bpmMax):undefined, key: key||undefined})
  }
  return (
    <div className='w-72 p-4 border-r border-slate-700'>
      <h4 className='text-sm font-semibold mb-2 text-slate-300'>Filters</h4>
      <div className='mb-3'>
        <label className='text-xs text-slate-400'>BPM Range</label>
        <div className='flex space-x-2 mt-1'>
          <input value={bpmMin} onChange={e=>setBpmMin(e.target.value)} className='w-1/2 p-1 bg-slate-800 rounded' placeholder='min' />
          <input value={bpmMax} onChange={e=>setBpmMax(e.target.value)} className='w-1/2 p-1 bg-slate-800 rounded' placeholder='max' />
        </div>
      </div>
      <div className='mb-3'>
        <label className='text-xs text-slate-400'>Key</label>
        <select value={key} onChange={e=>setKey(e.target.value)} className='w-full p-1 bg-slate-800 rounded mt-1'>
          <option value=''>Any</option>
          <option>9A</option>
          <option>10A</option>
        </select>
      </div>
      <div className='flex justify-end'>
        <button className='px-3 py-1 bg-slate-700 rounded' onClick={apply}>Apply</button>
      </div>
    </div>
  )
}
