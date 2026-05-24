import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { api } from '../api/client'
import { useUser } from '../hooks/useUser'

function OnlineDot({ online }) {
  return <span className={`online-dot ${online ? 'online-dot--on' : ''}`} title={online ? 'В сети' : 'Не в сети'} />
}

function fmtSeen(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('ru')
}

export default function AdminPanel() {
  const { user, loading, isAdmin } = useUser()
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [companies, setCompanies] = useState([])
  const [tab, setTab] = useState('stats')

  useEffect(() => {
    if (!isAdmin) return
    api('/admin/stats').then(setStats)
    api('/admin/users').then(setUsers)
    api('/admin/companies').then(setCompanies)
  }, [isAdmin])

  if (loading) return <p>Загрузка…</p>
  if (!isAdmin) return <Navigate to="/app" replace />

  const toggleUser = async (u, field) => {
    await api(`/admin/users/${u.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ [field]: !u[field] }),
    })
    setUsers((list) => list.map((x) => (x.id === u.id ? { ...x, [field]: !x[field] } : x)))
  }

  const toggleCompany = async (c) => {
    await api(`/admin/companies/${c.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: !c.is_active }),
    })
    setCompanies((list) => list.map((x) => (x.id === c.id ? { ...x, is_active: !x.is_active } : x)))
  }

  return (
    <div>
      <h1 className="page-title page-title--tight">Админ-панель платформы</h1>
      <p className="text-muted page-intro">
        Супер-админ: все пользователи и компании. Вход: <strong>superadmin@dot.kz</strong> / <strong>DotSuper2026!</strong>
      </p>

      <div className="toolbar-row admin-toolbar">
        {['stats', 'users', 'companies'].map((t) => (
          <button key={t} type="button" className={tab === t ? 'btn' : 'btn btn-outline'} onClick={() => setTab(t)}>
            {t === 'stats' ? 'Статистика' : t === 'users' ? 'Пользователи' : 'Компании'}
          </button>
        ))}
        <Link to="/app" className="btn btn-outline toolbar-back">← Кабинет</Link>
      </div>

      {tab === 'stats' && stats && (
        <div className="grid-2">
          <div className="card"><p className="stat-label">Пользователей</p><p className="stat-value">{stats.users_total}</p></div>
          <div className="card"><p className="stat-label">Компаний</p><p className="stat-value">{stats.companies_total}</p></div>
          <div className="card"><p className="stat-label">Активных компаний</p><p className="stat-value">{stats.companies_active}</p></div>
          <div className="card"><p className="stat-label">Заявок всего</p><p className="stat-value">{stats.leads_total}</p></div>
        </div>
      )}

      {tab === 'users' && (
        <div className="card table-scroll">
          <table className="data-table data-table--wide">
            <thead>
              <tr><th></th><th>ID</th><th>Имя</th><th>Email</th><th>Админ</th><th>Активен</th><th>Последний вход</th><th></th></tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td><OnlineDot online={u.is_online} /></td>
                  <td>{u.id}</td>
                  <td>{u.full_name}{u.id === user?.id ? ' (вы)' : ''}</td>
                  <td className="cell-break">{u.email}</td>
                  <td>{u.is_admin ? 'Да' : 'Нет'}</td>
                  <td>{u.is_active ? 'Да' : 'Нет'}</td>
                  <td className="cell-nowrap">{fmtSeen(u.last_seen_at)}</td>
                  <td className="table-actions">
                    <button type="button" className="btn btn-outline btn-xs" onClick={() => toggleUser(u, 'is_admin')}>
                      {u.is_admin ? 'Снять админ' : 'Сделать админ'}
                    </button>
                    <button type="button" className="btn btn-outline btn-xs" onClick={() => toggleUser(u, 'is_active')}>
                      {u.is_active ? 'Блок' : 'Разблок'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'companies' && (
        <div className="card table-scroll">
          <table className="data-table data-table--wide">
            <thead>
              <tr><th>ID</th><th>Название</th><th>Slug</th><th>Владелец</th><th>Статус</th><th></th></tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <tr key={c.id}>
                  <td>{c.id}</td>
                  <td>{c.name}</td>
                  <td><Link to={`/c/${c.slug}`} target="_blank">/c/{c.slug}</Link></td>
                  <td>{c.owner_id}</td>
                  <td>{c.is_active ? 'Активна' : 'Отключена'}</td>
                  <td>
                    <button type="button" className="btn btn-outline btn-xs" onClick={() => toggleCompany(c)}>
                      {c.is_active ? 'Отключить' : 'Включить'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
