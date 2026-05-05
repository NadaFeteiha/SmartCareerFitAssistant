import { useState } from 'react'
import { downloadCoverLetterPdf } from '../../api/client'

interface Props {
  text: string
}

export default function CoverLetter({ text }: Props) {
  const [draft, setDraft] = useState(text)
  const [downloading, setDownloading] = useState(false)

  async function handleDownload() {
    setDownloading(true)
    try {
      await downloadCoverLetterPdf(draft)
    } catch {
      alert('Failed to generate PDF.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
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

      <textarea
        value={draft}
        onChange={e => setDraft(e.target.value)}
        rows={22}
        className="w-full bg-slate-900 border border-slate-700 rounded-xl px-5 py-4 text-sm text-slate-300 leading-relaxed focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none"
      />
    </div>
  )
}
