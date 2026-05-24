import { useEffect, useState } from 'react'
import { api } from '../api/client'
import PageShell from '../components/PageShell'
import { useCompany } from '../hooks/useCompany'
import { useUser } from '../hooks/useUser'

const empty = {
  email: '', password: '', full_name: '', phone: '', job_title: '', department: '',
  role: 'employee', perm_leads: false, perm_crm: false, perm_catalog: false,
  perm_qr: false, perm_settings: false, perm_employees: false,
}

const PERM_LABELS = [
  ['perm_leads', 'Заявки'], ['perm_crm', 'CRM'], ['perm_catalog', 'Каталог'],
  ['perm_qr', 'QR'], ['perm_settings', 'Настройки'], ['perm_employees', 'Сотрудники'],
]

function OnlineDot({ online }) {
  return (
    <span className={`online-dot ${online ? 'online-dot--on' : ''}`} title={online ? 'В сети' : 'Не в сети'} />
  )
}

function fmtSeen(dt) {
  if (!dt) return 'Не входил'
  return new Date(dt).toLocaleString('ru')
}

export default function Employees() {
  const { companies, companyId, select, loading, error } = useCompany()
  const { isAdmin, permsFor, loading: userLoading } = useUser()
  const perms = permsFor(companyId)
  const canManage = isAdmin || perms.role === 'owner' || perms.employees === true

  const [list, setList] = useState([])
  const [form, setForm] = useState(empty)
  const [formCompanyId, setFormCompanyId] = useState('')
  const [editing, setEditing] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [loadErr, setLoadErr] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selected, setSelected] = useState([])

  const targetCompanyId = Number(formCompanyId || companyId)

  const load = () => {
    if (!companyId || !canManage) return
    setLoadErr('')
    api(`/companies/${companyId}/employees?status=${statusFilter}`)
      .then(setList)
      .catch((e) => { setLoadErr(e.message); setList([]) })
  }

  useEffect(load, [companyId, canManage, statusFilter])
  useEffect(() => { setFormCompanyId(String(companyId || '')) }, [companyId])

  const toggleSelect = (id) => {
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))
  }

  const save = async (e) => {
    e.preventDefault()
    const cid = targetCompanyId
    if (!cid) return
    if (editing) {
      const body = { ...form }
      delete body.email
      if (!body.password) delete body.password
      await api(`/companies/${cid}/employees/${editing}`, { method: 'PATCH', body: JSON.stringify(body) })
    } else {
      await api(`/companies/${cid}/employees`, { method: 'POST', body: JSON.stringify(form) })
    }
    setForm(empty)
    setEditing(null)
    setShowForm(false)
    load()
  }

  const bulkDeactivate = async () => {
    if (!selected.length || !window.confirm(`Отключить ${selected.length} сотрудников?`)) return
    await api(`/companies/${companyId}/employees/bulk-deactivate`, {
      method: 'POST',
      body: JSON.stringify({ ids: selected }),
    })
    setSelected([])
    load()
  }

  const bulkRestore = async () => {
    if (!selected.length) return
    await api(`/companies/${companyId}/employees/bulk-restore`, {
      method: 'POST',
      body: JSON.stringify({ ids: selected }),
    })
    setSelected([])
    load()
  }

  if (userLoading || loading) return <p>Загрузка…</p>

  if (!canManage) {
    return (
      <PageShell title="Сотрудники" loading={false} error={error} companies={companies} companyId={companyId} onSelect={select} moduleDisabled moduleName="Сотрудники" />
    )
  }

  return (
    <PageShell title="Сотрудники компании" loading={false} error={error} companies={companies} companyId={companyId} onSelect={select}>
      <p style={{ color: 'var(--muted)', marginBottom: '1rem' }}>
        Сотрудники входят по email и паролю. Зелёная точка — пользователь в сети (был активен в последние 5 мин).
      </p>
      {loadErr && <p style={{ color: 'var(--danger)' }}>{loadErr}</p>}

      <div className="catalog-toolbar card" style={{ marginBottom: '1rem' }}>
        <select className="input-unified catalog-toolbar-input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">Все</option>
          <option value="active">Активные</option>
          <option value="blocked">Заблокированные</option>
        </select>
        {selected.length > 0 && (
          <>
            <button type="button" className="btn btn-outline" onClick={bulkDeactivate}>Отключить ({selected.length})</button>
            <button type="button" className="btn btn-outline" onClick={bulkRestore}>Восстановить ({selected.length})</button>
          </>
        )}
        <button className="btn btn-toolbar-end" type="button" onClick={() => { setShowForm(!showForm); setEditing(null); setForm(empty) }}>
          {showForm ? 'Отмена' : '+ Сотрудник'}
        </button>
      </div>

      {showForm && (
        <form className="card" onSubmit={save} style={{ marginBottom: '1.5rem' }}>
          <h3>{editing ? 'Карточка сотрудника' : 'Новый сотрудник'}</h3>
          {!editing && companies.length > 1 && (
            <div className="field">
              <label>Компания</label>
              <select className="input-unified" value={formCompanyId} onChange={(e) => setFormCompanyId(e.target.value)} required>
                {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
          )}
          <div className="grid-2">
            {!editing && (
              <div className="field">
                <label>Email (логин)</label>
                <input className="input-unified" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              </div>
            )}
            <div className="field">
              <label>{editing ? 'Новый пароль' : 'Пароль'}</label>
              <input className="input-unified" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required={!editing} />
            </div>
            <div className="field"><label>ФИО</label><input className="input-unified" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required /></div>
            <div className="field"><label>Телефон</label><input className="input-unified" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
            <div className="field"><label>Должность</label><input className="input-unified" value={form.job_title} onChange={(e) => setForm({ ...form, job_title: e.target.value })} /></div>
            <div className="field"><label>Отдел</label><input className="input-unified" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} /></div>
          </div>
          <h4 style={{ margin: '1rem 0 0.5rem' }}>Права</h4>
          <div className="perm-grid">
            {PERM_LABELS.map(([key, label]) => (
              <label key={key} className="perm-chip">
                <input type="checkbox" checked={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.checked })} />
                {label}
              </label>
            ))}
          </div>
          <button className="btn" type="submit" style={{ marginTop: '1rem' }}>Сохранить</button>
        </form>
      )}

      <div className="grid-2">
        {list.map((emp) => (
          <div key={emp.id} className={`card employee-card ${!emp.is_active ? 'inactive' : ''}`}>
            <div className="employee-card-top">
              <label className="bulk-check">
                <input type="checkbox" checked={selected.includes(emp.id)} onChange={() => toggleSelect(emp.id)} />
              </label>
              <OnlineDot online={emp.is_online} />
              <h3 style={{ flex: 1, margin: 0 }}>{emp.full_name}</h3>
            </div>
            <p className="emp-meta">{emp.job_title} · {emp.department}</p>
            <p className="emp-meta">{emp.email}</p>
            <p className="emp-meta">Последний вход: {fmtSeen(emp.last_seen_at)}</p>
            <div className="perm-tags">
              {PERM_LABELS.filter(([k]) => emp[k]).map(([, l]) => <span key={l} className="perm-tag">{l}</span>)}
            </div>
            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button type="button" className="btn btn-outline" onClick={() => { setEditing(emp.id); setForm({ ...emp, password: '' }); setShowForm(true) }}>Изменить</button>
              {emp.is_active ? (
                <button type="button" className="btn btn-outline" onClick={async () => { await api(`/companies/${companyId}/employees/${emp.id}`, { method: 'DELETE' }); load() }}>Отключить</button>
              ) : (
                <button type="button" className="btn btn-outline" onClick={async () => { await api(`/companies/${companyId}/employees/${emp.id}/restore`, { method: 'POST' }); load() }}>Восстановить</button>
              )}
            </div>
          </div>
        ))}
      </div>
      {list.length === 0 && !loadErr && <p style={{ color: 'var(--muted)' }}>Сотрудников нет</p>}
    </PageShell>
  )
}
