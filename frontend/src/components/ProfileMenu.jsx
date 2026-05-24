import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { logout } from '../api/client'
import { useUser } from '../hooks/useUser'
import { useCompany } from '../hooks/useCompany'

const CLOSE_DELAY_MS = 280

export default function ProfileMenu() {
  const { user, isAdmin, permsFor, loading: userLoading } = useUser()
  const { company, companyId, select, companies } = useCompany()
  const [open, setOpen] = useState(false)
  const closeTimer = useRef(null)
  const nav = useNavigate()
  const perms = permsFor(companyId)
  const canEmployees = isAdmin || perms.role === 'owner' || perms.employees === true
  const canSettings = isAdmin || perms.role === 'owner' || perms.settings === true

  const activeCompany = company || companies[0]

  const show = () => {
    if (closeTimer.current) {
      clearTimeout(closeTimer.current)
      closeTimer.current = null
    }
    setOpen(true)
  }

  const hide = () => {
    closeTimer.current = setTimeout(() => setOpen(false), CLOSE_DELAY_MS)
  }

  const toggle = () => setOpen((v) => !v)

  return (
    <div
      className="profile-menu"
      onMouseEnter={show}
      onMouseLeave={hide}
    >
      <button
        type="button"
        className="profile-trigger"
        aria-label="Профиль"
        aria-expanded={open}
        onClick={toggle}
      >
        <span className="profile-avatar">
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt="" className="profile-avatar-img" />
          ) : (
            (user?.full_name || 'U').charAt(0).toUpperCase()
          )}
        </span>
      </button>

      {open && !userLoading && user && (
        <div className="profile-dropdown" onMouseEnter={show} onMouseLeave={hide}>
          <div className="profile-dropdown-head">
            <strong>{user.full_name}</strong>
            <span>{user.email}</span>
            {user.phone && <span>{user.phone}</span>}
            {isAdmin && <span className="profile-badge">Админ платформы</span>}
          </div>

          {activeCompany && (
            <div className="profile-company-block">
              <span className="profile-label">Текущая компания</span>
              <strong>{activeCompany.name}</strong>
              <span className="profile-slug">/c/{activeCompany.slug}</span>
            </div>
          )}

          <nav className="profile-links">
            <Link to="/app/profile" onClick={() => setOpen(false)}>Мой профиль</Link>
            <Link to="/app/company" onClick={() => setOpen(false)}>Мои компании</Link>
            {canSettings && (
              <Link to="/app/settings" onClick={() => setOpen(false)}>Настройки компании</Link>
            )}
            {canEmployees && (
              <Link to="/app/employees" onClick={() => setOpen(false)}>Сотрудники</Link>
            )}
          </nav>

          {!isAdmin && companies.length > 1 && (
            <div className="profile-switch">
              <span className="profile-label">Сменить компанию</span>
              {companies.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className={c.id === companyId ? 'active' : ''}
                  onClick={() => {
                    select(c.id, { reload: true })
                    setOpen(false)
                  }}
                >
                  {c.name}
                </button>
              ))}
            </div>
          )}

          <button
            type="button"
            className="profile-logout"
            onClick={() => {
              logout()
              nav('/login')
            }}
          >
            Выйти
          </button>
        </div>
      )}
    </div>
  )
}
