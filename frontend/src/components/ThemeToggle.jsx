import { useEffect, useState } from 'react'

export default function ThemeToggle() {
  const [theme, setTheme] = useState(() => localStorage.getItem('dot_theme') || 'dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('dot_theme', theme)
  }, [theme])

  const toggle = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))

  return (
    <button type="button" className="theme-toggle" onClick={toggle} title="Сменить тему">
      {theme === 'dark' ? '☀️' : '🌙'}
    </button>
  )
}
