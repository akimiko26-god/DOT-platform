import { useEffect, useState } from 'react'

export default function HeroSlider({ slides = [] }) {
  const [idx, setIdx] = useState(0)

  useEffect(() => {
    if (slides.length < 2) return undefined
    const t = setInterval(() => setIdx((i) => (i + 1) % slides.length), 5000)
    return () => clearInterval(t)
  }, [slides.length])

  if (!slides.length) return null
  const slide = slides[idx]

  return (
    <div className="hero-slider">
      <img src={slide.image_url} alt={slide.caption || ''} className="hero-slider-img" />
      {slide.caption && <p className="hero-slider-caption">{slide.caption}</p>}
      {slides.length > 1 && (
        <div className="hero-slider-dots">
          {slides.map((s, i) => (
            <button
              key={s.id || i}
              type="button"
              className={`hero-dot ${i === idx ? 'active' : ''}`}
              aria-label={`Слайд ${i + 1}`}
              onClick={() => setIdx(i)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
