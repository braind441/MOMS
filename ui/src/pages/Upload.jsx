import { useState, useRef } from 'react'

export default function Upload() {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const inputRef = useRef(null)

  async function uploadFiles(files) {
    setUploading(true)
    setResult(null)
    const form = new FormData()
    for (const f of files) form.append('files', f)
    try {
      const res = await fetch('/api/upload/', { method: 'POST', body: form })
      setResult(await res.json())
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setUploading(false)
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    uploadFiles(Array.from(e.dataTransfer.files))
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-lg font-bold mb-4">Upload</h1>
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-16 text-center cursor-pointer transition-colors ${
          dragging ? 'border-blue-500 bg-blue-950' : 'border-gray-600 hover:border-gray-500'
        }`}
      >
        <p className="text-gray-400 text-sm">
          {uploading ? 'Uploading...' : 'Перетащи MP3/FLAC файлы или кликни для выбора'}
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".mp3,.flac,.m4a,.ogg"
          className="hidden"
          onChange={e => uploadFiles(Array.from(e.target.files))}
        />
      </div>
      {result && (
        <div className="mt-4 bg-gray-800 rounded p-3 text-sm">
          {result.error
            ? <span className="text-red-400">{result.error}</span>
            : <span className="text-green-400">Сохранено: {result.saved.join(', ') || 'нет допустимых файлов'}</span>
          }
        </div>
      )}
    </div>
  )
}
