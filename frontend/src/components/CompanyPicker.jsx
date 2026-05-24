export default function CompanyPicker({ companies, companyId, onSelect }) {
  if (!companies.length) return null
  return (
    <div className="field company-picker-field">
      <label>Активная компания</label>
      <select value={companyId || ''} onChange={(e) => onSelect(Number(e.target.value))}>
        {companies.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>
    </div>
  )
}
