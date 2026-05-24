import { useState } from 'react'

function confirmDelete(name) {
  return window.confirm(`Удалить «${name}»?\n\nВы уверены, что хотите удалить эту запись?`)
}

export default function CategoryRefPanel({ items, value, onChange, onAdd, onDelete, disabled }) {
  const [childInputs, setChildInputs] = useState({})
  const roots = items.filter((c) => !c.parent_id)
  const childrenOf = (pid) => items.filter((c) => c.parent_id === pid)

  const submitRoot = async () => {
    if (disabled || !value.trim()) return
    try {
      await onAdd(value.trim(), null)
      onChange('')
    } catch (e) {
      alert(e.message || 'Ошибка')
    }
  }

  const submitChild = async (parentId) => {
    const name = (childInputs[parentId] || '').trim()
    if (!name) return
    try {
      await onAdd(name, parentId)
      setChildInputs((s) => ({ ...s, [parentId]: '' }))
    } catch (e) {
      alert(e.message || 'Ошибка')
    }
  }

  return (
    <div className="card">
      <h3>Категории</h3>
      <p className="refs-hint">Примеры уже есть — добавляйте свои. Enter — сохранить. «+» — подкатегория.</p>
      {disabled && <p className="emp-meta" style={{ color: 'var(--danger)' }}>Выберите компанию</p>}
      <div className="ref-form-row">
        <input
          className="input-unified"
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); submitRoot() } }}
          placeholder="Новая категория верхнего уровня"
        />
      </div>
      <ul className="ref-list scroll-panel">
        {roots.map((root) => (
          <li key={root.id} className="ref-cat-block">
            <div className="ref-cat-row">
              <span>{root.full_name || root.name}</span>
              <div className="ref-cat-actions">
                <button type="button" className="btn btn-outline btn-sm" title="Подкатегория" onClick={() => setChildInputs((s) => ({ ...s, [root.id]: s[root.id] ?? '' }))}>+</button>
                <button type="button" className="ref-del" onClick={() => { if (confirmDelete(root.name)) onDelete(root.id) }}>×</button>
              </div>
            </div>
            {childInputs[root.id] !== undefined && (
              <div className="ref-child-input ref-form-row">
                <input
                  className="input-unified"
                  value={childInputs[root.id]}
                  onChange={(e) => setChildInputs((s) => ({ ...s, [root.id]: e.target.value }))}
                  placeholder="Подкатегория"
                  onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); submitChild(root.id) } }}
                />
                <button type="button" className="btn btn-outline btn-sm" onClick={() => submitChild(root.id)}>OK</button>
              </div>
            )}
            {childrenOf(root.id).map((ch) => (
              <div key={ch.id} className="ref-cat-row ref-cat-child">
                <span>↳ {ch.name}</span>
                <button type="button" className="ref-del" onClick={() => { if (confirmDelete(ch.full_name || ch.name)) onDelete(ch.id) }}>×</button>
              </div>
            ))}
          </li>
        ))}
      </ul>
    </div>
  )
}
