import type { FitScore, SkillGapReport } from '../../types'

interface Props {
  fitScore: FitScore
  skillGaps: SkillGapReport
}

const cardCls = 'p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-soft'
const labelCls = 'text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3'
const tinyLabelCls = 'text-xs text-slate-500 dark:text-slate-500 uppercase tracking-wider mb-2'

export default function FitAnalysis({ fitScore, skillGaps }: Props) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <ScoreCard label="Overall Fit" value={fitScore.overall} max={100} accent />
        <ScoreCard label="Skill Match" value={fitScore.skill_match} max={40} />
        <ScoreCard label="Experience" value={fitScore.experience_alignment} max={30} />
        <ScoreCard label="Keywords" value={fitScore.keyword_coverage} max={30} />
      </div>

      <div className={cardCls}>
        <h4 className={labelCls}>Analysis Summary</h4>
        <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">{fitScore.explanation}</p>
      </div>

      {fitScore.strengths.length > 0 && (
        <div className={cardCls}>
          <h4 className={labelCls}>Strengths</h4>
          <div className="flex flex-wrap gap-2">
            {fitScore.strengths.map(s => (
              <Chip key={s} color="green">{s}</Chip>
            ))}
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-4">
        {skillGaps.missing_hard_skills.length > 0 && (
          <div className={cardCls}>
            <h4 className={labelCls}>Missing Hard Skills</h4>
            <div className="flex flex-wrap gap-2">
              {skillGaps.missing_hard_skills.map(s => (
                <Chip key={s} color="red">{s}</Chip>
              ))}
            </div>
          </div>
        )}
        {skillGaps.missing_soft_skills.length > 0 && (
          <div className={cardCls}>
            <h4 className={labelCls}>Missing Soft Skills</h4>
            <div className="flex flex-wrap gap-2">
              {skillGaps.missing_soft_skills.map(s => (
                <Chip key={s} color="amber">{s}</Chip>
              ))}
            </div>
          </div>
        )}
      </div>

      {(skillGaps.missing_requirements.missing_experience.length > 0 ||
        skillGaps.missing_requirements.missing_keywords.length > 0) && (
        <div className={`${cardCls} space-y-3`}>
          <h4 className={labelCls}>Additional Gaps</h4>
          {skillGaps.missing_requirements.missing_experience.length > 0 && (
            <div>
              <p className={tinyLabelCls}>Experience Gaps</p>
              <ul className="space-y-1">
                {skillGaps.missing_requirements.missing_experience.map(e => (
                  <li key={e} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                    <span className="text-amber-500 dark:text-amber-400 mt-0.5">•</span> {e}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {skillGaps.missing_requirements.missing_keywords.length > 0 && (
            <div>
              <p className={tinyLabelCls}>Missing Keywords</p>
              <div className="flex flex-wrap gap-2">
                {skillGaps.missing_requirements.missing_keywords.map(k => (
                  <Chip key={k} color="slate">{k}</Chip>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ScoreCard({
  label,
  value,
  max,
  accent = false,
}: {
  label: string
  value: number
  max: number
  accent?: boolean
}) {
  const pct = Math.round((value / max) * 100)
  const tone =
    pct >= 70 ? 'text-emerald-600 dark:text-emerald-400'
    : pct >= 40 ? 'text-amber-600 dark:text-amber-400'
    : 'text-red-600 dark:text-red-400'
  const bar =
    accent ? 'bg-brand-600 dark:bg-brand-500'
    : pct >= 70 ? 'bg-emerald-500'
    : pct >= 40 ? 'bg-amber-500'
    : 'bg-red-500'

  return (
    <div
      className={`p-4 rounded-xl border shadow-soft ${
        accent
          ? 'bg-brand-50 dark:bg-brand-500/10 border-brand-200 dark:border-brand-500/30'
          : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800'
      }`}
    >
      <p className="text-xs text-slate-500 dark:text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-bold ${accent ? 'text-brand-700 dark:text-brand-300' : tone}`}>
        {value}
        <span className="text-xs font-normal text-slate-500 dark:text-slate-500 ml-1">/ {max}</span>
      </p>
      <div className="mt-2 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${bar}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

type ChipColor = 'green' | 'red' | 'amber' | 'slate'

function Chip({ color, children }: { color: ChipColor; children: React.ReactNode }) {
  const cls: Record<ChipColor, string> = {
    green: 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20',
    red:   'bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/20',
    amber: 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/20',
    slate: 'bg-slate-100 dark:bg-slate-700/50 text-slate-700 dark:text-slate-400 border-slate-200 dark:border-slate-700',
  }
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${cls[color]}`}>
      {children}
    </span>
  )
}
