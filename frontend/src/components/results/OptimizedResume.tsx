import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { downloadResumePdf, parseResumeText } from '../../api/client'
import ResumePreview from '../../resume/ResumePreview'
import ResumeSections from '../../resume/ResumeSections'
import { structuredToMarkdown } from '../../resume/serialize'
import type { StructuredResume } from '../../types'

interface Props {
  markdown: string
}

type View = 'split' | 'markdown'

const EMPTY: StructuredResume = {
  personal: { name: '', title: '', email: '', phone: '', location: '', portfolio: '', linkedin: '', github: '', summary: '' },
  skills: [],
  education: [],
  experience: [],
  projects: [],
  custom: [],
}

export default function OptimizedResume({ markdown }: Props) {
  const [view, setView] = useState<View>('split')
  const [draftMd, setDraftMd] = useState(markdown)
  const [structured, setStructured] = useState<StructuredResume | null>(null)
  const [parsing, setParsing] = useState(true)
  const [parseError, setParseError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    let cancelled = false
    setParsing(true)
    setParseError(null)
    parseResumeText(markdown)
      .then(s => {
        if (cancelled) return
        setStructured(s)
        setDraftMd(markdown)
      })
      .catch(() => {
        if (cancelled) return
        setParseError('Could not split this resume into editable sections — switch to Markdown to edit raw.')
        setStructured(EMPTY)
      })
      .finally(() => {
        if (!cancelled) setParsing(false)
      })
    return () => {
      cancelled = true
    }
  }, [markdown])

  function handleStructuredChange(next: StructuredResume) {
    setStructured(next)
    setDraftMd(structuredToMarkdown(next))
  }

  async function handleDownload() {
    setDownloading(true)
    try {
      const md = view === 'split' && structured ? structuredToMarkdown(structured) : draftMd
      await downloadResumePdf(md)
    } catch {
      alert('Failed to generate PDF.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex gap-1 p-1 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-soft">
          <ViewBtn active={view === 'split'} onClick={() => setView('split')}>Editor + Preview</ViewBtn>
          <ViewBtn active={view === 'markdown'} onClick={() => setView('markdown')}>Markdown</ViewBtn>
        </div>

        <button
          onClick={handleDownload}
          disabled={downloading}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
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

      {parseError && (
        <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 text-amber-700 dark:text-amber-400 text-xs">
          {parseError}
        </div>
      )}

      {view === 'split' ? (
        parsing ? (
          <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-12 text-center text-slate-500 dark:text-slate-400 text-sm shadow-soft">
            <span className="inline-flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-slate-200 dark:border-slate-700 border-t-brand-500 dark:border-t-brand-400 rounded-full animate-spin" />
              Splitting into editable sections…
            </span>
          </div>
        ) : (
          <div className="grid lg:grid-cols-2 gap-6 items-start">
            <div className="space-y-3">
              <ResumeSections value={structured ?? EMPTY} onChange={handleStructuredChange} />
            </div>
            <div className="lg:sticky lg:top-20">
              <ResumePreview resume={structured ?? EMPTY} />
              <div className="mt-2 flex items-center gap-2 justify-end">
                <span className="text-xs text-slate-500 dark:text-slate-500">Live preview</span>
              </div>
            </div>
          </div>
        )
      ) : (
        <div className="grid lg:grid-cols-2 gap-6">
          <textarea
            value={draftMd}
            onChange={e => setDraftMd(e.target.value)}
            rows={30}
            className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-700 dark:text-slate-300 font-mono leading-relaxed focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none shadow-soft"
          />
          <div className="p-6 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 prose dark:prose-invert prose-sm max-w-none overflow-y-auto max-h-[calc(100vh-200px)] shadow-soft">
            <ReactMarkdown>{draftMd}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}

function ViewBtn({
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
        active
          ? 'bg-brand-600 dark:bg-brand-500 text-white shadow'
          : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
      }`}
    >
      {children}
    </button>
  )
}
