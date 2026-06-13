import { useCallback, useEffect, useState } from 'react'
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

const EMPTY_USER = { email: '', password: '', full_name: '', is_admin: false, is_active: true }

export default function AdminPanel() {
  const { user, loading, isAdmin } = useUser()
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [companies, setCompanies] = useState([])
  const [logs, setLogs] = useState([])
  const [tab, setTab] = useState('stats')
  const [filters, setFilters] = useState({ is_admin: '', is_active: '', company_id: '' })
  const [userForm, setUserForm] = useState(null)
  const [editUser, setEditUser] = useState(null)
  const [resetPwd, setResetPwd] = useState('')

  const loadUsers = useCallback(() => {
    const qs = new URLSearchParams()
    if (filters.is_admin) qs.set('is_admin', filters.is_admin)
    if (filters.is_active) qs.set('is_active', filters.is_active)
    if (filters.company_id) qs.set('company_id', filters.company_id)
    const q = qs.toString()
    api(`/admin/users${q ? `?${q}` : ''}`).then(setUsers)
  }, [filters])

  const loadLogs = useCallback(() => {
    api('/admin/audit-logs?limit=150').then(setLogs).catch(() => setLogs([]))
  }, [])

  useEffect(() => {
    if (!isAdmin) return
    api('/admin/stats').then(setStats)
    api('/admin/companies').then(setCompanies)
    loadUsers()
    loadLogs()
  }, [isAdmin, loadUsers, loadLogs])

  if (loading) return <p className="page-empty">Загрузка…</p>
  if (!isAdmin) return <Navigate to="/app" replace />

  const toggleUser = async (u, field) => {
    await api(`/admin/users/${u.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ [field]: !u[field] }),
    })
    loadUsers()
    loadLogs()
  }

  const toggleCompany = async (c) => {
    await api(`/admin/companies/${c.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: !c.is_active }),
    })
    setCompanies((list) => list.map((x) => (x.id === c.id ? { ...x, is_active: !x.is_active } : x)))
    loadLogs()
  }

  const createUser = async (e) => {
    e.preventDefault()
    await api('/admin/users', { method: 'POST', body: JSON.stringify(userForm) })
    setUserForm(null)
    loadUsers()
    loadLogs()
  }

  const saveUser = async (e) => {
    e.preventDefault()
    await api(`/admin/users/${editUser.id}`, {
      method: 'PATCH',
      body: JSON.stringify({
        full_name: editUser.full_name,
        email: editUser.email,
        is_admin: editUser.is_admin,
        is_active: editUser.is_active,
      }),
    })
    if (resetPwd.trim()) {
      await api(`/admin/users/${editUser.id}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({ password: resetPwd }),
      })
    }
    setEditUser(null)
    setResetPwd('')
    loadUsers()
    loadLogs()
  }

  return (
    <div>
      <h1 className="page-title page-title--tight">Админ-панель платформы</h1>
      <p className="text-muted page-intro">Управление пользователями, компаниями и журналом действий.</p>

      <div className="toolbar-row admin-toolbar">
        {[
          ['stats', 'Статистика'],
          ['users', 'Пользователи'],
          ['companies', 'Компании'],
          ['logs', 'Журнал'],
        ].map(([t, label]) => (
          <button key={t} type="button" className={tab === t ? 'btn' : 'btn btn-outline'} onClick={() => setTab(t)}>
            {label}
          </button>
        ))}
        <Link to="/app" className="btn btn-outline toolbar-back">← Кабинет</Link>
      </div>

      {tab === 'stats' && stats && (
        <div className="grid-2">
          <div className="card card-padded"><p className="stat-label">Пользователей</p><p className="stat-value">{stats.users_total}</p></div>
          <div className="card card-padded"><p className="stat-label">Компаний</p><p className="stat-value">{stats.companies_total}</p></div>
          <div className="card card-padded"><p className="stat-label">Активных компаний</p><p className="stat-value">{stats.companies_active}</p></div>
          <div className="card card-padded"><p className="stat-label">Заявок всего</p><p className="stat-value">{stats.leads_total}</p></div>
        </div>
      )}

      {tab === 'users' && (
        <>
          <div className="card card-padded filter-bar">
            <div className="grid-2">
              <div className="field">
                <label>Права админа</label>
                <select className="input-unified" value={filters.is_admin} onChange={(e) => setFilters({ ...filters, is_admin: e.target.value })}>
                  <option value="">Все</option>
                  <option value="true">Только админы</option>
                  <option value="false">Не админы</option>
                </select>
              </div>
              <div className="field">
                <label>Активность</label>
                <select className="input-unified" value={filters.is_active} onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}>
                  <option value="">Все</option>
                  <option value="true">Активные</option>
                  <option value="false">Заблокированные</option>
                </select>
              </div>
              <div className="field field-span-2">
                <label>Компания</label>
                <select className="input-unified" value={filters.company_id} onChange={(e) => setFilters({ ...filters, company_id: e.target.value })}>
                  <option value="">Все компании</option>
                  {companies.map((c) => <option key={c.id} value={c.id}>{c.name} (#{c.id})</option>)}
                </select>
              </div>
            </div>
            <button type="button" className="btn btn-outline" onClick={loadUsers}>Применить фильтр</button>
            <button type="button" className="btn" style={{ marginLeft: '0.5rem' }} onClick={() => setUserForm({ ...EMPTY_USER })}>+ Создать пользователя</button>
          </div>

          {userForm && (
            <form className="card card-padded" onSubmit={createUser} style={{ marginTop: '1rem' }}>
              <h3>Создание пользователя</h3>
              <div className="grid-2">
                <div className="field"><label>Имя</label><input className="input-unified" required value={userForm.full_name} onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })} /></div>
                <div className="field"><label>Email</label><input className="input-unified" type="email" required value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} /></div>
                <div className="field"><label>Пароль</label><input className="input-unified" type="password" required minLength={6} value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} /></div>
              </div>
              <label className="module-toggle"><input type="checkbox" checked={userForm.is_admin} onChange={(e) => setUserForm({ ...userForm, is_admin: e.target.checked })} /> Админ платформы</label>
              <div className="form-actions-row">
                <button type="submit" className="btn">Создать</button>
                <button type="button" className="btn btn-outline" onClick={() => setUserForm(null)}>Отмена</button>
              </div>
            </form>
          )}

          {editUser && (
            <form className="card card-padded" onSubmit={saveUser} style={{ marginTop: '1rem' }}>
              <h3>Редактирование #{editUser.id}</h3>
              <div className="grid-2">
                <div className="field"><label>Имя</label><input className="input-unified" value={editUser.full_name} onChange={(e) => setEditUser({ ...editUser, full_name: e.target.value })} /></div>
                <div className="field"><label>Email</label><input className="input-unified" value={editUser.email} onChange={(e) => setEditUser({ ...editUser, email: e.target.value })} /></div>
                <div className="field field-span-2"><label>Новый пароль (необязательно)</label><input className="input-unified" type="password" value={resetPwd} onChange={(e) => setResetPwd(e.target.value)} placeholder="Оставьте пустым, если не менять" /></div>
              </div>
              <label className="module-toggle"><input type="checkbox" checked={editUser.is_admin} onChange={(e) => setEditUser({ ...editUser, is_admin: e.target.checked })} /> Админ</label>
              <label className="module-toggle"><input type="checkbox" checked={editUser.is_active} onChange={(e) => setEditUser({ ...editUser, is_active: e.target.checked })} /> Активен</label>
              <div className="form-actions-row">
                <button type="submit" className="btn">Сохранить</button>
                <button type="button" className="btn btn-outline" onClick={() => { setEditUser(null); setResetPwd('') }}>Отмена</button>
              </div>
            </form>
          )}

          <div className="card table-scroll card-padded" style={{ marginTop: '1rem' }}>
            <table className="data-table data-table--wide">
              <thead>
                <tr><th></th><th>ID</th><th>Имя</th><th>Email</th><th>Компании</th><th>Админ</th><th>Активен</th><th>Последний вход</th><th></th></tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td><OnlineDot online={u.is_online} /></td>
                    <td>{u.id}</td>
                    <td>{u.full_name}{u.id === user?.id ? ' (вы)' : ''}</td>
                    <td className="cell-break">{u.email}</td>
                    <td className="cell-break">{u.company_names?.join(', ') || '—'}</td>
                    <td>{u.is_admin ? 'Да' : 'Нет'}</td>
                    <td>{u.is_active ? 'Да' : 'Нет'}</td>
                    <td className="cell-nowrap">{fmtSeen(u.last_seen_at)}</td>
                    <td className="table-actions">
                      <button type="button" className="btn btn-outline btn-xs" onClick={() => setEditUser({ ...u })}>Изменить</button>
                      <button type="button" className="btn btn-outline btn-xs" onClick={() => toggleUser(u, 'is_admin')}>{u.is_admin ? '−Админ' : '+Админ'}</button>
                      <button type="button" className="btn btn-outline btn-xs" onClick={() => toggleUser(u, 'is_active')}>{u.is_active ? 'Блок' : 'Разблок'}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'companies' && (
        <div className="card table-scroll card-padded">
          <table className="data-table data-table--wide">
            <thead>
              <tr><th>ID</th><th>Название</th><th>Slug</th><th>Владелец ID</th><th>Статус</th><th></th></tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <tr key={c.id}>
                  <td>{c.id}</td>
                  <td>{c.name}</td>
                  <td><Link to={`/c/${c.slug}`} target="_blank">/c/{c.slug}</Link></td>
                  <td>#{c.owner_id}</td>
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

      {tab === 'logs' && (
        <div className="card table-scroll card-padded">
          <table className="data-table data-table--wide">
            <thead>
              <tr><th>ID</th><th>Дата</th><th>Пользователь</th><th>Действие</th><th>Объект</th><th>Детали</th></tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td>{l.id}</td>
                  <td className="cell-nowrap">{fmtSeen(l.created_at)}</td>
                  <td>{l.user_name}{l.user_id ? ` (#${l.user_id})` : ''}</td>
                  <td>{l.action}</td>
                  <td>{l.entity_type}{l.entity_id ? ` #${l.entity_id}` : ''}</td>
                  <td className="cell-break">{l.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {logs.length === 0 && <p className="page-empty">Записей пока нет</p>}
        </div>
      )}
    </div>
  )
}
