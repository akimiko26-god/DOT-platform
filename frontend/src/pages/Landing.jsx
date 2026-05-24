import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <div style={{ minHeight: '100vh' }}>
      <header className="container" style={{ padding: '1.5rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong style={{ fontSize: '1.35rem' }}>
          <span style={{ color: 'var(--accent)' }}>./</span>dot
        </strong>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Link className="btn btn-outline" to="/login">Войти</Link>
          <Link className="btn" to="/register">Начать бесплатно</Link>
        </div>
      </header>

      <section className="container" style={{ padding: '4rem 0 5rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--accent)', fontWeight: 600, marginBottom: '1rem' }}>
          Цифровизация МСБ в Казахстане
        </p>
        <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.2rem)', lineHeight: 1.15, marginBottom: '1.25rem' }}>
          Онлайн-присутствие, заявки и CRM — в одной платформе
        </h1>
        <p style={{ color: 'var(--muted)', maxWidth: 560, margin: '0 auto 2rem', fontSize: '1.1rem' }}>
          Запустите страницу компании, примите заявки через сайт и QR, ведите клиентскую базу
          и каталог услуг без собственной IT-команды.
        </p>
        <Link className="btn" to="/register" style={{ fontSize: '1.05rem', padding: '0.85rem 1.6rem' }}>
          Создать компанию
        </Link>
      </section>

      <section className="container grid-2" style={{ paddingBottom: '4rem' }}>
        {[
          ['Заявки', 'Формы, QR, мессенджеры — все обращения в одном месте'],
          ['CRM', 'База клиентов, история и повторные обращения'],
          ['Каталог', 'Товары и услуги с ценами на мобильных'],
          ['QR-инструменты', 'Ссылки на сайт, каталог и форму заявки'],
        ].map(([title, desc]) => (
          <div key={title} className="card">
            <h3 style={{ marginBottom: '0.5rem' }}>{title}</h3>
            <p style={{ color: 'var(--muted)' }}>{desc}</p>
          </div>
        ))}
      </section>
    </div>
  )
}
