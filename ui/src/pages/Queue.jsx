import { useState, useEffect, useRef } from 'react'
import TrackRow from '../components/TrackRow'
import SourcePicker from '../components/SourcePicker'

export default function Queue() {
  const [jobs, setJobs] = useState({})
  const [picker, setPicker] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    loadJobs()
    const ws = new WebSocket(`ws://${window.location.host}/api/downloads/ws`)
    wsRef.current = ws
    ws.onmessage = e => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'update') {
        setJobs(prev => {
          const job = prev[msg.job_id]
          if (!job) return prev
          return {
            ...prev,
            [msg.job_id]: {
              ...job,
              tracks: job.tracks.map(t => t.id === msg.track.id ? msg.track : t),
            },
          }
        })
      }
    }
    return () => ws.close()
  }, [])

  async function loadJobs() {
    const list = await fetch('/api/downloads/jobs').then(r => r.json()).catch(() => [])
    const full = await Promise.all(
      list.map(j => fetch(`/api/downloads/jobs/${j.id}`).then(r => r.json()))
    )
    const map = {}
    full.forEach(j => { map[j.id] = j })
    setJobs(map)
  }

  async function handleRetry(jobId, trackId, url) {
    await fetch(`/api/downloads/jobs/${jobId}/tracks/${trackId}/retry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    })
    setPicker(null)
  }

  const jobList = Object.values(jobs)

  if (jobList.length === 0) {
    return <div className="text-gray-500 text-sm">Загрузок нет. Импортируй плейлист.</div>
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-lg font-bold mb-4">Queue</h1>
      {jobList.map(job => (
        <div key={job.id} className="mb-8">
          <div className="flex justify-between items-center mb-2 text-sm">
            <span className="font-medium">{job.name}</span>
            <span className="text-gray-500">
              {(job.tracks || []).filter(t => t.status === 'done').length} / {(job.tracks || []).length}
            </span>
          </div>
          <div className="space-y-1">
            {(job.tracks || []).map(track => (
              <TrackRow
                key={track.id}
                track={track}
                onFindAlternative={() => setPicker({ jobId: job.id, trackId: track.id })}
              />
            ))}
          </div>
        </div>
      ))}
      {picker && (
        <SourcePicker
          jobId={picker.jobId}
          trackId={picker.trackId}
          onSelect={url => handleRetry(picker.jobId, picker.trackId, url)}
          onClose={() => setPicker(null)}
        />
      )}
    </div>
  )
}
