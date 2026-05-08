import { useEffect, useState } from 'react'
import { getConfig, saveConfig } from '../api/client'
import type { LLMConfig, LLMProvider } from '../types'

const ANTHROPIC_MODELS = [
  { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6 (recommended)' },
  { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5 (faster)' },
  { value: 'claude-opus-4-7', label: 'Claude Opus 4.7 (most powerful)' },
]

export default function LLMSettings() {
  const [open, setOpen] = useState(false)
  const [provider, setProvider] = useState<LLMProvider>('ollama')
  const [apiKey, setApiKey] = useState('')
  const [modelName, setModelName] = useState('claude-sonnet-4-6')
  const [ollamaModel, setOllamaModel] = useState('llama3.2')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showKey, setShowKey] = useState(false)

  useEffect(() => {
    getConfig()
      .then(cfg => {
        setProvider(cfg.provider as LLMProvider)
        if (cfg.provider === 'anthropic') {
          setModelName(cfg.model_name || 'claude-sonnet-4-6')
        } else {
          setOllamaModel(cfg.model_name || 'llama3.2')
        }
      })
      .catch(() => {})
  }, [])

  async function handleSave() {
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      const config: LLMConfig = {
        provider,
        api_key: provider === 'anthropic' ? apiKey : '',
        model_name: provider === 'anthropic' ? modelName : ollamaModel,
      }
      await saveConfig(config)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null
      setError(msg || 'Failed to save settings.')
    } finally {
      setSaving(false)
    }
  }

  const inputCls =
    'w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-colors bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500'

  return (
    <div className="mb-6">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-lg border bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/70 transition-colors shadow-soft"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        AI Provider
        <span className={`ml-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
          provider === 'anthropic'
            ? 'bg-orange-100 dark:bg-orange-500/20 text-orange-700 dark:text-orange-400'
            : 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400'
        }`}>
          {provider === 'anthropic' ? 'Claude API' : 'Local Ollama'}
        </span>
        <svg
          className={`w-4 h-4 ml-auto transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="mt-2 p-5 rounded-2xl border bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 space-y-4 shadow-soft">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider mb-2 text-slate-500 dark:text-slate-400">
              Provider
            </p>
            <div className="flex gap-2">
              {([
                { value: 'ollama', label: 'Local (Ollama)', icon: '⚡' },
                { value: 'anthropic', label: 'Claude API', icon: '✦' },
              ] as const).map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setProvider(opt.value)}
                  className={`flex-1 py-2 px-3 rounded-lg border text-sm font-medium transition-all ${
                    provider === opt.value
                      ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/10 text-brand-700 dark:text-brand-300'
                      : 'border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-slate-400 dark:hover:border-slate-500'
                  }`}
                >
                  {opt.icon} {opt.label}
                </button>
              ))}
            </div>
          </div>

          {provider === 'ollama' && (
            <div>
              <label className="block text-xs font-medium mb-1 text-slate-500 dark:text-slate-400">
                Ollama Model
              </label>
              <input
                type="text"
                value={ollamaModel}
                onChange={e => setOllamaModel(e.target.value)}
                placeholder="llama3.2"
                className={inputCls}
              />
              <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                Make sure Ollama is running at localhost:11434
              </p>
            </div>
          )}

          {provider === 'anthropic' && (
            <>
              <div>
                <label className="block text-xs font-medium mb-1 text-slate-500 dark:text-slate-400">
                  Model
                </label>
                <select
                  value={modelName}
                  onChange={e => setModelName(e.target.value)}
                  className={inputCls}
                >
                  {ANTHROPIC_MODELS.map(m => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium mb-1 text-slate-500 dark:text-slate-400">
                  Anthropic API Key
                </label>
                <div className="relative">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={e => setApiKey(e.target.value)}
                    placeholder="sk-ant-..."
                    className={`${inputCls} pr-12`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(v => !v)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                  >
                    {showKey ? 'Hide' : 'Show'}
                  </button>
                </div>
                <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                  Your key is sent only to your local backend server and never stored on disk.
                </p>
              </div>
            </>
          )}

          {error && (
            <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
          )}

          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full py-2 rounded-lg font-semibold text-sm text-white bg-brand-600 hover:bg-brand-700 dark:bg-brand-500 dark:hover:bg-brand-600 disabled:opacity-50 transition-all"
          >
            {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save Settings'}
          </button>
        </div>
      )}
    </div>
  )
}
