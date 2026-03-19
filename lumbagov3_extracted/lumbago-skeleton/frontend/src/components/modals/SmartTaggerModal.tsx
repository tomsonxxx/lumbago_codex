import React, { useEffect, useState } from 'react'
import api from '../../api'

export default function SmartTaggerModal({ trackId, onClose }: any) {
  const [jobId, setJobId] = useState<string|null>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(()=>{
    startAnalysis()
  }, [trackId])

  async function startAnalysis(){
    setLoading(true)
    try{
      const res = await api.post('/api/ai/analyze', { track_id: trackId, ops: { bpm: true, key: true, tagger: true } })
      setJobId(res.data.job_id || res.data.job_id)
      pollResult(res.data.job_id || res.data.job_id)
    }catch(e){
      console.error(e)
    }finally{ setLoading(false) }
  }

  function pollResult(id:string){
    const iv = setInterval(async ()=>{
      try{
        const r = await api.get(`/api/ai/jobs/${id}`)
        if(r.data.status === 'finished' || r.data.state === 'SUCCESS'){
          setResult(r.data.result || r.data)
          clearInterval(iv)
        }
      }catch(e){
        console.error(e)
      }
    }, 1500)
  }

  return (
    <div className='p-4 bg-slate-900 text-slate-100 rounded shadow-lg'>
      <h3 className='text-lg font-semibold'>Smart Tagger</h3>
      {loading && <p>Uruchamianie analizy...</p>}
      {result && (
        <div className='mt-3'>
          <p>Proponowane tagi:</p>
          <pre className='text-sm bg-slate-800 p-2 rounded'>{JSON.stringify(result, null, 2)}</pre>
          <div className='mt-2'>
            <button className='px-3 py-1 bg-green-600 rounded mr-2'>Accept</button>
            <button className='px-3 py-1 bg-red-600 rounded' onClick={onClose}>Reject</button>
          </div>
        </div>
      )}
      {!result && !loading && <p>Oczekiwanie na wynik...</p>}
    </div>
  )
}
