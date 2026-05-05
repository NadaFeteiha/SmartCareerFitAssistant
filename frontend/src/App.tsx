import { useState } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import Hero from './components/Hero'
import InputPanel from './components/InputPanel'
import LLMSettings from './components/LLMSettings'
import ResultsTabs from './components/results/ResultsTabs'
import { analyze } from './api/client'
import type { FullAnalysis, Theme, UserProfile } from './types'

const DEFAULT_PROFILE: UserProfile = {
  jobTitle: '',
  targetRoles: '',
  tone: 'professional',
  strengths: '',
  goals: '',
}

export default function App() {
  const [theme, setTheme] = useState<Theme>('dark')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE)
  const [resumeText, setResumeText] = useState('')
  const [jobText, setJobText] = useState('')
  const [result, setResult] = useState<FullAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isDark = theme === 'dark'

  async function handleAnalyze() {
    if (!resumeText.trim() || !jobText.trim()) {
      setError('Please provide both a resume and a job description.')
      return
    }
    setError(null)
    setLoading(true)
    setResult(null)
    try {
      const data = await analyze(resumeText, jobText)
      setResult(data)
    } catch (err) {
      setError('Analysis failed. Make sure the backend server is running.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={isDark ? 'dark' : ''}>
      <div className="min-h-screen bg-slate-950 dark:bg-slate-950 text-slate-100 transition-colors duration-200">
        <Header
          theme={theme}
          onToggleTheme={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))}
          onToggleSidebar={() => setSidebarOpen(o => !o)}
        />

        <div className="flex">
          <Sidebar
            open={sidebarOpen}
            profile={profile}
            onChange={setProfile}
            isDark={isDark}
          />

          <main className="flex-1 px-4 py-8 max-w-5xl mx-auto w-full">
            <Hero />

            <LLMSettings isDark={isDark} />

            <InputPanel
              resumeText={resumeText}
              jobText={jobText}
              onResumeChange={setResumeText}
              onJobChange={setJobText}
              isDark={isDark}
            />

            {error && (
              <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                {error}
              </div>
            )}

            <div className="mt-6 flex justify-center">
              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="px-8 py-3 rounded-xl font-semibold text-white bg-brand-500 hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-brand-500/30 text-base"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Analyzing...
                  </span>
                ) : (
                  'Analyze Fit'
                )}
              </button>
            </div>

            {loading && (
              <div className="mt-8 text-center text-slate-400 text-sm animate-pulse">
                Running 7-agent AI pipeline... this may take a minute.
              </div>
            )}

            {result && (
              <div className="mt-10">
                <ResultsTabs result={result} />
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  )
}
