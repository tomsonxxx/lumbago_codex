import React, { useState } from 'react'
import TopbarSearch from './components/TopbarSearch'
import LeftSidebar from './components/LeftSidebar'
import FilterPanel from './components/library/FilterPanel'
import TrackList from './components/library/TrackList'
import TrackGrid from './components/library/TrackGrid'
import TrackDetailPanel from './components/library/TrackDetailPanel'
import DockPlayer from './components/DockPlayer'

export default function App(){
  const [view, setView] = useState('list')
  return (
    <div className='min-h-screen bg-slate-900 text-slate-100 flex flex-col'>
      <header className='p-4 border-b border-slate-700 flex items-center justify-between'>
        <h1 className='text-xl font-semibold'>Lumbago Music AI</h1>
        <div className='flex items-center space-x-4'><TopbarSearch/></div>
      </header>
      <div className='flex flex-1'>
        <LeftSidebar/>
        <FilterPanel onApply={(f:any)=>console.log('apply filters',f)} />
        <main className='flex-1 p-4 overflow-auto'>
          <div className='mb-4'>
            <button onClick={()=>setView('list')} className='px-3 py-1 bg-slate-700 rounded mr-2'>List</button>
            <button onClick={()=>setView('grid')} className='px-3 py-1 bg-slate-700 rounded'>Grid</button>
          </div>
          {view==='list' ? <TrackList/> : <TrackGrid/>}
        </main>
        <TrackDetailPanel/>
      </div>
      <DockPlayer/>
    </div>
  )
}
