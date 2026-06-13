import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, uploadImage, uploadLogo } from '../api/client'
import CompanyPicker from '../components/CompanyPicker'
import { useCompany } from '../hooks/useCompany'

export default function CompanySettings() {
  const { companies, company, companyId, select, loading, setCompanies } = useCompany()
  const [form, setForm] = useState(null)
  const [draftSlides, setDraftSlides] = useState([])
  const [slideCaption, setSlideCaption] = useState('')
  const [saved, setSaved] = useState(false)
  const [logoFile, setLogoFile] = useState(null)
  const [logoPreview, setLogoPreview] = useState('')
  const fileInputRef = useRef(null)
  const slideInputRef = useRef(null)

  useEffect(() => {
    if (company) {
      setForm({ ...company })
      setLogoPreview(company.logo_url || '')
      setLogoFile(null)
    }
  }, [company])

  useEffect(() => {
    if (!companyId) return
    api(`/companies/${companyId}/slides`)
      .then((list) => setDraftSlides(list.map((s) => ({ image_url: s.image_url, caption: s.caption || '' }))))
      .catch(() => setDraftSlides([]))
  }, [companyId])

  const onPickLogo = (file) => {
    setLogoFile(file)
    setLogoPreview(URL.createObjectURL(file))
  }

  const onPickSlide = async (file) => {
    const { url } = await uploadImage(companyId, file)
    setDraftSlides((s) => [...s, { image_url: url, caption: slideCaption }].slice(0, 10))
    setSlideCaption('')
  }

  const removeDraftSlide = (idx) => {
    setDraftSlides((s) => s.filter((_, i) => i !== idx))
  }

  const save = async (e) => {
    e.preventDefault()
    let logoUrl = form.logo_url
    if (logoFile) {
      const { url } = await uploadLogo(companyId, logoFile)
      logoUrl = url
    }
    const payload = { ...form, logo_url: logoUrl }
    const updated = await api(`/companies/${companyId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
    await api(`/companies/${companyId}/slides`, {
      method: 'PUT',
      body: JSON.stringify({ slides: draftSlides }),
    })
    setCompanies((list) => list.map((c) => (c.id === updated.id ? updated : c)))
    setForm({ ...updated })
    setLogoFile(null)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  if (loading) return <p className="page-empty">Загрузка…</p>

  return (
    <div>
      <h1 className="page-title">Личный кабинет компании</h1>
      <CompanyPicker companies={companies} companyId={companyId} onSelect={select} />

      {form && (
        <form className="card card-padded" onSubmit={save}>
          <h3 className="section-title">Бренд и публичная страница</h3>
          <p className="emp-meta field-hint">Логотип и слайдер сохраняются кнопкой «Сохранить» внизу формы.</p>
          <div className="brand-upload-row">
            <div className="brand-logo-block">
              <label className="profile-label">Логотип / аватарка</label>
              {logoPreview ? (
                <img src={logoPreview} alt="" className="company-logo-preview" />
              ) : (
                <div className="company-logo-placeholder">Нет лого</div>
              )}
              <input type="file" accept="image/*" hidden ref={fileInputRef} onChange={(e) => e.target.files?.[0] && onPickLogo(e.target.files[0])} />
              <button type="button" className="btn btn-outline btn-sm" onClick={() => fileInputRef.current?.click()}>Выбрать файл</button>
            </div>
            <div className="brand-slides-block">
              <label className="profile-label">Слайдер (до 10 фото)</label>
              <input
                className="input-unified"
                placeholder="Подпись к новому слайду (необязательно)"
                value={slideCaption}
                onChange={(e) => setSlideCaption(e.target.value)}
              />
              <div className="slide-grid-row">
                {draftSlides.map((s, idx) => (
                  <div key={`${s.image_url}-${idx}`} className="slide-grid-item">
                    <img src={s.image_url} alt="" />
                    <button type="button" className="slide-grid-remove" onClick={() => removeDraftSlide(idx)} aria-label="Удалить">×</button>
                  </div>
                ))}
                {draftSlides.length < 10 && (
                  <>
                    <input type="file" accept="image/*" hidden ref={slideInputRef} onChange={(e) => e.target.files?.[0] && onPickSlide(e.target.files[0])} />
                    <button type="button" className="slide-grid-add" onClick={() => slideInputRef.current?.click()} aria-label="Добавить фото">+</button>
                  </>
                )}
              </div>
            </div>
          </div>

          <h3 className="section-title">Реквизиты юр. лица</h3>
          <div className="grid-2">
            <div className="field"><label>Директор</label><input className="input-unified" value={form.director_name || ''} onChange={(e) => setForm({ ...form, director_name: e.target.value })} /></div>
            <div className="field"><label>БИН / ИИН</label><input className="input-unified" value={form.bin_iin || ''} onChange={(e) => setForm({ ...form, bin_iin: e.target.value })} /></div>
            <div className="field field-span-2"><label>Юридический адрес</label><input className="input-unified" value={form.legal_address || ''} onChange={(e) => setForm({ ...form, legal_address: e.target.value })} /></div>
          </div>
          <h3 className="section-title">Контакты</h3>
          <div className="grid-2">
            <div className="field"><label>Название</label><input className="input-unified" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
            <div className="field"><label>Телефон</label><input className="input-unified" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
            <div className="field"><label>Email</label><input className="input-unified" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
            <div className="field"><label>Фактический адрес</label><input className="input-unified" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></div>
            <div className="field"><label>WhatsApp (номер)</label><input className="input-unified" value={form.whatsapp} onChange={(e) => setForm({ ...form, whatsapp: e.target.value })} placeholder="77001234567" /></div>
            <div className="field"><label>Telegram (@username)</label><input className="input-unified" value={form.telegram} onChange={(e) => setForm({ ...form, telegram: e.target.value })} placeholder="mycompany" /></div>
            <div className="field"><label>Instagram</label><input className="input-unified" value={form.instagram} onChange={(e) => setForm({ ...form, instagram: e.target.value })} /></div>
            <div className="field"><label>График работы</label><input className="input-unified" value={form.work_schedule} onChange={(e) => setForm({ ...form, work_schedule: e.target.value })} /></div>
          </div>
          <div className="field">
            <label>Описание</label>
            <p className="field-hint">Переносы строк сохраняются — нажмите Enter для нового абзаца.</p>
            <textarea className="input-unified textarea-tall" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          <div className="field">
            <label>Направления деятельности</label>
            <textarea className="input-unified textarea-tall" value={form.activities} onChange={(e) => setForm({ ...form, activities: e.target.value })} />
          </div>

          <h3 className="section-title">Модули платформы</h3>
          <div className="module-toggles">
            {[
              ['module_leads', 'Заявки'],
              ['module_crm', 'CRM'],
              ['module_catalog', 'Каталог'],
              ['module_qr', 'QR'],
            ].map(([key, label]) => (
              <label key={key} className="module-toggle">
                <input type="checkbox" checked={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.checked })} />
                {label}
              </label>
            ))}
          </div>

          <button className="btn form-submit-btn" type="submit">
            {saved ? 'Сохранено ✓' : 'Сохранить'}
          </button>
        </form>
      )}

      <p className="page-footer-link">
        <Link to="/app/company">+ Добавить ещё одну компанию</Link>
      </p>
    </div>
  )
}
