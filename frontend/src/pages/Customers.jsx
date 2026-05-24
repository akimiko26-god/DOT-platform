import { useEffect, useState } from 'react'

import { api } from '../api/client'

import Modal from '../components/Modal'

import PageShell from '../components/PageShell'

import { useCompany } from '../hooks/useCompany'

import { useUser } from '../hooks/useUser'



const STATUS_RU = { new: 'Новая', in_progress: 'В работе', waiting: 'Ожидает', done: 'Готово', cancelled: 'Отменена' }



export default function Customers() {

  const { companies, company, companyId, select, loading, error } = useCompany()

  const { permsFor } = useUser()

  const perms = permsFor(companyId)

  const [customers, setCustomers] = useState([])

  const [search, setSearch] = useState('')

  const [selected, setSelected] = useState(null)

  const [detail, setDetail] = useState(null)

  const [editForm, setEditForm] = useState(null)

  const [loadingDetail, setLoadingDetail] = useState(false)



  const load = () => {

    if (!companyId) return

    const qs = search ? `?q=${encodeURIComponent(search)}` : ''

    api(`/companies/${companyId}/customers${qs}`).then(setCustomers).catch(() => setCustomers([]))

  }



  useEffect(load, [companyId, search])



  const openCard = async (c) => {

    setSelected(c)

    setLoadingDetail(true)

    try {

      const d = await api(`/companies/${companyId}/customers/${c.id}`)

      setDetail(d)

      setEditForm({

        name: d.name,

        phone: d.phone,

        email: d.email,

        notes: d.notes,

        is_vip: !!d.is_vip,

      })

    } finally {

      setLoadingDetail(false)

    }

  }



  const saveEdit = async () => {

    await api(`/companies/${companyId}/customers/${selected.id}`, {

      method: 'PATCH',

      body: JSON.stringify(editForm),

    })

    load()

    openCard({ ...selected, ...editForm })

  }



  const refreshAi = async () => {

    const data = await api(`/companies/${companyId}/customers/${selected.id}/refresh-insight`, { method: 'POST' })

    setDetail((d) => ({ ...d, ai_insight: data.insight, insight_meta: data }))

  }



  const noModule = company && (!company.module_crm || perms.crm === false)



  return (

    <PageShell

      title="CRM — клиенты"

      loading={loading}

      error={error}

      companies={companies}

      companyId={companyId}

      onSelect={select}

      moduleDisabled={noModule}

      moduleName="CRM"

    >

      <div className="catalog-toolbar card" style={{ marginBottom: '1rem' }}>

        <input

          className="input-unified catalog-toolbar-input"

          placeholder="Поиск клиента…"

          value={search}

          onChange={(e) => setSearch(e.target.value)}

        />

      </div>



      <div className="grid-2">

        {customers.map((c) => (

          <div

            key={c.id}

            className={`card employee-card clickable ${c.is_vip ? 'customer-vip' : ''}`}

            onClick={() => openCard(c)}

            role="button"

            tabIndex={0}

            onKeyDown={(e) => e.key === 'Enter' && openCard(c)}

          >

            <div className="customer-card-head">

              <h3>{c.name}</h3>

              {c.is_vip && <span className="vip-badge" title="VIP-клиент">VIP</span>}

            </div>

            <p className="emp-meta">{c.phone || '—'} · {c.email || '—'}</p>

            <p style={{ fontSize: '0.85rem', color: 'var(--accent)' }}>Обращений: {c.visit_count}</p>

            {c.ai_insight && <p className="ai-hint-preview">🤖 {c.ai_insight.slice(0, 80)}…</p>}

          </div>

        ))}

      </div>



      <Modal open={!!selected} onClose={() => { setSelected(null); setDetail(null) }} title={selected?.name || 'Клиент'} wide>

        {loadingDetail ? <p>Загрузка…</p> : detail && editForm && (

          <>

            <label className="vip-toggle">

              <input

                type="checkbox"

                checked={editForm.is_vip}

                onChange={(e) => setEditForm({ ...editForm, is_vip: e.target.checked })}

              />

              <span className="vip-badge">VIP</span>

              <span>Особый клиент (значок VIP в списке)</span>

            </label>

            <div className="grid-2" style={{ marginTop: '1rem' }}>

              <div className="field">

                <label>Имя</label>

                <input className="input-unified" value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />

              </div>

              <div className="field">

                <label>Телефон</label>

                <input className="input-unified" value={editForm.phone} onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })} />

              </div>

              <div className="field">

                <label>Email</label>

                <input className="input-unified" value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} />

              </div>

            </div>

            <div className="field">

              <label>Заметки</label>

              <textarea className="input-unified" value={editForm.notes} onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })} />

            </div>

            <button type="button" className="btn" onClick={saveEdit} style={{ marginBottom: '1rem' }}>Сохранить изменения</button>



            <div className="ai-insight-box">

              <div className="flex-between">

                <h4>Индивидуальная AI-подсказка</h4>

                <button type="button" className="btn btn-outline" onClick={refreshAi}>Обновить с ИИ</button>

              </div>

              <p className="emp-meta" style={{ marginTop: '0.35rem' }}>Анализ по заявкам и заметкам клиента. Обновляйте после новых обращений.</p>

              <pre className="ai-insight-text">{detail.ai_insight || 'Нажмите «Обновить с ИИ» для генерации.'}</pre>

              {detail.insight_meta?.pains?.length > 0 && (

                <p><strong>Боли:</strong> {detail.insight_meta.pains.join(', ')}</p>

              )}

            </div>



            <h4 style={{ marginTop: '1.25rem' }}>История обращений</h4>

            {detail.leads?.length ? detail.leads.map((l) => (

              <div key={l.id} className="history-item">

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>

                  <span className={`badge badge-${l.status}`}>{STATUS_RU[l.status] || l.status}</span>

                  <span className="emp-meta">{new Date(l.created_at).toLocaleString('ru')}</span>

                </div>

                <p style={{ marginTop: '0.35rem' }}>{l.message}</p>

                <p className="emp-meta">Источник: {l.source}</p>

              </div>

            )) : <p style={{ color: 'var(--muted)' }}>Обращений пока нет</p>}

          </>

        )}

      </Modal>

    </PageShell>

  )

}


