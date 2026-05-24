import { useEffect, useState } from 'react'
import { api, uploadAvatar } from '../api/client'
import { useUser } from '../hooks/useUser'

export default function Profile() {
  const { user, reload, isAdmin } = useUser()
  const [form, setForm] = useState({
    full_name: '', email: '', phone: '', job_title: '', department: '', avatar_url: '',
  })
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (user) {
      setForm({
        full_name: user.full_name,
        email: user.email,
        phone: user.phone || '',
        job_title: user.job_title || '',
        department: user.department || '',
        avatar_url: user.avatar_url || '',
      })
    }
  }, [user])

  const save = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api('/auth/me', { method: 'PATCH', body: JSON.stringify(form) })
      await reload()
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError(err.message)
    }
  }

  const onAvatar = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const { url } = await uploadAvatar(file)
      setForm((f) => ({ ...f, avatar_url: url }))
      await api('/auth/me', { method: 'PATCH', body: JSON.stringify({ avatar_url: url }) })
      await reload()
    } catch (err) {
      setError(err.message)
    }
  }

  if (!user) return <p>Загрузка…</p>

  return (
    <div className="page-narrow">
      <h1>Мой профиль</h1>
      <p style={{ color: 'var(--muted)', marginBottom: '1.25rem' }}>
        {isAdmin ? 'Администратор платформы' : 'Данные для входа и отображения в комментариях к заявкам'}
      </p>
      <form className="card" onSubmit={save}>
        <div className="profile-avatar-edit">
          {form.avatar_url ? (
            <img src={form.avatar_url} alt="" className="profile-avatar-large" />
          ) : (
            <span className="profile-avatar-large profile-avatar-placeholder">{(form.full_name || 'U').charAt(0)}</span>
          )}
          <label className="btn btn-outline">
            Загрузить фото
            <input type="file" accept="image/*" hidden onChange={onAvatar} />
          </label>
        </div>
        <div className="grid-2">
          <div className="field"><label>ФИО</label><input className="input-unified" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required /></div>
          <div className="field"><label>Должность</label><input className="input-unified" value={form.job_title} onChange={(e) => setForm({ ...form, job_title: e.target.value })} placeholder="Менеджер" /></div>
          <div className="field"><label>Email</label><input className="input-unified" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></div>
          <div className="field"><label>Отдел</label><input className="input-unified" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} /></div>
          <div className="field"><label>Телефон</label><input className="input-unified" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
        </div>
        {error && <p style={{ color: 'var(--danger)' }}>{error}</p>}
        <button className="btn" type="submit">{saved ? 'Сохранено ✓' : 'Сохранить'}</button>
      </form>

      <div className="card" style={{ marginTop: '1rem' }}>
        <h3>Доступ к компаниям</h3>
        <ul style={{ listStyle: 'none', marginTop: '0.75rem' }}>
          {user.companies_access?.map((c) => (
            <li key={c.company_id} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
              <strong>{c.company_name}</strong>
              <span style={{ color: 'var(--muted)', marginLeft: 8 }}>{c.permissions?.role || 'участник'}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
