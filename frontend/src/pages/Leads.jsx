import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import CompanyPicker from '../components/CompanyPicker'
import { useCompany } from '../hooks/useCompany'

const STATUS_LABELS = {
  new: 'Новая',
  in_progress: 'В работе',
  waiting: 'Ожидает ответа',
  done: 'Выполнена',
  cancelled: 'Отменена',
}

const STATUSES = ['new', 'in_progress', 'waiting', 'done', 'cancelled']

export default function Leads() {
  const { companies, companyId, select, loading } = useCompany()
  const [leads, setLeads] = useState([])
  const [selected, setSelected] = useState(null)
  const [comment, setComment] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const load = () => {
    if (!companyId) return
    api(`/companies/${companyId}/leads`).then(setLeads)
  }

  useEffect(load, [companyId])

  useEffect(() => {
    setSelected(null)
    setStatusFilter('')
  }, [companyId])

  const filteredLeads = useMemo(
    () => (statusFilter ? leads.filter((l) => l.status === statusFilter) : leads),
    [leads, statusFilter],
  )

  const updateStatus = async (lead, status) => {
    await api(`/companies/${companyId}/leads/${lead.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
    load()
    if (selected?.id === lead.id) {
      const updated = await api(`/companies/${companyId}/leads/${lead.id}`)
      setSelected(updated)
    }
  }

  const addComment = async () => {
    if (!comment.trim() || !selected) return
    await api(`/companies/${companyId}/leads/${selected.id}/comments`, {
      method: 'POST',
      body: JSON.stringify({ text: comment }),
    })
    setComment('')
    const updated = await api(`/companies/${companyId}/leads/${selected.id}`)
    setSelected(updated)
    load()
  }

  if (loading) return <p className="page-empty">Загрузка…</p>

  return (
    <div>
      <h1 className="page-title">Заявки</h1>
      <CompanyPicker companies={companies} companyId={companyId} onSelect={select} />

      <div className="catalog-toolbar card" style={{ marginBottom: '1rem' }}>
        <select
          className="input-unified catalog-toolbar-input"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value)
            setSelected(null)
          }}
        >
          <option value="">Все статусы</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
          ))}
        </select>
        {statusFilter && (
          <span className="emp-meta">
            Показано: {filteredLeads.length} из {leads.length}
          </span>
        )}
      </div>

      <div className="split-layout">
        <div className="card split-panel split-panel--list">
          {filteredLeads.length === 0 ? (
            <p className="panel-empty">
              {leads.length === 0 ? 'Заявок нет' : 'Заявок с выбранным статусом нет'}
            </p>
          ) : (
            filteredLeads.map((l) => (
              <button
                key={l.id}
                type="button"
                className={`lead-row ${selected?.id === l.id ? 'lead-row--active' : ''}`}
                onClick={() => setSelected(l)}
              >
                <div className="lead-row-head">
                  <strong>{l.client_name}</strong>
                  <span className={`badge badge-${l.status}`}>{STATUS_LABELS[l.status]}</span>
                </div>
                <p className="emp-meta">{l.source} · {new Date(l.created_at).toLocaleString('ru')}</p>
              </button>
            ))
          )}
        </div>

        <div className="card split-panel split-panel--detail">
          {selected ? (
            <>
              <h3>{selected.client_name}</h3>
              <p style={{ color: 'var(--muted)', margin: '0.5rem 0' }}>{selected.client_phone} {selected.client_email}</p>
              <p style={{ marginBottom: '1rem' }}>{selected.message}</p>
              <div className="field">
                <label>Статус</label>
                <select className="input-unified" value={selected.status} onChange={(e) => updateStatus(selected, e.target.value)}>
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                  ))}
                </select>
              </div>
              <h4 style={{ margin: '1rem 0 0.5rem' }}>Комментарии</h4>
              <ul className="comment-list scroll-panel">
                {(selected.comments || []).map((c) => (
                  <li key={c.id} className="comment-item">
                    <div className="comment-meta">
                      <strong>{c.author_name}</strong>
                      {c.author_job_title && <span className="emp-meta"> · {c.author_job_title}</span>}
                      <span className="comment-date">{new Date(c.created_at).toLocaleString('ru')}</span>
                    </div>
                    <p className="comment-text">{c.text}</p>
                  </li>
                ))}
              </ul>
              <div className="field">
                <label>Новый комментарий</label>
                <textarea className="input-unified" value={comment} onChange={(e) => setComment(e.target.value)} />
              </div>
              <button className="btn" type="button" onClick={addComment}>Добавить</button>
            </>
          ) : (
            <p className="panel-empty">Выберите заявку</p>
          )}
        </div>
      </div>
    </div>
  )
}
