import type { LearningItem } from '../../types'

interface Props {
  items: LearningItem[]
}

export default function LearningRoadmap({ items }: Props) {
  if (items.length === 0) {
    return (
      <p className="text-slate-500 dark:text-slate-500 text-sm text-center py-10">No learning items generated.</p>
    )
  }

  const sorted = [...items].sort((a, b) => priorityOrder(a.priority) - priorityOrder(b.priority))

  return (
    <div className="space-y-4">
      {sorted.map((item, i) => (
        <div key={i} className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 shadow-soft">
          <div className="flex items-center gap-3">
            <PriorityBadge priority={item.priority} />
            <h4 className="font-semibold text-slate-900 dark:text-slate-200 text-sm">{item.skill}</h4>
          </div>
          <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">{item.reason}</p>
          <div className="flex items-start gap-2 mt-1 pt-3 border-t border-slate-200 dark:border-slate-800">
            <svg className="w-4 h-4 text-brand-600 dark:text-brand-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <p className="text-slate-600 dark:text-slate-400 text-sm">{item.suggestion}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

function priorityOrder(p: LearningItem['priority']): number {
  return p === 'high' ? 0 : p === 'medium' ? 1 : 2
}

function PriorityBadge({ priority }: { priority: LearningItem['priority'] }) {
  const cls = {
    high:   'bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/20',
    medium: 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/20',
    low:    'bg-slate-100 dark:bg-slate-700/50 text-slate-700 dark:text-slate-400 border-slate-200 dark:border-slate-700',
  }[priority]

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border uppercase tracking-wide ${cls}`}>
      {priority}
    </span>
  )
}
