import { useRef, useState } from 'react'
import { uploadPdf } from '../api/client'

interface Props {
  resumeText: string
  jobText: string
  onResumeChange: (v: string) => void
  onJobChange: (v: string) => void
  isDark: boolean
}

export default function InputPanel({ resumeText, jobText, onResumeChange, onJobChange, isDark: _isDark }: Props) {
  const [uploadMode, setUploadMode] = useState<'paste' | 'upload'>('paste')
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const text = await uploadPdf(file)
      onResumeChange(text)
    } catch {
      alert('Failed to extract PDF text. Try pasting instead.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="grid md:grid-cols-2 gap-5">
      {/* Resume Input */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-slate-200 text-sm">Resume</h3>
          <div className="flex gap-1 p-1 bg-slate-800 rounded-lg">
            <TabBtn active={uploadMode === 'paste'} onClick={() => setUploadMode('paste')}>
              Paste
            </TabBtn>
            <TabBtn active={uploadMode === 'upload'} onClick={() => setUploadMode('upload')}>
              PDF Upload
            </TabBtn>
          </div>
        </div>

        {uploadMode === 'paste' ? (
          <textarea
            value={resumeText}
            onChange={e => onResumeChange(e.target.value)}
            placeholder="Paste your resume here..."
            rows={14}
            className={textareaCls}
          />
        ) : (
          <div className="space-y-3">
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="w-full h-24 border-2 border-dashed border-slate-700 rounded-xl text-slate-400 hover:border-brand-500 hover:text-brand-400 transition-colors text-sm flex flex-col items-center justify-center gap-1"
            >
              {uploading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-slate-500 border-t-brand-400 rounded-full animate-spin" />
                  Extracting text...
                </span>
              ) : (
                <>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Click to upload PDF
                </>
              )}
            </button>
            <input ref={fileRef} type="file" accept=".pdf" onChange={handleFile} className="hidden" />
            {resumeText && (
              <textarea
                value={resumeText}
                onChange={e => onResumeChange(e.target.value)}
                placeholder="Extracted text will appear here..."
                rows={10}
                className={textareaCls}
              />
            )}
          </div>
        )}
      </div>

      {/* Job Description Input */}
      <div className="space-y-3">
        <h3 className="font-semibold text-slate-200 text-sm">Job Description</h3>
        <textarea
          value={jobText}
          onChange={e => onJobChange(e.target.value)}
          placeholder="Paste the job description here..."
          rows={14}
          className={textareaCls}
        />
      </div>
    </div>
  )
}

const textareaCls =
  'w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none font-mono leading-relaxed'

function TabBtn({
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
      className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
        active ? 'bg-brand-500 text-white' : 'text-slate-400 hover:text-slate-200'
      }`}
    >
      {children}
    </button>
  )
}
