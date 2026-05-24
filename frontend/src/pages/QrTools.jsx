import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api/client'
import PageShell from '../components/PageShell'
import { useCompany } from '../hooks/useCompany'
import { useUser } from '../hooks/useUser'

const BUILTIN_PRESETS = [
  { id: 'neon', label: 'Неон', accentClass: 'template-btn-neon' },
  { id: 'sunset', label: 'Закат', accentClass: 'template-btn-sunset' },
  { id: 'festive', label: 'Праздничный', accentClass: 'template-btn-festive' },
  { id: 'luxury', label: 'Премиум', accentClass: 'template-btn-luxury' },
]

const DEFAULT_CUSTOM = {
  bg_color: '#1e293b',
  fg_color: '#ffffff',
  accent_color: '#3d9cf5',
  accent2_color: '#a855f7',
  qr_scale: 0.52,
  show_dots: true,
  show_stars: false,
  show_gradient: true,
  show_badge: true,
  frame_style: 'rounded',
}

const SOCIAL = [
  { key: 'telegram', label: 'Telegram' },
  { key: 'whatsapp', label: 'WhatsApp' },
  { key: 'facebook', label: 'Facebook' },
  { key: 'vk', label: 'VK' },
  { key: 'linkedin', label: 'LinkedIn' },
]

const BASE_TARGETS = [
  { id: 'profile', label: 'Страница компании' },
  { id: 'catalog', label: 'Каталог' },
  { id: 'lead', label: 'Форма заявки' },
  { id: 'contacts', label: 'Контакты' },
]

function buildQrImageUrl(companyId, target, templateKey, customConfig) {
  const params = new URLSearchParams({ target, styled: 'true', template: templateKey })
  if (customConfig && Object.keys(customConfig).length > 0) {
    params.set('custom_json', JSON.stringify(customConfig))
  }
  params.set('_', String(Date.now()))
  return `/api/companies/${companyId}/qr/image?${params.toString()}`
}

