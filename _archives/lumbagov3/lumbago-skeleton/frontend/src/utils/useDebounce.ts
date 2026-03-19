import { useEffect, useState } from 'react'

export default function useDebounce(value:any, delay:number=300){
  const [v, setV] = useState(value)
  useEffect(()=>{
    const id = setTimeout(()=>setV(value), delay)
    return ()=>clearTimeout(id)
  }, [value, delay])
  return v
}
