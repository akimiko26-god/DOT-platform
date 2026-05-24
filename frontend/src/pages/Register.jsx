import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, login } from '../api/client'

export default function Register() {
  const nav = useNavigate()
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    company_name: '',
    slug: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (key) => (e) => {
    const v = e.target.value
    setForm((f) => {
      const next = { ...f, [key]: v }
      if (key === 'company_name' && !f.slug) {
        next.slug = v
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '')
          .slice(0, 40)
      }
      return next
    })
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          email: form.email,
          password: form.password,
          full_name: form.full_name,
        }),
      })
      await login(form.email, form.password)
      const company = await api('/companies', {
        method: 'POST',
        body: JSON.stringify({
          name: form.company_name,
          slug: form.slug,
        }),
      })
      localStorage.setItem('dot_company_id', String(company.id))
      nav('/app')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container page-narrow page-auth">
      <h1 style={{ marginBottom: '0.5rem' }}>Регистрация</h1>
      <p style={{ color: 'var(--muted)', marginBottom: '1.5rem' }}>
        Создайте аккаунт и первую компанию за минуту
      </p>
      <form className="card" onSubmit={submit}>
        <div className="field">
          <label>Ваше имя</label>
          <input value={form.full_name} onChange={set('full_name')} required />
        </div>
        <div className="field">
          <label>Email</label>
          <input type="email" value={form.email} onChange={set('email')} required />
        </div>
        <div className="field">
          <label>Пароль (мин. 6 символов)</label>
          <input type="password" value={form.password} onChange={set('password')} minLength={6} required />
        </div>
        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '1.25rem 0' }} />
        <div className="field">
          <label>Название компании</label>
          <input value={form.company_name} onChange={set('company_name')} required />
        </div>
        <div className="field">
          <label>Адрес страницы (латиница)</label>
          <input
            value={form.slug}
            onChange={set('slug')}
            pattern="^[a-z0-9-]+$"
            placeholder="my-cafe"
            required
          />
        </div>
        {error && <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{error}</p>}
        <button className="btn" type="submit" disabled={loading} style={{ width: '100%' }}>
          {loading ? 'Создание…' : 'Создать аккаунт'}
        </button>
      </form>
      <p style={{ marginTop: '1rem', color: 'var(--muted)' }}>
        Уже есть аккаунт? <Link to="/login">Войти</Link>
      </p>
    </div>
  )
}
