import { useCallback, useEffect, useState } from 'react'
import { api, uploadImage } from '../api/client'
import CategoryRefPanel from '../components/CategoryRefPanel'
import ImageDropzone from '../components/ImageDropzone'
import TagPicker from '../components/TagPicker'
import PageShell from '../components/PageShell'
import { useCompany } from '../hooks/useCompany'
import { useUser } from '../hooks/useUser'

const empty = {
  title: '', description: '', category: '', tags: [], folder_id: null,
  price: 0, image_url: '', is_available: true, is_published: true,
}

function fmtPrice(p) {
  return Number(p ?? 0).toLocaleString('ru')
}

function buildQuery(params) {
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== '' && v != null) q.set(k, v)
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

function confirmDelete(name) {
  return window.confirm(`Удалить «${name}»?\n\nВы уверены, что хотите удалить эту запись?`)
}

function RefPanel({ title, hint, items, value, onChange, onAdd, onDelete, placeholder, disabled }) {
  const submit = async () => {
    if (disabled || !value.trim()) return
    try {
      await onAdd(value.trim())
      onChange('')
    } catch (e) {
      alert(e.message || 'Ошибка сохранения')
    }
  }
  return (
    <div className="card">
      <h3>{title}</h3>
      {hint && <p className="refs-hint">{hint}</p>}
      {disabled && <p className="emp-meta" style={{ color: 'var(--danger)' }}>Выберите компанию в кабинете</p>}
      <div className="ref-form-row">
        <input
          className="input-unified"
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); submit() } }}
          placeholder={placeholder}
        />
      </div>
      <p className="emp-meta ref-enter-hint">Введите название и нажмите Enter</p>
      <ul className="ref-list scroll-panel">
        {items.map((item) => (
          <li key={item.id}>
            <span>{item.name}</span>
            <button type="button" className="ref-del" title="Удалить" onClick={() => { if (confirmDelete(item.name)) onDelete(item.id) }}>×</button>
          </li>
        ))}
      </ul>
    </div>
  )
}

function FolderBlock({ title, count, open, onToggle, onDragOver, onDrop, children, empty }) {
  return (
    <div className="folder-drop card" onDragOver={onDragOver} onDrop={onDrop}>
      <button type="button" className="folder-header" onClick={onToggle} aria-expanded={open}>
        <span className="folder-chevron">{open ? '▼' : '▶'}</span>
        <span>📁 {title}</span>
        <span className="folder-count">({count})</span>
      </button>
      {open && (
        <div className="folder-body">
          {empty ? <p className="folder-empty">Папка пуста</p> : children}
        </div>
      )}
    </div>
  )
}

