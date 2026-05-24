import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'

function validId(id) {
  return Number.isFinite(id) && id > 0
}

export function useCompany() {
  const [companies, setCompanies] = useState([])
  const [companyId, setCompanyId] = useState(() => {
    const raw = Number(localStorage.getItem('dot_company_id'))
    return validId(raw) ? raw : null
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const reload = useCallback(() => {
    setLoading(true)
    setError('')
    return api('/companies')
      .then((list) => {
        setCompanies(list)
        const stored = Number(localStorage.getItem('dot_company_id'))
        const id = validId(stored) && list.some((c) => c.id === stored)
          ? stored
          : list[0]?.id ?? null
        setCompanyId(id)
        if (id) localStorage.setItem('dot_company_id', String(id))
        else localStorage.removeItem('dot_company_id')
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  const select = (id, options = {}) => {
    if (!validId(id)) return
    setCompanyId(id)
    localStorage.setItem('dot_company_id', String(id))
    if (options.reload) {
      window.location.reload()
    }
  }

  const company = companies.find((c) => c.id === companyId)

  return { companies, company, companyId, select, loading, error, setCompanies, reload }
}
