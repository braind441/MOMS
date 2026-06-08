import { useState } from 'react'
import Import from './pages/Import'
import Queue from './pages/Queue'
import Library from './pages/Library'
import Upload from './pages/Upload'

const TABS = ['Import', 'Queue', 'Library', 'Upload']

export default function App() {
  const [tab, setTab] = useState('Import')

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <nav className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center gap-4">
        <span className="font-bold text-white mr-2">MOMS</span>
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1 rounded text-sm ${
              tab === t ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-700'
            }`}
          >
            {t}
          </button>
        ))}
      </nav>
      <main className="p-6">
        {tab === 'Import' && <Import />}
        {tab === 'Queue' && <Queue />}
        {tab === 'Library' && <Library />}
        {tab === 'Upload' && <Upload />}
      </main>
    </div>
  )
}
