import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { BarChart, DonutChart } from '../components/SimpleChart'
import CompanyPicker from '../components/CompanyPicker'
import { useCompany } from '../hooks/useCompany'

const STATUS_LABELS = {
  new: 'Новая', in_progress: 'В работе', waiting: 'Ожидает ответа',
  done: 'Выполнена', cancelled: 'Отменена',
}

export default function Dashboard() {
  const { companies, company, companyId, select, loading } = useCompany()
  const [analytics, setAnalytics] = useState(null)
  const [overview, setOverview] = useState(null)
  const [leads, setLeads] = useState([])

  useEffect(() => {
    if (!companyId) return
    api(`/companies/${companyId}/analytics`).then(setAnalytics)
    api(`/companies/${companyId}/leads`).then((list) => setLeads(list.slice(0, 5)))
    api('/analytics/overview').then(setOverview)
  }, [companyId])

  if (loading) return <p>Загрузка…</p>
  if (!companies.length) {
    return (
      <div className="card">
        <h2>Добро пожаловать!</h2>
        <p style={{ color: 'var(--muted)', margin: '0.75rem 0 1rem' }}>Создайте первую компанию</p>
        <Link className="btn" to="/app/company">Мои компании</Link>
      </div>
    )
  }

  return (
    <div>
      <h1>Обзор</h1>
      <p style={{ color: 'var(--muted)', marginBottom: '1rem' }}>
        {company && <>Страница: <Link to={`/c/${company.slug}`} target="_blank">/c/{company.slug}</Link></>}
      </p>
      <CompanyPicker companies={companies} companyId={companyId} onSelect={select} />

      {analytics && (
        <>
          <div className="grid-2" style={{ margin: '1.25rem 0' }}>
            <div className="card"><p className="stat-label">Заявки</p><p className="stat-value">{analytics.total_leads}</p></div>
            <div className="card"><p className="stat-label">Клиенты</p><p className="stat-value">{analytics.total_customers}</p></div>
            <div className="card"><p className="stat-label">Повторные</p><p className="stat-value">{analytics.repeat_customers}</p></div>
            <div className="card"><p className="stat-label">Конверсия</p><p className="stat-value">{analytics.conversion_rate}%</p></div>
          </div>

          <h2 style={{ marginBottom: '1rem' }}>Статистика по компаниям</h2>
          <div className="grid-2">
            <div className="card">
              <h3>Динамика заявок (7 дней)</h3>
              <BarChart data={analytics.leads_timeline || []} />
            </div>
            <div className="card">
              <h3>Статусы заявок</h3>
              <DonutChart data={(analytics.status_chart || []).map((d) => ({
                label: STATUS_LABELS[d.label] || d.label,
                value: d.value,
              }))} />
            </div>
            <div className="card">
              <h3>Источники</h3>
              <DonutChart data={analytics.source_chart || []} />
            </div>
          </div>
        </>
      )}

      {overview?.companies?.length > 1 && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <h3>Сравнение компаний</h3>
          <div className="grid-2" style={{ marginTop: '1rem' }}>
            {overview.companies.map((c) => (
              <div key={c.company_id} className="card" style={{ background: 'var(--bg)' }}>
                <strong>{c.company_name}</strong>
                <p className="emp-meta">Заявок: {c.total_leads} · Клиентов: {c.total_customers}</p>
                <BarChart data={c.leads_timeline || []} color="var(--success)" />
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <h2>Последние заявки</h2>
          <Link to="/app/leads">Все →</Link>
        </div>
        {leads.map((l) => (
          <div key={l.id} style={{ padding: '0.65rem 0', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', gap: '0.5rem' }}>
            <div>
              <strong>{l.client_name}</strong>
              <p className="emp-meta">{l.message?.slice(0, 60)}</p>
            </div>
            <span className={`badge badge-${l.status}`}>{STATUS_LABELS[l.status]}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
