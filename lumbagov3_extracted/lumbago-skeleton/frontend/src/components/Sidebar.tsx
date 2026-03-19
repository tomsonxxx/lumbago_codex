import React from 'react'
export default function Sidebar(){
  return (
    <div className='w-60 border-r border-slate-700 p-4'>
      <h3 className='text-sm font-semibold'>Library</h3>
      <ul className='mt-3 text-sm space-y-2'>
        <li>All Tracks</li>
        <li>Favorites</li>
        <li>Recently Added</li>
      </ul>
    </div>
  )
}
