import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, uploadImage, uploadLogo } from '../api/client'
import CompanyPicker from '../components/CompanyPicker'
import ImageDropzone from '../components/ImageDropzone'
import { useCompany } from '../hooks/useCompany'

export default function CompanySettings() {
  const { companies, company, companyId, select, loading, setCompanies } = useCompany()
  const [form, setForm] = useState(null)
  const [slides, setSlides] = useState([])
  const [slideCaption, setSlideCaption] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (company) setForm({ ...company })
  }, [company])

  useEffect(() => {
    if (!companyId) return
    api(`/companies/${companyId}/slides`).then(setSlides).catch(() => setSlides([]))
  }, [companyId])

  const save = async (e) => {
    e.preventDefault()
    const updated = await api(`/companies/${companyId}`, {
      method: 'PATCH',
      body: JSON.stringify(form),
    })
    setCompanies((list) => list.map((c) => (c.id === updated.id ? updated : c)))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const onLogo = async (file) => {
    const { url } = await uploadLogo(companyId, file)
    setForm((f) => ({ ...f, logo_url: url }))
    const updated = await api(`/companies/${companyId}`, { method: 'PATCH', body: JSON.stringify({ logo_url: url }) })
    setCompanies((list) => list.map((c) => (c.id === updated.id ? updated : c)))
  }

  const addSlide = async (file) => {
    const { url } = await uploadImage(companyId, file)
    const slide = await api(`/companies/${companyId}/slides`, {
      method: 'POST',
      body: JSON.stringify({ image_url: url, caption: slideCaption }),
    })
    setSlides((s) => [...s, slide])
    setSlideCaption('')
  }

  const removeSlide = async (id) => {
    await api(`/companies/${companyId}/slides/${id}`, { method: 'DELETE' })
    setSlides((s) => s.filter((x) => x.id !== id))
  }

  if (loading) return <p>Загрузка…</p>

  return (
    <div>
      <h1 className="page-title">Личный кабинет компании</h1>
      <CompanyPicker companies={companies} companyId={companyId} onSelect={select} />

      {form && (
        <form className="card" onSubmit={save}>
          <h3 className="section-title">Бренд и публичная страница</h3>
          <p className="emp-meta field-hint">Логотип и слайдер видят клиенты при сканировании QR «Страница компании».</p>
          <div className="brand-upload-row">
            <div className="brand-logo-block">
              <label className="profile-label">Логотип / аватарка</label>
              {form.logo_url ? (
                <img src={form.logo_url} alt="" className="company-logo-preview" />
              ) : (
                <div className="company-logo-placeholder">Нет лого</div>
              )}
              <ImageDropzone previewUrl={form.logo_url} onUpload={onLogo} />
            </div>
            <div className="brand-slides-block">
              <label className="profile-label">Слайдер (до 10 фото)</label>
              <input
                className="input-unified"
                placeholder="Подпись к новому слайду (необязательно)"
                value={slideCaption}
                onChange={(e) => setSlideCaption(e.target.value)}
              />
              <ImageDropzone onUpload={addSlide} />
              <ul className="slide-admin-list">
                {slides.map((s) => (
                  <li key={s.id} className="slide-admin-item">
                    <img src={s.image_url} alt="" />
                    <span>{s.caption || 'Без подписи'}</span>
                    <button type="button" className="btn btn-outline btn-sm" onClick={() => removeSlide(s.id)}>×</button>
                  </li>
                ))}
              </ul>
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

          <button className="btn" type="submit" style={{ marginTop: '1.25rem' }}>
            {saved ? 'Сохранено ✓' : 'Сохранить'}
          </button>
        </form>
      )}

      <p style={{ marginTop: '1rem' }}>
        <Link to="/app/company">+ Добавить ещё одну компанию</Link>
      </p>
    </div>
  )
}
