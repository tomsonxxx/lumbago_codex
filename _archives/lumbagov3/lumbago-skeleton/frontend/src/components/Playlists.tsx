import React from 'react'
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'
import api from '../api'

export default function Playlists(){
  const [playlists, setPlaylists] = React.useState<any[]>([])

  React.useEffect(()=>{ fetchPlaylists() }, [])
  async function fetchPlaylists(){
    try{ const r = await api.get('/api/playlists'); setPlaylists(r.data) }catch(e){console.error(e)}
  }

  function onDragEnd(result:any){
    if(!result.destination) return;
    const items = Array.from(playlists);
    const [reordered] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reordered);
    setPlaylists(items);
    // optionally: persist order to backend
  }

  return (
    <div className='p-4'>
      <h4 className='font-semibold mb-3'>Playlists</h4>
      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId='pls'>
          {(provided)=> (
            <div ref={provided.innerRef} {...provided.droppableProps} className='space-y-2'>
              {playlists.map((pl, idx)=> (
                <Draggable key={pl.id} draggableId={String(pl.id)} index={idx}>
                  {(prov)=> (
                    <div ref={prov.innerRef} {...prov.draggableProps} {...prov.dragHandleProps} className='p-2 bg-slate-800 rounded'>
                      {pl.name}
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>
    </div>
  )
}
