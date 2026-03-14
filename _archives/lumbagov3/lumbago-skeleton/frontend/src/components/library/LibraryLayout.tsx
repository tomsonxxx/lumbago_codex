import React from 'react'
import Sidebar from '../Sidebar'
import FilterPanel from '../FilterPanel'
import EnhancedTrackList from './EnhancedTrackList'
import TrackGrid from './TrackGrid'
import TrackDetailPanel from '../TrackDetailPanel'
import DockPlayer from '../DockPlayer'

export default function LibraryLayout(){
  return (
    <div className='flex flex-col min-h-screen'>
      <div className='flex flex-1'>
        <Sidebar />
        <FilterPanel />
        <div className='flex-1 p-4'>
          <EnhancedTrackList />
          <TrackGrid />
        </div>
        <TrackDetailPanel />
      </div>
      <DockPlayer />
    </div>
  )
}
