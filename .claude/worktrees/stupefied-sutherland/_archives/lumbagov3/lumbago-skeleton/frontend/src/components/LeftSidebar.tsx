import React from 'react'
import Playlists from './Playlists'

export default function LeftSidebar(){
  return (
    <div className='w-60 border-r border-slate-700 p-4 text-sm'>
      <h2 className='font-semibold mb-3'>Library</h2>
      <Playlists />
      <div className='mt-6'>
        <h4 className='text-xs text-slate-400 uppercase'>Sources</h4>
        <ul className='mt-2 text-sm'>
          <li>Local Disk</li>
          <li>External Drive</li>
          <li>Cloud (S3)</li>
        </ul>
      </div>
    </div>
  )
}
