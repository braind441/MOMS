import { useState } from 'react'

export default function Import() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function handleImport() {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await fetch('/api/playlist/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Error')
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-lg font-bold mb-4">Import Playlist</h1>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && url && !loading && handleImport()}
          placeholder="Yandex / Spotify / SoundCloud playlist URL"
          className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={handleImport}
          disabled={loading || !url}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-40 px-4 py-2 rounded text-sm"
        >
          {loading ? 'Loading...' : 'Import'}
        </button>
      </div>
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {result && (
        <div className="bg-gray-800 rounded p-3 text-sm text-gray-300">
          Импортировано {result.tracks} треков из {result.source}. Загрузка запущена — перейди в Queue.
        </div>
      )}
    </div>
  )
}
