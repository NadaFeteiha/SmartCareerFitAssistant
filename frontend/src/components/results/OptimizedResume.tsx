import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { downloadResumePdf } from '../../api/client'

interface Props {
  markdown: string
}

export default function OptimizedResume({ markdown }: Props) {
  const [draft, setDraft] = useState(markdown)
  const [mode, setMode] = useState<'preview' | 'edit'>('preview')
  const [downloading, setDownloading] = useState(false)

  async function handleDownload() {
    setDownloading(true)
    try {
      await downloadResumePdf(draft)
    } catch {
      alert('Failed to generate PDF.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-1 p-1 bg-slate-900 rounded-lg border border-slate-800">
          <ModeBtn active={mode === 'preview'} onClick={() => setMode('preview')}>Preview</ModeBtn>
          <ModeBtn active={mode === 'edit'} onClick={() => setMode('edit')}>Edit</ModeBtn>
        </div>

        <button
          onClick={handleDownload}
          disabled={downloading}
          className="flex items-center gap-2 px-4 py-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {downloading ? (
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          )}
          Download PDF
        </button>
      </div>

      {mode === 'preview' ? (
        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{draft}</ReactMarkdown>
        </div>
      ) : (
        <textarea
          value={draft}
          onChange={e => setDraft(e.target.value)}
          rows={30}
          className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-300 font-mono leading-relaxed focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none"
        />
      )}
    </div>
  )
}

function ModeBtn({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
        active ? 'bg-brand-500 text-white' : 'text-slate-400 hover:text-slate-200'
      }`}
    >
      {children}
    </button>
  )
}
