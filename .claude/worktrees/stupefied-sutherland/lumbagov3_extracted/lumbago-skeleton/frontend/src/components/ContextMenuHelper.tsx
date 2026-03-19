import React from 'react'
export default function ContextMenuHelper({x,y,items}:{x:number,y:number,items:any[]}){
  return (
    <div style={{left:x,top:y}} className='absolute bg-slate-800 rounded shadow p-2'>
      {items.map((it:any,i:number)=>(<div key={i} className='p-1 hover:bg-slate-700 cursor-pointer'>{it.label}</div>))}
    </div>
  )
}
