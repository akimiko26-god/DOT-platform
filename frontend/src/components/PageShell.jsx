import { Link } from 'react-router-dom'
import CompanyPicker from './CompanyPicker'

export default function PageShell({
  title,
  loading,
  error,
  companies,
  companyId,
  onSelect,
  moduleDisabled,
  moduleName,
  children,
}) {
  if (loading) return <p>Загрузка…</p>

  if (error) {
    return (
      <div className="card">
        <h2>{title}</h2>
        <p style={{ color: 'var(--danger)', margin: '1rem 0' }}>{error}</p>
        <p style={{ color: 'var(--muted)' }}>
          Проверьте, что backend запущен на порту 8000, и обновите страницу.
        </p>
      </div>
    )
  }

  if (!companies.length) {
    return (
      <div className="card">
        <h2>{title}</h2>
        <p style={{ color: 'var(--muted)', margin: '1rem 0' }}>
          Сначала создайте компанию в разделе «Компания».
        </p>
        <Link className="btn" to="/app/settings">Настроить компанию</Link>
      </div>
    )
  }

  if (!companyId) {
    return (
      <div className="card">
        <h2>{title}</h2>
        <p style={{ color: 'var(--muted)' }}>Выберите компанию ниже</p>
        <CompanyPicker companies={companies} companyId={companyId} onSelect={onSelect} />
      </div>
    )
  }

  if (moduleDisabled) {
    return (
      <div>
        <h1 className="page-title">{title}</h1>
        <CompanyPicker companies={companies} companyId={companyId} onSelect={onSelect} />
        <div className="card">
          <p style={{ color: 'var(--muted)' }}>
            Модуль «{moduleName}» отключён в настройках компании или у вас нет прав доступа.
          </p>
          <Link to="/app/settings" style={{ marginTop: '1rem', display: 'inline-block' }}>
            Настройки компании →
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div>
      {title && <h1 className="page-title">{title}</h1>}
      <CompanyPicker companies={companies} companyId={companyId} onSelect={onSelect} />
      {children}
    </div>
  )
}
