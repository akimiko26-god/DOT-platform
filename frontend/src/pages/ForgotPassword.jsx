import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [msg, setMsg] = useState('')
  const [devLink, setDevLink] = useState('')
  const [emailSent, setEmailSent] = useState(false)
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMsg('')
    setDevLink('')
    setEmailSent(false)
    try {
      const res = await api('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email: email.trim() }),
      })
      setMsg(res.message || 'Готово')
      setEmailSent(!!res.email_sent)
      if (res.dev_reset_link) setDevLink(res.dev_reset_link)
      if (res.smtp_error) {
        setMsg(`${res.message} (${res.smtp_error})`)
      }
    } catch (err) {
      setMsg(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container page-narrow page-auth">
      <h1>Сброс пароля</h1>
      <p style={{ color: 'var(--muted)', margin: '0.5rem 0 1.5rem' }}>
        Укажите email, с которым вы регистрировались — пришлём ссылку для нового пароля
      </p>
      <form className="card" onSubmit={submit}>
        <div className="field">
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
        </div>
        <button className="btn" type="submit" disabled={loading} style={{ width: '100%' }}>
          {loading ? 'Отправка…' : 'Отправить письмо'}
        </button>
      </form>

      {msg && (
        <p style={{ marginTop: '1rem', color: emailSent ? 'var(--success)' : 'var(--text)' }}>
          {emailSent ? '✓ ' : ''}{msg}
        </p>
      )}

      {devLink && (
        <div className="card" style={{ marginTop: '1rem', borderColor: 'var(--accent)' }}>
          <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>
            {emailSent
              ? 'Письмо также можно открыть по прямой ссылке:'
              : 'Почта не настроена на сервере — нажмите кнопку для сброса пароля:'}
          </p>
          <a className="btn" href={devLink} style={{ width: '100%', textAlign: 'center' }}>
            Задать новый пароль
          </a>
          <p style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '0.75rem', wordBreak: 'break-all' }}>
            {devLink}
          </p>
        </div>
      )}

      <p style={{ marginTop: '1.25rem', fontSize: '0.85rem', color: 'var(--muted)' }}>
        Для отправки на реальную почту администратору нужно указать SMTP в файле{' '}
        <code>backend/.env</code> (см. README).
      </p>
      <p style={{ marginTop: '1rem' }}>
        <Link to="/login">← Назад к входу</Link>
      </p>
    </div>
  )
}
