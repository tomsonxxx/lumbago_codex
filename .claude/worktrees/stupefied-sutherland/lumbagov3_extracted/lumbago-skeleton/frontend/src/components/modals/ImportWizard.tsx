
import React, { useState } from 'react'
import api from '../../api'

export default function ImportWizard({onClose}:any){
  const [folder, setFolder] = useState('')
  const [files, setFiles] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  async function scan(){
    setLoading(true)
    try{
      const r = await api.post('/api/import/scan', {folder})
      setFiles(r.data.files || [])
    }catch(e){ console.error(e) }
    setLoading(false)
  }

  return (
    <div className='p-4 bg-slate-900 rounded text-slate-100 w-full max-w-xl'>
      <h3 className='text-lg font-semibold mb-3'>Import Wizard</h3>

      <div className='mb-3'>
        <label className='text-sm text-slate-400'>Folder path</label>
        <input value={folder} onChange={e=>setFolder(e.target.value)}
               className='w-full p-2 bg-slate-800 rounded mt-1' placeholder='/music/'/>
      </div>

      <button onClick={scan} className='px-4 py-1 bg-slate-700 rounded'>
        Scan
      </button>

      {loading && <p className='mt-4'>Scanning...</p>}

      {!loading && files.length>0 && (
        <div className='mt-4 max-h-64 overflow-auto bg-slate-800 p-2 rounded'>
          {files.map((f:any,i:number)=>(
            <div key={i} className='text-sm p-1 border-b border-slate-700'>
              {f.filename}
            </div>
          ))}
        </div>
      )}

      <div className='mt-4 flex justify-end'>
        <button onClick={onClose} className='px-3 py-1 bg-slate-700 rounded'>Close</button>
      </div>
    </div>
  )
}
