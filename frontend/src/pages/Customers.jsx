import { useEffect, useState } from 'react'

import { api } from '../api/client'

import FormattedText from '../components/FormattedText'

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

  const [aiLoading, setAiLoading] = useState(false)

  const [aiQuestion, setAiQuestion] = useState('')

  const [aiAnswer, setAiAnswer] = useState('')

  const [aiAskLoading, setAiAskLoading] = useState(false)



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

    if (!selected || !editForm || aiLoading || aiAskLoading) return

    setAiLoading(true)

    try {

      const data = await api(`/companies/${companyId}/customers/${selected.id}/refresh-insight`, {

        method: 'POST',

        body: JSON.stringify(editForm),

      })

      setDetail((d) => ({

        ...d,

        ...editForm,

        ai_insight: data.insight,

        insight_meta: data,

      }))

      setSelected((s) => ({ ...s, ...editForm }))

      load()

    } finally {

      setAiLoading(false)

    }

  }



  const askAi = async () => {

    if (!selected || !aiQuestion.trim() || aiLoading || aiAskLoading) return

    setAiAskLoading(true)

    try {

      const data = await api(`/companies/${companyId}/customers/${selected.id}/ask-ai`, {

        method: 'POST',

        body: JSON.stringify({ question: aiQuestion.trim() }),

      })

      setAiAnswer(data.answer)

    } finally {

      setAiAskLoading(false)

    }

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



            <div className={`ai-insight-box${aiLoading || aiAskLoading ? ' is-loading' : ''}`}>

              <div className="flex-between">

                <h4>AI-бриф для менеджера</h4>

                <button type="button" className="btn btn-outline" onClick={refreshAi} disabled={aiLoading || aiAskLoading}>

                  {aiLoading ? 'Анализ…' : 'Обновить с ИИ'}

                </button>

              </div>

              {(aiLoading || aiAskLoading) && (

                <div className="ai-loading-banner" role="status" aria-live="polite">

                  <span className="ai-spinner" aria-hidden="true" />

                  <span>

                    {aiLoading

                      ? 'ИИ формирует бриф по клиенту. Подождите ответ — обычно 10–30 секунд. Не нажимайте «Обновить с ИИ» повторно.'

                      : 'ИИ готовит ответ на ваш вопрос. Подождите — не отправляйте вопрос повторно.'}

                  </span>

                </div>

              )}

              <p className="emp-meta" style={{ marginTop: '0.35rem' }}>

                Учитывает текущую карточку, заметки и всю историю обращений.

                {detail.insight_meta?.source === 'gemini'

                  ? ` Модель: ${detail.insight_meta.gemini_model || 'Gemini'}.`

                  : detail.insight_meta?.gemini_error === 'quota'

                    ? ' Лимит Gemini — локальный анализ.'

                    : ' Локальный анализ.'}

                {detail.insight_meta?.generated_at && (

                  <> Обновлено: {new Date(detail.insight_meta.generated_at).toLocaleString('ru')}.</>

                )}

              </p>

              {detail.ai_insight ? (

                <FormattedText text={detail.ai_insight} className="ai-insight-text" tag="div" />

              ) : (

                <p className="ai-insight-text text-muted">Нажмите «Обновить с ИИ» — будет составлена предыстория, портрет клиента, рекомендации и риски.</p>

              )}

              {detail.insight_meta?.risks?.length > 0 && (

                <div className="ai-meta-block">

                  <strong>Риски:</strong> {detail.insight_meta.risks.join(' · ')}

                </div>

              )}

              {detail.insight_meta?.touch_points?.length > 0 && (

                <div className="ai-meta-block">

                  <strong>Точки соприкосновения:</strong> {detail.insight_meta.touch_points.join(' · ')}

                </div>

              )}

              <div className="ai-ask-box">

                <label className="profile-label">Спросить совет у ИИ</label>

                <div className="ai-ask-row">

                  <input

                    className="input-unified"

                    placeholder="Например: как лучше ответить на последнюю жалобу?"

                    value={aiQuestion}

                    onChange={(e) => setAiQuestion(e.target.value)}

                    onKeyDown={(e) => e.key === 'Enter' && !aiAskLoading && !aiLoading && askAi()}

                    disabled={aiAskLoading || aiLoading}

                  />

                  <button type="button" className="btn btn-outline" onClick={askAi} disabled={aiAskLoading || aiLoading}>

                    {aiAskLoading ? 'Ждём…' : 'Спросить'}

                  </button>

                </div>

                {aiAnswer && <FormattedText text={aiAnswer} className="ai-ask-answer" tag="div" />}

              </div>

            </div>



            <h4 style={{ marginTop: '1.25rem' }}>История обращений</h4>

            {detail.leads?.length ? detail.leads.map((l) => (

              <div key={l.id} className="history-item">

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>

                  <span className={`badge badge-${l.status}`}>{STATUS_RU[l.status] || l.status}</span>

                  <span className="emp-meta">{new Date(l.created_at).toLocaleString('ru')}</span>

                </div>

                <p style={{ marginTop: '0.35rem' }}>{l.message}</p>

                {l.comments?.length > 0 && l.comments.map((c) => (

                  <p key={c.id} className="emp-meta" style={{ marginTop: '0.25rem' }}>

                    💬 {c.author_name}: {c.text}

                  </p>

                ))}

                <p className="emp-meta">Источник: {l.source}</p>

              </div>

            )) : <p style={{ color: 'var(--muted)' }}>Обращений пока нет</p>}

          </>

        )}

      </Modal>

    </PageShell>

  )

}


