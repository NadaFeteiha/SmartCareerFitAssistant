import { useState } from 'react'
import Header from './components/Header'
import Hero from './components/Hero'
import LLMSettings from './components/LLMSettings'
import ResultsTabs from './components/results/ResultsTabs'
import MissingSkillsAssistant from './components/MissingSkillsAssistant'
import { analyze } from './api/client'
import { AuthProvider, useAuth } from './auth/AuthContext'
import AuthScreen from './auth/AuthScreen'
import SavedResumePanel from './resume/SavedResumePanel'
import { ThemeProvider } from './theme/ThemeContext'
import type { FullAnalysis } from './types'

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    </ThemeProvider>
  )
}

function AppShell() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400 text-sm">
          <span className="w-4 h-4 border-2 border-slate-300 dark:border-slate-700 border-t-brand-500 dark:border-t-brand-400 rounded-full animate-spin" />
          Loading…
        </div>
      </div>
    )
  }

  if (!user) {
    return <AuthScreen />
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      <Header />
      <Main />
    </div>
  )
}

function Main() {
  const [resumeReady, setResumeReady] = useState(false)
  const [jobText, setJobText] = useState('')
  const [result, setResult] = useState<FullAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [refreshingAfterSkill, setRefreshingAfterSkill] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleAnalyze() {
    if (!resumeReady) {
      setError('Build or import your resume first.')
      return
    }
    if (!jobText.trim()) {
      setError('Please provide a job description.')
      return
    }
    setError(null)
    setLoading(true)
    setResult(null)
    try {
      const data = await analyze(jobText)
      setResult(data)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(detail || 'Analysis failed. Make sure the backend server is running.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSkillAnswered() {
    if (!jobText.trim()) return
    setRefreshingAfterSkill(true)
    setError(null)
    try {
      const data = await analyze(jobText)
      setResult(data)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(detail || 'Could not refresh analysis after your skill confirmation.')
    } finally {
      setRefreshingAfterSkill(false)
    }
  }

  return (
    <main className="px-4 py-8 max-w-6xl mx-auto w-full">
      <Hero />

      <LLMSettings />

      <div className="grid lg:grid-cols-2 gap-6">
        <SavedResumePanel onResumeReadyChange={setResumeReady} jobText={jobText} />

        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Job Description</h2>
          <textarea
            value={jobText}
            onChange={e => setJobText(e.target.value)}
            placeholder="Paste the job description here..."
            rows={20}
            className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl px-4 py-3 text-sm text-slate-700 dark:text-slate-300 placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none font-mono leading-relaxed shadow-soft"
          />
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="mt-6 flex justify-center">
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="px-8 py-3 rounded-xl font-semibold text-white bg-brand-600 hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-brand-500/30 text-base"
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

      {(loading || refreshingAfterSkill) && (
        <div className="mt-8 text-center text-slate-500 dark:text-slate-400 text-sm animate-pulse">
          {refreshingAfterSkill
            ? 'Updating fit score with your confirmed skills...'
            : 'Running 7-agent AI pipeline... this may take a minute.'}
        </div>
      )}

      {result && (
        <div className="mt-10">
          <ResultsTabs result={result} />
          <MissingSkillsAssistant result={result} onSkillAnswered={handleSkillAnswered} />
        </div>
      )}
    </main>
  )
}
