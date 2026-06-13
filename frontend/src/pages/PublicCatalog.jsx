import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import FormattedText from '../components/FormattedText'

export default function PublicCatalog() {
  const { slug } = useParams()
  const [items, setItems] = useState([])

  useEffect(() => {
    api(`/public/companies/${slug}/catalog`).then(setItems)
  }, [slug])

  return (
    <div className="container public-inner">
      <Link to={`/c/${slug}`} style={{ color: 'var(--muted)' }}>← Назад</Link>
      <h1 style={{ margin: '1rem 0' }}>Каталог</h1>
      <div className="grid-2">
        {items.map((item) => (
          <article key={item.id} className="card">
            {item.image_url && (
              <img src={item.image_url} alt="" style={{ width: '100%', height: 160, objectFit: 'cover', borderRadius: 8, marginBottom: '0.75rem' }} />
            )}
            <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>{item.category}</span>
            <h3 style={{ margin: '0.35rem 0' }}>{item.title}</h3>
            <p className="catalog-price">{item.price.toLocaleString('ru')} ₸</p>
            <FormattedText text={item.description} className="text-muted catalog-desc" />
          </article>
        ))}
      </div>
      {items.length === 0 && <p style={{ color: 'var(--muted)' }}>Каталог пуст</p>}
      <Link className="btn" to={`/c/${slug}/contact`} style={{ marginTop: '1.5rem', display: 'inline-flex' }}>
        Оставить заявку
      </Link>
    </div>
  )
}
