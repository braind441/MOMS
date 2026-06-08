import { useState, useEffect, useRef, useCallback } from 'react'

function formatDuration(sec) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = String(Math.floor(sec % 60)).padStart(2, '0')
  return `${m}:${s}`
}

function formatSize(bytes) {
  if (!bytes) return ''
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function PlayIcon() {
  return (
    <svg viewBox="0 0 24 24" className="w-3 h-3 fill-current ml-0.5">
      <polygon points="5,3 19,12 5,21" />
    </svg>
  )
}

function PauseIcon() {
  return (
    <svg viewBox="0 0 24 24" className="w-3 h-3 fill-current">
      <rect x="5" y="3" width="4" height="18" />
      <rect x="15" y="3" width="4" height="18" />
    </svg>
  )
}

function ContextMenu({ onDelete, onClose }) {
  const ref = useRef(null)

  useEffect(() => {
    function handle(e) {
      if (ref.current && !ref.current.contains(e.target)) onClose()
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [onClose])

  return (
    <div
      ref={ref}
      className="absolute right-0 top-6 z-50 bg-gray-700 border border-gray-600 rounded shadow-lg py-1 min-w-32"
    >
      <button
        onClick={onDelete}
        className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-gray-600"
      >
        Удалить
      </button>
    </div>
  )
}

function TrackItem({ track, isPlaying, onPlay, onDelete }) {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="flex items-center px-3 py-2 border-b border-gray-700 last:border-0 hover:bg-gray-750 gap-2 group">
      {/* Play button */}
      <button
        onClick={onPlay}
        className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-600 hover:bg-blue-600 flex items-center justify-center text-white transition-colors"
      >
        {isPlaying ? <PauseIcon /> : <PlayIcon />}
      </button>

      {/* Track info */}
      <div className="flex-1 min-w-0">
        <div className={`text-sm truncate ${isPlaying ? 'text-blue-400' : 'text-gray-100'}`}>
          {track.title || track.filename}
        </div>
        {track.artist && (
          <div className="text-xs text-gray-500 truncate mt-0.5">{track.artist}</div>
        )}
      </div>

      {/* Meta + menu */}
      <div className="flex items-center gap-3 flex-shrink-0 text-xs text-gray-500">
        {track.quality && <span>{track.quality}</span>}
        {track.size > 0 && <span>{formatSize(track.size)}</span>}
        {track.duration > 0 && <span className="w-9 text-right">{formatDuration(track.duration)}</span>}

        {/* 3-dot menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(o => !o)}
            className="w-6 h-6 flex flex-col items-center justify-center gap-0.5 opacity-40 hover:opacity-100 transition-opacity"
          >
            <span className="w-1 h-1 rounded-full bg-gray-400" />
            <span className="w-1 h-1 rounded-full bg-gray-400" />
            <span className="w-1 h-1 rounded-full bg-gray-400" />
          </button>
          {menuOpen && (
            <ContextMenu
              onDelete={() => { setMenuOpen(false); onDelete() }}
              onClose={() => setMenuOpen(false)}
            />
          )}
        </div>
      </div>
    </div>
  )
}

function PlaylistGroup({ playlist, currentPath, onPlay, onDelete }) {
  const [open, setOpen] = useState(false)
  const totalDuration = playlist.tracks.reduce((s, t) => s + (t.duration || 0), 0)

  return (
    <div className="mb-2 bg-gray-800 rounded overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-750 text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-gray-400 text-sm w-4">{open ? '▾' : '▸'}</span>
          <span className="font-medium text-sm">{playlist.name}</span>
          <span className="text-gray-500 text-xs">{playlist.tracks.length} треков</span>
        </div>
        <span className="text-gray-500 text-xs">{formatDuration(totalDuration)}</span>
      </button>
      {open && (
        <div className="border-t border-gray-700">
          {playlist.tracks.map((t, i) => (
            <TrackItem
              key={i}
              track={t}
              isPlaying={currentPath === t.path}
              onPlay={() => onPlay(t)}
              onDelete={() => onDelete(t)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function Library() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [currentPath, setCurrentPath] = useState(null)
  const audioRef = useRef(null)

  const load = useCallback(() => {
    setLoading(true)
    fetch('/api/library/')
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  function handlePlay(track) {
    const audio = audioRef.current
    if (!audio) return

    if (currentPath === track.path) {
      audio.paused ? audio.play() : audio.pause()
      return
    }

    audio.src = `/api/library/stream?path=${encodeURIComponent(track.path)}`
    audio.play()
    setCurrentPath(track.path)
  }

  async function handleDelete(track) {
    if (!confirm(`Удалить «${track.title || track.filename}»?`)) return
    const res = await fetch(`/api/library/file?path=${encodeURIComponent(track.path)}`, { method: 'DELETE' })
    if (!res.ok) return
    if (currentPath === track.path) {
      audioRef.current?.pause()
      setCurrentPath(null)
    }
    // Удаляем трек из state без перезагрузки страницы
    setData(prev => {
      const playlists = prev.playlists.map(p => ({
        ...p,
        tracks: p.tracks.filter(t => t.path !== track.path),
      })).filter(p => p.tracks.length > 0)
      const ungrouped = prev.ungrouped.filter(t => t.path !== track.path)
      return { playlists, ungrouped }
    })
  }

  if (loading) return <div className="text-gray-500 text-sm">Loading...</div>
  if (!data) return <div className="text-gray-500 text-sm">Ошибка загрузки.</div>

  const total = (data.playlists || []).reduce((s, p) => s + p.tracks.length, 0)
    + (data.ungrouped || []).length

  return (
    <div className="max-w-2xl">
      <audio ref={audioRef} onEnded={() => setCurrentPath(null)} />

      <h1 className="text-lg font-bold mb-4">Library — {total} tracks</h1>

      {data.playlists.length === 0 && data.ungrouped.length === 0 && (
        <div className="text-gray-500 text-sm">Треков нет.</div>
      )}

      {data.playlists.map((p, i) => (
        <PlaylistGroup
          key={i}
          playlist={p}
          currentPath={currentPath}
          onPlay={handlePlay}
          onDelete={handleDelete}
        />
      ))}

      {data.ungrouped.length > 0 && (
        <PlaylistGroup
          playlist={{ name: 'Без плейлиста', tracks: data.ungrouped }}
          currentPath={currentPath}
          onPlay={handlePlay}
          onDelete={handleDelete}
        />
      )}
    </div>
  )
}
