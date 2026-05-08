export default function Hero() {
  return (
    <div className="rounded-2xl p-8 mb-8 text-center bg-gradient-to-br from-white via-brand-50/40 to-white dark:from-slate-900 dark:via-indigo-950/40 dark:to-slate-900 border border-slate-200 dark:border-slate-800 shadow-soft">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-500/10 border border-brand-200 dark:border-brand-500/30 text-brand-700 dark:text-brand-300 text-xs font-medium mb-4">
        <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse" />
        Powered by Claude
      </div>
      <h1 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-3 tracking-tight">
        AI-Powered Career Fit Analysis
      </h1>
      <p className="text-slate-600 dark:text-slate-400 text-base max-w-2xl mx-auto">
        Paste your resume and a job description to get an instant AI-driven fit score,
        skill gap analysis, optimized resume, and personalized cover letter.
      </p>
    </div>
  )
}
