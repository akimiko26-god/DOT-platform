import { useRef, useState } from 'react'

export default function ImageDropzone({ onUpload, previewUrl }) {
  const inputRef = useRef(null)
  const [drag, setDrag] = useState(false)
  const [uploading, setUploading] = useState(false)

  const handleFiles = async (files) => {
    const file = files?.[0]
    if (!file || !file.type.startsWith('image/')) return
    setUploading(true)
    try {
      await onUpload(file)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div
      className={`dropzone ${drag ? 'drag-active' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDrag(false)
        handleFiles(e.dataTransfer.files)
      }}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => handleFiles(e.target.files)}
      />
      {previewUrl ? (
        <img src={previewUrl} alt="" className="dropzone-preview" />
      ) : (
        <p>{uploading ? 'Загрузка…' : 'Перетащите изображение или нажмите для выбора'}</p>
      )}
    </div>
  )
}
