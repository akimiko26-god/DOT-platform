import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'

export default function PublicContact() {
  const { slug } = useParams()
  const [form, setForm] = useState({ client_name: '', client_phone: '', client_email: '', message: '' })
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api(`/public/companies/${slug}/leads`, {
        method: 'POST',
        body: JSON.stringify({ ...form, source: 'form' }),
      })
      setDone(true)
    } catch (err) {
      setError(err.message)
    }
  }

  if (done) {
    return (
      <div className="container" style={{ padding: '4rem 0', textAlign: 'center' }}>
        <h2>Заявка отправлена</h2>
        <p style={{ color: 'var(--muted)', margin: '1rem 0' }}>Мы свяжемся с вами в ближайшее время</p>
        <Link to={`/c/${slug}`}>На главную</Link>
      </div>
    )
  }

  return (
    <div className="container page-narrow public-inner">
      <Link to={`/c/${slug}`} style={{ color: 'var(--muted)' }}>← Назад</Link>
      <h1 style={{ margin: '1rem 0' }}>Оставить заявку</h1>
      <form className="card" onSubmit={submit}>
        <div className="field"><label>Имя</label><input value={form.client_name} onChange={(e) => setForm({ ...form, client_name: e.target.value })} required /></div>
        <div className="field"><label>Телефон</label><input value={form.client_phone} onChange={(e) => setForm({ ...form, client_phone: e.target.value })} /></div>
        <div className="field"><label>Email</label><input type="email" value={form.client_email} onChange={(e) => setForm({ ...form, client_email: e.target.value })} /></div>
        <div className="field"><label>Сообщение</label><textarea value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} required /></div>
        {error && <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{error}</p>}
        <button className="btn" type="submit" style={{ width: '100%' }}>Отправить</button>
      </form>
    </div>
  )
}
