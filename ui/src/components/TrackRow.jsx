const STATUS = {
  pending:     { label: 'pending',       color: 'text-gray-400' },
  downloading: { label: 'downloading',  color: 'text-yellow-400' },
  done:        { label: 'done',          color: 'text-green-400' },
  unavailable: { label: 'unavailable',  color: 'text-orange-400' },
  not_found:   { label: 'not found',    color: 'text-red-400' },
}

export default function TrackRow({ track, onFindAlternative }) {
  const s = STATUS[track.status] || STATUS.pending
  const canRetry = track.status === 'unavailable' || track.status === 'not_found'

  return (
    <div className="bg-gray-800 rounded px-3 py-2 text-sm flex justify-between items-center gap-2">
      <span className="truncate flex-1">{track.artist} — {track.title}</span>
      <div className="flex items-center gap-2 flex-shrink-0">
        {track.source && track.source !== 'library' && <span className="text-gray-500 text-xs">{track.source}</span>}
        {track.source === 'library' && <span className="text-gray-500 text-xs">из библиотеки</span>}
        <span className={s.color}>{s.label}</span>
        {canRetry && (
          <button
            onClick={onFindAlternative}
            className="text-xs text-blue-400 hover:text-blue-300 underline"
          >
            найти
          </button>
        )}
      </div>
    </div>
  )
}