export default function CatalogManage() {
  const { companies, company, companyId, select, loading, error } = useCompany()
  const { isAdmin, permsFor } = useUser()
  const perms = permsFor(companyId)
  const [tab, setTab] = useState('items')
  const [view, setView] = useState('grid')
  const [activeFolder, setActiveFolder] = useState(null)
  const [itemStatus, setItemStatus] = useState('active')
  const [selectedIds, setSelectedIds] = useState([])
  const [bulkFolder, setBulkFolder] = useState('')
  const [items, setItems] = useState([])
  const [folders, setFolders] = useState([])
  const [categories, setCategories] = useState([])
  const [tagRefs, setTagRefs] = useState([])
  const [adminCompanies, setAdminCompanies] = useState([])
  const [adminCompanyId, setAdminCompanyId] = useState('')
  const [search, setSearch] = useState('')
  const [tagFilter, setTagFilter] = useState('')
  const [catFilter, setCatFilter] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(empty)
  const [editing, setEditing] = useState(null)
  const [dragItem, setDragItem] = useState(null)
  const [newCatName, setNewCatName] = useState('')
  const [newTagName, setNewTagName] = useState('')
  const [openFolders, setOpenFolders] = useState({})
  const [showFolderModal, setShowFolderModal] = useState(false)
  const [folderName, setFolderName] = useState('')

  const effectiveCompanyId = isAdmin && adminCompanyId ? Number(adminCompanyId) : companyId

  const loadRefs = useCallback(async () => {
    if (!effectiveCompanyId) return
    const [cats, tags] = await Promise.all([
      api(`/companies/${effectiveCompanyId}/catalog/refs/categories`),
      api(`/companies/${effectiveCompanyId}/catalog/refs/tags`),
    ])
    setCategories(cats)
    setTagRefs(tags)
  }, [effectiveCompanyId])

  const load = useCallback(() => {
    if (!effectiveCompanyId) return
    const qs = buildQuery({ q: search, tag: tagFilter, category: catFilter, status: itemStatus })
    api(`/companies/${effectiveCompanyId}/catalog/items${qs}`).then(setItems)
    api(`/companies/${effectiveCompanyId}/catalog/folders`).then((list) => {
      setFolders(list)
      setOpenFolders((prev) => {
        const next = { ...prev, none: prev.none ?? true }
        list.forEach((f) => { if (next[f.id] === undefined) next[f.id] = true })
        return next
      })
    })
    loadRefs()
  }, [effectiveCompanyId, search, tagFilter, catFilter, itemStatus, loadRefs])

  useEffect(() => { if (isAdmin) api('/admin/companies').then(setAdminCompanies) }, [isAdmin])
  useEffect(load, [load])
  useEffect(() => { if (view === 'list') setActiveFolder(null) }, [view])
  useEffect(() => { setSelectedIds([]) }, [itemStatus, activeFolder])

  const toggleSelect = (id) => {
    setSelectedIds((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))
  }

  const bulkDelete = async () => {
    if (!selectedIds.length || !window.confirm(`Удалить ${selectedIds.length} позиций в корзину?`)) return
    await api(`/companies/${effectiveCompanyId}/catalog/items/bulk-delete`, {
      method: 'POST', body: JSON.stringify({ ids: selectedIds }),
    })
    setSelectedIds([])
    load()
  }

  const bulkRestore = async () => {
    await api(`/companies/${effectiveCompanyId}/catalog/items/bulk-restore`, {
      method: 'POST', body: JSON.stringify({ ids: selectedIds }),
    })
    setSelectedIds([])
    load()
  }

  const bulkMove = async () => {
    const folderId = bulkFolder === '' ? null : bulkFolder === 'none' ? null : Number(bulkFolder)
    await api(`/companies/${effectiveCompanyId}/catalog/items/bulk-move`, {
      method: 'POST', body: JSON.stringify({ ids: selectedIds, folder_id: folderId }),
    })
    setSelectedIds([])
    load()
  }

  const bulkPublish = async (published) => {
    await api(`/companies/${effectiveCompanyId}/catalog/items/bulk-publish`, {
      method: 'POST', body: JSON.stringify({ ids: selectedIds, is_published: published }),
    })
    load()
  }

  const togglePublished = async (item) => {
    await api(`/companies/${effectiveCompanyId}/catalog/items/${item.id}`, {
      method: 'PATCH', body: JSON.stringify({ is_published: !item.is_published }),
    })
    load()
  }

  const addCategoryRef = async (name, parentId = null) => {
    if (!effectiveCompanyId) throw new Error('Компания не выбрана')
    await api(`/companies/${effectiveCompanyId}/catalog/refs/categories`, {
      method: 'POST', body: JSON.stringify({ name, parent_id: parentId }),
    })
    await loadRefs()
  }

  const addTagRef = async (name) => {
    if (!effectiveCompanyId) throw new Error('Компания не выбрана')
    await api(`/companies/${effectiveCompanyId}/catalog/refs/tags`, {
      method: 'POST', body: JSON.stringify({ name }),
    })
    await loadRefs()
  }

  const save = async (e) => {
    e.preventDefault()
    const body = { ...form, price: Number(form.price) || 0 }
    if (editing) {
      await api(`/companies/${effectiveCompanyId}/catalog/${editing}`, { method: 'PATCH', body: JSON.stringify(body) })
    } else {
      await api(`/companies/${effectiveCompanyId}/catalog`, { method: 'POST', body: JSON.stringify(body) })
    }
    setShowForm(false)
    setEditing(null)
    setForm(empty)
    load()
  }

  const renderItems = (list) => {
    if (!list.length) return <p className="folder-empty">Нет позиций</p>
    const inTrash = itemStatus === 'trash'
    if (view === 'list') {
      return (
        <div className="catalog-list">
          {list.map((item) => (
            <ItemRow
              key={item.id}
              item={item}
              fmtPrice={fmtPrice}
              selected={selectedIds.includes(item.id)}
              onSelect={() => toggleSelect(item.id)}
              inTrash={inTrash}
              onDragStart={() => setDragItem(item.id)}
              onTogglePublish={() => togglePublished(item)}
              onEdit={() => { setEditing(item.id); setForm({ ...item, tags: item.tags || [] }); setShowForm(true) }}
              onDelete={async () => {
                if (inTrash) {
                  await api(`/companies/${effectiveCompanyId}/catalog/items/${item.id}`, { method: 'DELETE', ...{} })
                } else {
                  await api(`/companies/${effectiveCompanyId}/catalog/items/${item.id}`, { method: 'DELETE' })
                }
                load()
              }}
              onRestore={async () => {
                await api(`/companies/${effectiveCompanyId}/catalog/items/${item.id}/restore`, { method: 'POST' })
                load()
              }}
            />
          ))}
        </div>
      )
    }
    return (
      <div className="catalog-grid">
        {list.map((item) => (
          <CatalogCard
            key={item.id}
            item={item}
            fmtPrice={fmtPrice}
            selected={selectedIds.includes(item.id)}
            onSelect={() => toggleSelect(item.id)}
            inTrash={inTrash}
            onDragStart={() => setDragItem(item.id)}
            onTogglePublish={() => togglePublished(item)}
            onEdit={() => { setEditing(item.id); setForm({ ...item, tags: item.tags || [] }); setShowForm(true) }}
            onDelete={async () => { await api(`/companies/${effectiveCompanyId}/catalog/items/${item.id}`, { method: 'DELETE' }); load() }}
            onRestore={async () => { await api(`/companies/${effectiveCompanyId}/catalog/items/${item.id}/restore`, { method: 'POST' }); load() }}
          />
        ))}
      </div>
    )
  }

  const itemsInFolder = (fid) => items.filter((i) => i.folder_id === fid)
  const itemsNoFolder = items.filter((i) => !i.folder_id)
  const noModule = company && (!company.module_catalog || perms.catalog === false) && !isAdmin

  const onDropItem = async (itemId, folderId) => {
    const url = folderId != null
      ? `/companies/${effectiveCompanyId}/catalog/items/${itemId}/move?folder_id=${folderId}`
      : `/companies/${effectiveCompanyId}/catalog/items/${itemId}/move`
    await api(url, { method: 'PATCH' })
    load()
  }

  return (
    <PageShell title="Цифровой каталог" loading={loading} error={error} companies={companies} companyId={companyId} onSelect={select} moduleDisabled={noModule} moduleName="Каталог">
      <div className="catalog-tabs">
        <button type="button" className={tab === 'items' ? 'btn' : 'btn btn-outline'} onClick={() => setTab('items')}>Товары и услуги</button>
        <button type="button" className={tab === 'refs' ? 'btn' : 'btn btn-outline'} onClick={() => { setTab('refs'); loadRefs() }}>Справочник</button>
      </div>

      {tab === 'refs' && (
        <>
          <p className="refs-hint card" style={{ marginBottom: '1rem' }}>
            Примеры категорий и тегов уже добавлены. Дополняйте свои — Enter для сохранения. Они появятся при создании товаров.
          </p>
          <div className="grid-2">
            <CategoryRefPanel items={categories} value={newCatName} onChange={setNewCatName} onAdd={addCategoryRef}
              disabled={!effectiveCompanyId}
              onDelete={async (id) => { await api(`/companies/${effectiveCompanyId}/catalog/refs/categories/${id}`, { method: 'DELETE' }); loadRefs() }} />
            <RefPanel title="Теги" items={tagRefs} value={newTagName} onChange={setNewTagName} onAdd={addTagRef}
              disabled={!effectiveCompanyId} placeholder="Новый тег"
              onDelete={async (id) => { await api(`/companies/${effectiveCompanyId}/catalog/refs/tags/${id}`, { method: 'DELETE' }); loadRefs() }} />
          </div>
        </>
      )}

      {tab === 'items' && (
        <>
          <div className="catalog-toolbar card">
            <input placeholder="Поиск…" value={search} onChange={(e) => setSearch(e.target.value)} className="input-unified catalog-toolbar-input" />
            <select value={catFilter} onChange={(e) => setCatFilter(e.target.value)} className="input-unified catalog-toolbar-input">
              <option value="">Все категории</option>
              {categories.map((c) => <option key={c.id} value={c.full_name || c.name}>{c.full_name || c.name}</option>)}
            </select>
            <select value={tagFilter} onChange={(e) => setTagFilter(e.target.value)} className="input-unified catalog-toolbar-input">
              <option value="">Все теги</option>
              {tagRefs.map((t) => <option key={t.id} value={t.name}>{t.name}</option>)}
            </select>
            <select value={itemStatus} onChange={(e) => setItemStatus(e.target.value)} className="input-unified catalog-toolbar-input">
              <option value="active">Активные</option>
              <option value="hidden">Скрытые с витрины</option>
              <option value="trash">Корзина</option>
              <option value="all">Все не удалённые</option>
            </select>
            <div className="view-toggle">
              <button type="button" className={view === 'grid' ? 'active' : ''} onClick={() => setView('grid')}>▦</button>
              <button type="button" className={view === 'list' ? 'active' : ''} onClick={() => setView('list')}>☰</button>
            </div>
            <button type="button" className="btn btn-outline" onClick={() => { setFolderName(''); setShowFolderModal(true) }}>+ Папка</button>
            <button type="button" className="btn" onClick={() => { setShowForm(true); setEditing(null); setForm(empty) }}>+ Товар</button>
          </div>

          {selectedIds.length > 0 && (
            <div className="catalog-toolbar card" style={{ marginTop: '0.5rem' }}>
              <span>Выбрано: {selectedIds.length}</span>
              {itemStatus === 'trash' ? (
                <button type="button" className="btn btn-outline" onClick={bulkRestore}>Восстановить</button>
              ) : (
                <button type="button" className="btn btn-outline" onClick={bulkDelete}>В корзину</button>
              )}
              {itemStatus !== 'trash' && (
                <>
                  <select className="input-unified" value={bulkFolder} onChange={(e) => setBulkFolder(e.target.value)}>
                    <option value="">Переместить в…</option>
                    <option value="none">Без папки</option>
                    {folders.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
                  </select>
                  <button type="button" className="btn btn-outline" onClick={bulkMove} disabled={bulkFolder === ''}>Переместить</button>
                  <button type="button" className="btn btn-outline" onClick={() => bulkPublish(true)}>Показать на витрине</button>
                  <button type="button" className="btn btn-outline" onClick={() => bulkPublish(false)}>Скрыть с витрины</button>
                </>
              )}
            </div>
          )}

          {showFolderModal && (
            <div className="modal-overlay" onClick={() => setShowFolderModal(false)}>
              <form className="card modal-card" onSubmit={async (e) => {
                e.preventDefault()
                if (!folderName.trim()) return
                await api(`/companies/${effectiveCompanyId}/catalog/folders`, { method: 'POST', body: JSON.stringify({ name: folderName.trim() }) })
                setShowFolderModal(false)
                setFolderName('')
                load()
              }} onClick={(ev) => ev.stopPropagation()}>
                <h3>Новая папка</h3>
                <input className="input-unified" value={folderName} onChange={(e) => setFolderName(e.target.value)} required autoFocus />
                <div className="form-actions"><button className="btn" type="submit">Создать</button></div>
              </form>
            </div>
          )}

          {showForm && (
            <form className="card catalog-form" onSubmit={save}>
              <h3>{editing ? 'Редактировать' : 'Новая позиция'}</h3>
              <div className="grid-2">
                <div className="field"><label>Название</label><input className="input-unified" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required /></div>
                <div className="field">
                  <label>Категория (одна)</label>
                  <select className="input-unified" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                    <option value="">— Выберите —</option>
                    {categories.map((c) => <option key={c.id} value={c.full_name || c.name}>{c.full_name || c.name}</option>)}
                  </select>
                </div>
                <div className="field"><label>Цена (₸)</label><input className="input-unified" type="number" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} /></div>
                <div className="field">
                  <label>Папка</label>
                  <select className="input-unified" value={form.folder_id || ''} onChange={(e) => setForm({ ...form, folder_id: e.target.value ? Number(e.target.value) : null })}>
                    <option value="">Без папки</option>
                    {folders.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="field">
                <label>Теги (мультивыбор)</label>
                <TagPicker
                  tags={tagRefs}
                  selected={form.tags}
                  onChange={(tags) => setForm((f) => ({ ...f, tags }))}
                />
              </div>
              <label className="vip-toggle">
                <input type="checkbox" checked={form.is_published !== false} onChange={(e) => setForm({ ...form, is_published: e.target.checked })} />
                Показывать посетителям на публичном каталоге
              </label>
              <ImageDropzone previewUrl={form.image_url} onUpload={async (file) => {
                const { url } = await uploadImage(effectiveCompanyId, file)
                setForm({ ...form, image_url: url })
              }} />
              <div className="field"><label>Описание</label><textarea className="input-unified" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
              <div className="form-actions">
                <button className="btn" type="submit">Сохранить</button>
                <button type="button" className="btn btn-outline" onClick={() => setShowForm(false)}>Отмена</button>
              </div>
            </form>
          )}

          {view === 'grid' && !activeFolder && itemStatus !== 'trash' && (
            <div className="catalog-grid folder-grid">
              {folders.map((folder) => (
                <button key={folder.id} type="button" className="folder-card" onClick={() => setActiveFolder(folder.id)}>
                  <span className="folder-card-icon">📁</span>
                  <strong>{folder.name}</strong>
                  <span className="emp-meta">{itemsInFolder(folder.id).length} поз.</span>
                </button>
              ))}
              <button type="button" className="folder-card" onClick={() => setActiveFolder('none')}>
                <span className="folder-card-icon">📂</span>
                <strong>Без папки</strong>
                <span className="emp-meta">{itemsNoFolder.length} поз.</span>
              </button>
            </div>
          )}

          {(view === 'grid' && activeFolder) || itemStatus === 'trash' || view === 'list' ? (
            <div className="folder-detail card" style={{ marginTop: '1rem' }}>
              {view === 'grid' && activeFolder && (
                <div className="folder-detail-head">
                  <button type="button" className="btn btn-outline" onClick={() => setActiveFolder(null)}>← К папкам</button>
                  <h3>{activeFolder === 'none' ? 'Без папки' : folders.find((f) => f.id === activeFolder)?.name}</h3>
                </div>
              )}
              {itemStatus === 'trash' && <h3>Корзина</h3>}
              <div onDragOver={(e) => e.preventDefault()} onDrop={() => {
                if (!dragItem || itemStatus === 'trash') return
                onDropItem(dragItem, activeFolder === 'none' ? null : activeFolder)
              }}>
                {view === 'grid' && activeFolder
                  ? renderItems(activeFolder === 'none' ? itemsNoFolder : itemsInFolder(activeFolder))
                  : itemStatus === 'trash'
                    ? renderItems(items)
                    : view === 'list' && (
                      <>
                        {folders.map((folder) => (
                          <FolderBlock key={folder.id} title={folder.name} count={itemsInFolder(folder.id).length}
                            open={!!openFolders[folder.id]} onToggle={() => setOpenFolders((p) => ({ ...p, [folder.id]: !p[folder.id] }))}
                            onDragOver={(e) => e.preventDefault()} onDrop={() => dragItem && onDropItem(dragItem, folder.id)}
                            empty={!itemsInFolder(folder.id).length}>
                            {renderItems(itemsInFolder(folder.id))}
                          </FolderBlock>
                        ))}
                        <FolderBlock title="Без папки" count={itemsNoFolder.length} open={!!openFolders.none}
                          onToggle={() => setOpenFolders((p) => ({ ...p, none: !p.none }))}
                          onDragOver={(e) => e.preventDefault()} onDrop={() => dragItem && onDropItem(dragItem, null)}
                          empty={!itemsNoFolder.length}>
                          {renderItems(itemsNoFolder)}
                        </FolderBlock>
                      </>
                    )}
              </div>
            </div>
          ) : null}
        </>
      )}
    </PageShell>
  )
}

function CatalogCard({ item, fmtPrice, selected, onSelect, inTrash, onDragStart, onTogglePublish, onEdit, onDelete, onRestore }) {
  return (
    <article className="catalog-item-card" draggable={!inTrash} onDragStart={onDragStart}>
      <div className="catalog-card-top">
        <label className="bulk-check"><input type="checkbox" checked={selected} onChange={onSelect} /></label>
        {!item.is_published && <span className="item-badge-unpub">Скрыт</span>}
        {inTrash && <span className="item-badge-trash">Корзина</span>}
      </div>
      {item.image_url && <img src={item.image_url} alt="" className="catalog-thumb" />}
      <div className="catalog-item-body">
        <h4>{item.title}</h4>
        <p className="emp-meta">{item.category || '—'}</p>
        <div className="perm-tags">{item.tags?.map((t) => <span key={t} className="perm-tag">{t}</span>)}</div>
        <p className="catalog-price">{fmtPrice(item.price)} ₸</p>
      </div>
      <div className="catalog-item-actions">
        {!inTrash && (
          <button type="button" className="btn btn-outline btn-sm" onClick={onTogglePublish}>
            {item.is_published ? 'Скрыть с витрины' : 'На витрину'}
          </button>
        )}
        <button type="button" className="btn btn-outline btn-sm" onClick={onEdit}>Изменить</button>
        {inTrash ? (
          <button type="button" className="btn btn-outline btn-sm" onClick={onRestore}>Восстановить</button>
        ) : (
          <button type="button" className="btn btn-outline btn-sm btn-danger-outline" onClick={onDelete}>В корзину</button>
        )}
      </div>
    </article>
  )
}

function ItemRow({ item, fmtPrice, selected, onSelect, inTrash, onDragStart, onTogglePublish, onEdit, onDelete, onRestore }) {
  return (
    <div className="catalog-list-row" draggable={!inTrash} onDragStart={onDragStart}>
      <label className="bulk-check"><input type="checkbox" checked={selected} onChange={onSelect} /></label>
      {item.image_url ? <img src={item.image_url} alt="" className="catalog-list-thumb" /> : <div className="catalog-list-thumb catalog-list-thumb-empty">—</div>}
      <div className="catalog-list-info">
        <strong>{item.title}</strong>
        <span className="emp-meta">{item.category}</span>
        <div className="perm-tags">{item.tags?.map((t) => <span key={t} className="perm-tag">{t}</span>)}</div>
      </div>
      <div className="catalog-list-price">{fmtPrice(item.price)} ₸</div>
      <div className="catalog-item-actions catalog-item-actions--row">
        {!inTrash && <button type="button" className="btn btn-outline btn-sm" onClick={onTogglePublish}>{item.is_published ? 'Скрыть' : 'Витрина'}</button>}
        <button type="button" className="btn btn-outline btn-sm" onClick={onEdit}>Изменить</button>
        {inTrash ? <button type="button" className="btn btn-outline btn-sm" onClick={onRestore}>Восстановить</button> : <button type="button" className="btn btn-outline btn-sm btn-danger-outline" onClick={onDelete}>Корзина</button>}
      </div>
    </div>
  )
}
