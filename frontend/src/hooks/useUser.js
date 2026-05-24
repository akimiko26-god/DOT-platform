import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'

export function useUser() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(() => {
    const token = localStorage.getItem('dot_token')
    if (!token) {
      setUser(null)
      setLoading(false)
      return Promise.resolve()
    }
    setLoading(true)
    return api('/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  const permsFor = (companyId) => {
    const row = user?.companies_access?.find((c) => c.company_id === companyId)
    return row?.permissions || {}
  }

  return { user, loading, reload, permsFor, isAdmin: !!user?.is_admin }
}
