import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'

export default function PublicCompany() {
  const { slug } = useParams()
  const [company, setCompany] = useState(null)
  const [messenger, setMessenger] = useState(null)

  useEffect(() => {
    api(`/public/companies/${slug}`).then(setCompany)
    api(`/public/companies/${slug}/messenger?message=${encodeURIComponent('Здравствуйте! Интересует ваша услуга.')}`).then(setMessenger)
  }, [slug])

  if (!company) return <div className="container page-loading">Загрузка…</div>

  return (
    <div className="public-page">
      <header className="container public-hero">
        <p className="public-brand">./dot</p>
        <h1 className="public-title">{company.name}</h1>
        {company.description && <p className="text-muted public-desc">{company.description}</p>}
      </header>

      <div className="container grid-2 public-grid">
        <div className="card" id="contacts">
          <h3>Контакты</h3>
          {company.phone && <p>📞 {company.phone}</p>}
          {company.email && <p>✉️ {company.email}</p>}
          {company.address && <p>📍 {company.address}</p>}
          {company.work_schedule && <p>🕐 {company.work_schedule}</p>}
          {company.activities && <p className="public-activities">{company.activities}</p>}
        </div>

        <div className="card">
          <h3>Связаться</h3>
          <div className="stack-actions">
            {company.module_catalog && (
              <Link className="btn btn-outline" to={`/c/${slug}/catalog`}>Каталог услуг</Link>
            )}
            {company.module_leads && (
              <Link className="btn" to={`/c/${slug}/contact`}>Оставить заявку</Link>
            )}
            {messenger?.whatsapp_url && (
              <a className="btn btn-outline" href={messenger.whatsapp_url} target="_blank" rel="noreferrer">WhatsApp</a>
            )}
            {messenger?.telegram_url && (
              <a className="btn btn-outline" href={messenger.telegram_url} target="_blank" rel="noreferrer">Telegram</a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
