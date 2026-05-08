import { useState } from 'react'
import FitAnalysis from './FitAnalysis'
import OptimizedResume from './OptimizedResume'
import CoverLetter from './CoverLetter'
import LearningRoadmap from './LearningRoadmap'
import type { FullAnalysis } from '../../types'

const TABS = ['Fit Analysis', 'Optimized Resume', 'Cover Letter', 'Learning Roadmap'] as const
type Tab = (typeof TABS)[number]

interface Props {
  result: FullAnalysis
}

export default function ResultsTabs({ result }: Props) {
  const [active, setActive] = useState<Tab>('Fit Analysis')

  return (
    <div>
      {/* Tab bar */}
      <div className="flex gap-1 p-1 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 mb-6 overflow-x-auto shadow-soft">
        {TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActive(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-150 ${
              active === tab
                ? 'bg-brand-600 dark:bg-brand-500 text-white shadow'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {active === 'Fit Analysis' && <FitAnalysis fitScore={result.fit_score} skillGaps={result.skill_gaps} />}
      {active === 'Optimized Resume' && <OptimizedResume markdown={result.optimized_resume} />}
      {active === 'Cover Letter' && <CoverLetter text={result.cover_letter} />}
      {active === 'Learning Roadmap' && <LearningRoadmap items={result.skill_gaps.learning_roadmap} />}
    </div>
  )
}
