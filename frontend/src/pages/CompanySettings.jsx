import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import CompanyPicker from '../components/CompanyPicker'
import { useCompany } from '../hooks/useCompany'

export default function CompanySettings() {
  const { companies, company, companyId, select, loading, setCompanies } = useCompany()
  const [form, setForm] = useState(null)
  const [saved, setSaved] = useState(false)
  useEffect(() => {
    if (company) setForm({ ...company })
  }, [company])

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

  if (loading) return <p>Загрузка…</p>

  return (
    <div>
      <h1 className="page-title">Личный кабинет компании</h1>
      <CompanyPicker companies={companies} companyId={companyId} onSelect={select} />

      {form && (
        <form className="card" onSubmit={save}>
          <h3 style={{ margin: '0 0 0.75rem' }}>Реквизиты юр. лица</h3>
          <div className="grid-2">
            <div className="field"><label>Директор</label><input className="input-unified" value={form.director_name || ''} onChange={(e) => setForm({ ...form, director_name: e.target.value })} /></div>
            <div className="field"><label>БИН / ИИН</label><input className="input-unified" value={form.bin_iin || ''} onChange={(e) => setForm({ ...form, bin_iin: e.target.value })} /></div>
            <div className="field field-span-2"><label>Юридический адрес</label><input className="input-unified" value={form.legal_address || ''} onChange={(e) => setForm({ ...form, legal_address: e.target.value })} /></div>
          </div>
          <h3 style={{ margin: '1.25rem 0 0.75rem' }}>Контакты</h3>
          <div className="grid-2">
            <div className="field"><label>Название</label><input className="input-unified" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
            <div className="field"><label>Телефон</label><input className="input-unified" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
            <div className="field"><label>Email</label><input className="input-unified" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
            <div className="field"><label>Фактический адрес</label><input className="input-unified" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></div>
            <div className="field"><label>WhatsApp (номер)</label><input value={form.whatsapp} onChange={(e) => setForm({ ...form, whatsapp: e.target.value })} placeholder="77001234567" /></div>
            <div className="field"><label>Telegram (@username)</label><input value={form.telegram} onChange={(e) => setForm({ ...form, telegram: e.target.value })} placeholder="mycompany" /></div>
            <div className="field"><label>Instagram</label><input value={form.instagram} onChange={(e) => setForm({ ...form, instagram: e.target.value })} /></div>
            <div className="field"><label>График работы</label><input value={form.work_schedule} onChange={(e) => setForm({ ...form, work_schedule: e.target.value })} /></div>
          </div>
          <div className="field"><label>Описание</label><textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
          <div className="field"><label>Направления деятельности</label><textarea value={form.activities} onChange={(e) => setForm({ ...form, activities: e.target.value })} /></div>

          <h3 style={{ margin: '1.25rem 0 0.75rem' }}>Модули платформы</h3>
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
