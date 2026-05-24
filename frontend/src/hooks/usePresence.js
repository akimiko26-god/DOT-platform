import { useEffect } from 'react'
import { api } from '../api/client'

export function usePresence() {
  useEffect(() => {
    const token = localStorage.getItem('dot_token')
    if (!token) return undefined
    const ping = () => api('/auth/ping', { method: 'POST' }).catch(() => {})
    ping()
    const id = setInterval(ping, 60000)
    return () => clearInterval(id)
  }, [])
}
