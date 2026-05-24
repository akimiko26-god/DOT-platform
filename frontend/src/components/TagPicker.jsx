import { useMemo, useState } from 'react'

export default function TagPicker({ tags, selected, onChange }) {
  const [q, setQ] = useState('')
  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase()
    if (!s) return tags
    return tags.filter((t) => t.name.toLowerCase().includes(s))
  }, [tags, q])

  const toggle = (name) => {
    if (selected.includes(name)) onChange(selected.filter((x) => x !== name))
    else onChange([...selected, name])
  }

  return (
    <div className="tag-picker-box">
      <input
        className="input-unified"
        placeholder="Поиск тега…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <div className="tag-picker-scroll scroll-panel">
        {filtered.length === 0 ? (
          <p className="emp-meta" style={{ padding: '0.5rem' }}>Нет тегов. Добавьте в справочнике.</p>
        ) : (
          filtered.map((t) => (
            <label key={t.id} className="tag-pick-item">
              <input type="checkbox" checked={selected.includes(t.name)} onChange={() => toggle(t.name)} />
              {t.name}
            </label>
          ))
        )}
      </div>
      {selected.length > 0 && (
        <div className="perm-tags" style={{ marginTop: '0.5rem' }}>
          {selected.map((name) => (
            <span key={name} className="perm-tag">{name}</span>
          ))}
        </div>
      )}
    </div>
  )
}
