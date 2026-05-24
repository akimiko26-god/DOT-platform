import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useCompany } from '../hooks/useCompany'

export default function CompanyHub() {
  const { companies, companyId, select, reload, loading, error } = useCompany()
  const [newCo, setNewCo] = useState({ name: '', slug: '' })
  const [msg, setMsg] = useState('')

  const create = async (e) => {
    e.preventDefault()
    setMsg('')
    try {
      const c = await api('/companies', { method: 'POST', body: JSON.stringify(newCo) })
      localStorage.setItem('dot_company_id', String(c.id))
      setNewCo({ name: '', slug: '' })
      await reload()
      setMsg('Компания создана')
    } catch (err) {
      setMsg(err.message)
    }
  }

  const onName = (name) => {
    setNewCo({
      name,
      slug: name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40),
    })
  }

  if (loading) return <p>Загрузка…</p>
  if (error) return <p style={{ color: 'var(--danger)' }}>{error}</p>

  return (
    <div>
      <h1>Мои компании</h1>
      <p style={{ color: 'var(--muted)', marginBottom: '1.25rem' }}>
        Здесь можно добавить новые компании и переключаться между ними
      </p>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {companies.map((c) => (
          <div key={c.id} className={`card ${c.id === companyId ? 'company-active' : ''}`}>
            <h3>{c.name}</h3>
            <p style={{ color: 'var(--muted)' }}>/c/{c.slug}</p>
            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button type="button" className="btn btn-outline" onClick={() => select(c.id)}>
                {c.id === companyId ? 'Активна' : 'Выбрать'}
              </button>
              <Link className="btn" to="/app/settings">Настроить</Link>
              <Link className="btn btn-outline" to={`/c/${c.slug}`} target="_blank">Сайт</Link>
            </div>
          </div>
        ))}
      </div>

      <form className="card" onSubmit={create}>
        <h3>Добавить компанию</h3>
        <div className="field">
          <label>Название</label>
          <input value={newCo.name} onChange={(e) => onName(e.target.value)} required />
        </div>
        <div className="field">
          <label>Адрес страницы (латиница)</label>
          <input value={newCo.slug} onChange={(e) => setNewCo({ ...newCo, slug: e.target.value })} pattern="^[a-z0-9-]+$" required />
        </div>
        {msg && <p style={{ marginBottom: '0.75rem', color: msg.includes('создан') ? 'var(--success)' : 'var(--danger)' }}>{msg}</p>}
        <button className="btn" type="submit">Создать компанию</button>
      </form>
    </div>
  )
}
