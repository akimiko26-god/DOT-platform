import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import ProfileMenu from './ProfileMenu'
import { usePresence } from '../hooks/usePresence'
import { useUser } from '../hooks/useUser'

const NAV = [
  { to: '/app', label: 'Обзор', end: true, perm: null },
  { to: '/app/leads', label: 'Заявки', perm: 'leads' },
  { to: '/app/customers', label: 'CRM', perm: 'crm', alwaysShow: true },
  { to: '/app/catalog', label: 'Каталог', perm: 'catalog', alwaysShow: true },
  { to: '/app/qr', label: 'QR', perm: 'qr', alwaysShow: true },
  { to: '/app/admin', label: 'Админ', perm: 'admin', adminOnly: true },
]

export default function Layout() {
  usePresence()
  const { isAdmin, permsFor } = useUser()
  const companyId = Number(localStorage.getItem('dot_company_id'))
  const perms = permsFor(companyId)
  const [navOpen, setNavOpen] = useState(false)

  const visible = NAV.filter((item) => {
    if (item.adminOnly) return isAdmin
    if (item.alwaysShow) return true
    if (!item.perm) return true
    if (isAdmin || perms.role === 'owner') return true
    return perms[item.perm] === true
  })

  useEffect(() => {
    document.body.classList.toggle('nav-open', navOpen)
    return () => document.body.classList.remove('nav-open')
  }, [navOpen])

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 900) setNavOpen(false)
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const closeNav = () => setNavOpen(false)

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="container header-inner">
          <NavLink to="/app" className="brand-link" onClick={closeNav}>
            <strong><span className="brand-dot">./</span>dot</strong>
          </NavLink>

          <button
            type="button"
            className="nav-toggle"
            aria-expanded={navOpen}
            aria-label={navOpen ? 'Закрыть меню' : 'Открыть меню'}
            onClick={() => setNavOpen((v) => !v)}
          >
            <span className="nav-toggle-bar" />
            <span className="nav-toggle-bar" />
            <span className="nav-toggle-bar" />
          </button>

          <nav className={`main-nav ${navOpen ? 'main-nav--open' : ''}`} aria-label="Основное меню">
            {visible.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => (isActive ? 'nav-active' : '')}
                onClick={closeNav}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="header-profile">
            <ProfileMenu />
          </div>
        </div>
      </header>

      {navOpen && (
        <button type="button" className="nav-backdrop" aria-label="Закрыть меню" onClick={closeNav} />
      )}

      <main className="container app-main">
        <Outlet key={companyId ?? 'none'} />
      </main>
    </div>
  )
}
