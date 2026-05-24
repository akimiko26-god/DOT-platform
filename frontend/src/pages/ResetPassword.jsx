import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'

export default function ResetPassword() {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [password, setPassword] = useState('')
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({ token, new_password: password }),
      })
      setDone(true)
    } catch (err) {
      setError(err.message)
    }
  }

  if (!token) {
    return (
      <div className="container" style={{ padding: '3rem 0' }}>
        <p style={{ color: 'var(--danger)' }}>Ссылка недействительна. Запросите сброс пароля снова.</p>
        <Link to="/forgot-password">Забыли пароль?</Link>
      </div>
    )
  }

  if (done) {
    return (
      <div className="container page-narrow page-auth page-auth--center">
        <h2>Пароль обновлён</h2>
        <Link className="btn" to="/login" style={{ marginTop: '1.5rem', display: 'inline-flex' }}>Войти</Link>
      </div>
    )
  }

  return (
    <div className="container page-narrow page-auth">
      <h1>Новый пароль</h1>
      <form className="card" onSubmit={submit} style={{ marginTop: '1rem' }}>
        <div className="field">
          <label>Пароль (мин. 6 символов)</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
        </div>
        {error && <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{error}</p>}
        <button className="btn" type="submit" style={{ width: '100%' }}>Сохранить</button>
      </form>
    </div>
  )
}