export default function QrTools() {
  const { companies, company, companyId, select, loading, error } = useCompany()
  const { permsFor } = useUser()
  const perms = permsFor(companyId)
  const [target, setTarget] = useState('profile')
  const [mode, setMode] = useState('presets')
  const [templateKey, setTemplateKey] = useState('brand')
  const [custom, setCustom] = useState(DEFAULT_CUSTOM)
  const [savedTemplates, setSavedTemplates] = useState([])
  const [customLinks, setCustomLinks] = useState([])
  const [saveName, setSaveName] = useState('')
  const [linkName, setLinkName] = useState('')
  const [linkUrl, setLinkUrl] = useState('')
  const [links, setLinks] = useState(null)
  const [share, setShare] = useState(null)
  const [qrBlob, setQrBlob] = useState(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const blobRef = useRef(null)

  const targetOptions = useMemo(() => [
    ...BASE_TARGETS,
    ...customLinks.map((l) => ({ id: `link:${l.id}`, label: l.name })),
  ], [customLinks])

  const isSavedTemplate = templateKey.startsWith('saved:')
  const isEditingCustom = mode === 'custom' && !isSavedTemplate

  const activeCustom = useMemo(() => {
    if (isEditingCustom) return custom
    return null
  }, [isEditingCustom, custom])

  const previewSignature = useMemo(
    () => JSON.stringify({ target, templateKey, custom: activeCustom }),
    [target, templateKey, activeCustom],
  )

  const loadSaved = useCallback(() => {
    if (!companyId) return
    api(`/companies/${companyId}/qr/templates`).then((list) => {
      setSavedTemplates(list.filter((t) => !t.is_system && t.id))
    }).catch(() => setSavedTemplates([]))
  }, [companyId])

  const loadCustomLinks = useCallback(() => {
    if (!companyId) return
    api(`/companies/${companyId}/qr/custom-links`).then(setCustomLinks).catch(() => setCustomLinks([]))
  }, [companyId])

  useEffect(loadSaved, [loadSaved])
  useEffect(loadCustomLinks, [loadCustomLinks])

  const fetchPreview = useCallback(() => {
    if (!companyId || perms.qr === false) return
    const url = buildQrImageUrl(companyId, target, templateKey, activeCustom)
    const token = localStorage.getItem('dot_token')
    setPreviewLoading(true)
    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((r) => (r.ok ? r.blob() : Promise.reject()))
      .then((b) => {
        if (blobRef.current) URL.revokeObjectURL(blobRef.current)
        blobRef.current = URL.createObjectURL(b)
        setQrBlob(blobRef.current)
      })
      .catch(() => setQrBlob(null))
      .finally(() => setPreviewLoading(false))
  }, [companyId, target, templateKey, activeCustom, perms.qr])

  useEffect(() => {
    const timer = setTimeout(fetchPreview, 300)
    return () => clearTimeout(timer)
  }, [previewSignature, fetchPreview])

  useEffect(() => {
    if (!companyId || perms.qr === false) return
    api(`/companies/${companyId}/qr/links?target=${encodeURIComponent(target)}&template=${templateKey}`).then(setLinks)
    api(`/companies/${companyId}/qr/share?target=${encodeURIComponent(target)}`).then(setShare)
  }, [companyId, target, templateKey, perms.qr])

  const selectPreset = (id) => {
    setMode('presets')
    setTemplateKey(id)
  }

  const selectSaved = (t) => {
    setMode('presets')
    setTemplateKey(`saved:${t.id}`)
  }

  const saveTemplate = async () => {
    if (!saveName.trim() || !companyId) return
    await api(`/companies/${companyId}/qr/templates`, {
      method: 'POST',
      body: JSON.stringify({ name: saveName.trim(), base_template: 'custom', config: custom }),
    })
    setSaveName('')
    loadSaved()
    setMode('presets')
  }

  const deleteSaved = async (id, name) => {
    if (!window.confirm(`Удалить шаблон «${name}»?`)) return
    await api(`/companies/${companyId}/qr/templates/${id}`, { method: 'DELETE' })
    if (templateKey === `saved:${id}`) setTemplateKey('brand')
    loadSaved()
  }

  const addCustomLink = async () => {
    if (!linkName.trim() || !linkUrl.trim()) return
    const row = await api(`/companies/${companyId}/qr/custom-links`, {
      method: 'POST',
      body: JSON.stringify({ name: linkName.trim(), url: linkUrl.trim() }),
    })
    setLinkName('')
    setLinkUrl('')
    loadCustomLinks()
    setTarget(`link:${row.id}`)
  }

  const deleteCustomLink = async (id, name) => {
    if (!window.confirm(`Удалить ссылку «${name}»?`)) return
    await api(`/companies/${companyId}/qr/custom-links/${id}`, { method: 'DELETE' })
    if (target === `link:${id}`) setTarget('profile')
    loadCustomLinks()
  }

  const downloadQr = () => {
    if (!qrBlob || !company) return
    const a = document.createElement('a')
    a.href = qrBlob
    a.download = `qr-${company.slug}-${target.replace(':', '-')}.png`
    a.click()
  }

  const noModule = company && (!company.module_qr || perms.qr === false)
  const targetLabel = targetOptions.find((t) => t.id === target)?.label || ''

  return (
    <PageShell title="QR-инструменты" loading={loading} error={error} companies={companies} companyId={companyId} onSelect={select} moduleDisabled={noModule} moduleName="QR">
      <div className="qr-mode-tabs">
        <button type="button" className={mode === 'presets' ? 'btn' : 'btn btn-outline'} onClick={() => { setMode('presets'); setTemplateKey('brand') }}>
          Готовые шаблоны
        </button>
        <button type="button" className={mode === 'custom' ? 'btn' : 'btn btn-outline'} onClick={() => { setMode('custom'); setTemplateKey('custom'); setCustom(DEFAULT_CUSTOM) }}>
          Конструктор (новый шаблон)
        </button>
      </div>

      <div className="qr-builder-layout">
        <div className="qr-builder-controls card">
          <div className="field">
            <label>Куда ведёт QR</label>
            <select className="input-unified" value={target} onChange={(e) => setTarget(e.target.value)}>
              {targetOptions.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
          </div>

          {mode === 'presets' && (
            <div className="field">
              <label>Шаблон оформления</label>
              <p className="emp-meta">Минимальный и Брендовый — системные. Сохранённые шаблоны только выбираются (не редактируются).</p>
              <div className="template-picker">
                <button type="button" className={`template-btn ${templateKey === 'minimal' ? 'active' : ''}`} onClick={() => selectPreset('minimal')}>Минимальный</button>
                <button type="button" className={`template-btn ${templateKey === 'brand' ? 'active' : ''}`} onClick={() => selectPreset('brand')}>Брендовый</button>
                {BUILTIN_PRESETS.map((t) => (
                  <button key={t.id} type="button" className={`template-btn ${t.accentClass} ${templateKey === t.id ? 'active' : ''}`} onClick={() => selectPreset(t.id)}>{t.label}</button>
                ))}
              </div>
              {savedTemplates.length > 0 && (
                <>
                  <label className="profile-label" style={{ display: 'block', marginTop: '1rem' }}>Мои сохранённые шаблоны</label>
                  <div className="template-picker">
                    {savedTemplates.map((t) => (
                      <div key={t.id} className="saved-tpl-wrap">
                        <button type="button" className={`template-btn ${templateKey === `saved:${t.id}` ? 'active' : ''}`} onClick={() => selectSaved(t)}>{t.name}</button>
                        <button type="button" className="ref-del" title="Удалить" onClick={() => deleteSaved(t.id, t.name)}>×</button>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {isEditingCustom && (
            <>
              <p className="emp-meta">Настройте вид и сохраните — после сохранения шаблон можно только выбрать или удалить.</p>
              <div className="qr-control-group">
                <label>Фон</label>
                <div className="qr-color-row">
                  <input type="color" value={custom.bg_color} onChange={(e) => setCustom((c) => ({ ...c, bg_color: e.target.value }))} />
                  <input className="input-unified" value={custom.bg_color} onChange={(e) => setCustom((c) => ({ ...c, bg_color: e.target.value }))} />
                </div>
              </div>
              <div className="qr-control-group">
                <label>Размер QR ({Math.round(custom.qr_scale * 100)}%)</label>
                <input type="range" className="qr-range" min="0.32" max="0.65" step="0.01" value={custom.qr_scale} onChange={(e) => setCustom((c) => ({ ...c, qr_scale: Number(e.target.value) }))} />
              </div>
              <div className="field">
                <label>Сохранить шаблон</label>
                <div className="ref-form-row">
                  <input className="input-unified" value={saveName} onChange={(e) => setSaveName(e.target.value)} placeholder="Название шаблона" />
                  <button type="button" className="btn btn-outline" onClick={saveTemplate}>Сохранить</button>
                </div>
              </div>
            </>
          )}

          <div className="card" style={{ marginTop: '1rem', background: 'var(--surface2)' }}>
            <h4>Созданные мной ссылки</h4>
            <p className="emp-meta">Свои URL для QR (сайт, акция, форма и т.д.)</p>
            <div className="ref-form-row">
              <input className="input-unified" placeholder="Название" value={linkName} onChange={(e) => setLinkName(e.target.value)} />
            </div>
            <div className="ref-form-row" style={{ marginTop: '0.5rem' }}>
              <input className="input-unified" placeholder="https://…" value={linkUrl} onChange={(e) => setLinkUrl(e.target.value)} />
              <button type="button" className="btn btn-outline" onClick={addCustomLink}>Добавить</button>
            </div>
            <ul className="ref-list scroll-panel" style={{ marginTop: '0.75rem', maxHeight: 140 }}>
              {customLinks.map((l) => (
                <li key={l.id}>
                  <span>{l.name}</span>
                  <button type="button" className="ref-del" onClick={() => deleteCustomLink(l.id, l.name)}>×</button>
                </li>
              ))}
            </ul>
          </div>

          {links && (
            <>
              <p style={{ wordBreak: 'break-all', color: 'var(--muted)', fontSize: '0.9rem', marginTop: '0.75rem' }}>{links.url}</p>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <a className="btn btn-outline" href={links.url} target="_blank" rel="noreferrer">Открыть</a>
                <button type="button" className="btn" onClick={downloadQr} disabled={!qrBlob}>Скачать PNG</button>
              </div>
            </>
          )}
        </div>

        <div className="qr-builder-preview card">
          <h3>Предпросмотр {previewLoading && <span className="emp-meta">…</span>}</h3>
          <p className="qr-preview-caption-top">{targetLabel}</p>
          <div className="qr-grid-canvas qr-preview-safe">
            {qrBlob ? <img src={qrBlob} alt="QR" key={previewSignature} /> : <div className="qr-placeholder">…</div>}
          </div>
          <p className="emp-meta" style={{ textAlign: 'center', marginTop: '0.5rem' }}>{company?.name}</p>
        </div>
      </div>

      {share && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <h3>Соцсети</h3>
          <div className="social-share-row">
            {SOCIAL.map((s) => (
              <a key={s.key} className="social-btn" href={share[s.key]} target="_blank" rel="noreferrer">{s.label}</a>
            ))}
          </div>
        </div>
      )}
    </PageShell>
  )
}
