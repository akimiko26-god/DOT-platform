import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import FormattedText from '../components/FormattedText'
import HeroSlider from '../components/HeroSlider'

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
      <HeroSlider slides={company.slides || []} />

      <header className="container public-hero">
        <p className="public-brand">./dot</p>
        <div className="public-title-row">
          {company.logo_url && (
            <img src={company.logo_url} alt="" className="public-company-logo" />
          )}
          <div>
            <h1 className="public-title">{company.name}</h1>
            {company.work_schedule && <p className="public-schedule">🕐 {company.work_schedule}</p>}
          </div>
        </div>
        {company.description && (
          <FormattedText text={company.description} className="public-desc text-muted" tag="div" />
        )}
      </header>

      <div className="container public-content">
        {company.activities && (
          <section className="card public-section">
            <h2 className="public-section-title">Направления деятельности</h2>
            <FormattedText text={company.activities} className="public-body-text" />
          </section>
        )}

        <div className="grid-2 public-grid">
          <section className="card public-section" id="contacts">
            <h2 className="public-section-title">Контакты</h2>
            <ul className="public-contact-list">
              {company.phone && <li>📞 <a href={`tel:${company.phone}`}>{company.phone}</a></li>}
              {company.email && <li>✉️ <a href={`mailto:${company.email}`}>{company.email}</a></li>}
              {company.address && <li>📍 <FormattedText text={company.address} tag="span" /></li>}
            </ul>
          </section>

          <section className="card public-section">
            <h2 className="public-section-title">Связаться</h2>
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
          </section>
        </div>
      </div>
    </div>
  )
}
