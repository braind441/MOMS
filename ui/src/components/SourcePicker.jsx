import { useState, useEffect } from 'react'

function formatDuration(sec) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = String(sec % 60).padStart(2, '0')
  return `${m}:${s}`
}

export default function SourcePicker({ jobId, trackId, onSelect, onClose }) {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/downloads/jobs/${jobId}/tracks/${trackId}/search`)
      .then(r => r.json())
      .then(setResults)
      .catch(() => setResults([]))
      .finally(() => setLoading(false))
  }, [jobId, trackId])

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-4 max-w-lg w-full mx-4 max-h-[80vh] flex flex-col">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-medium text-sm">Найти в другом источнике</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-lg leading-none">×</button>
        </div>
        <div className="overflow-y-auto flex-1">
          {loading ? (
            <p className="text-gray-400 text-sm">Поиск...</p>
          ) : results.length === 0 ? (
            <p className="text-gray-400 text-sm">Ничего не найдено.</p>
          ) : (
            <div className="space-y-2">
              {results.map((r, i) => (
                <button
                  key={i}
                  onClick={() => onSelect(r.url)}
                  className="w-full text-left bg-gray-700 hover:bg-gray-600 rounded px-3 py-2 text-sm"
                >
                  <div className="flex justify-between gap-2">
                    <span className="truncate">{r.title}</span>
                    <div className="flex gap-2 text-gray-400 flex-shrink-0">
                      {r.duration && <span>{formatDuration(r.duration)}</span>}
                      <span>{r.source}</span>
                    </div>
                  </div>
                  {r.uploader && <div className="text-gray-400 text-xs mt-0.5">{r.uploader}</div>}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
