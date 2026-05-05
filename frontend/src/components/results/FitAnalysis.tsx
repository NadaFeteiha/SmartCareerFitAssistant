import type { FitScore, SkillGapReport } from '../../types'

interface Props {
  fitScore: FitScore
  skillGaps: SkillGapReport
}

export default function FitAnalysis({ fitScore, skillGaps }: Props) {
  return (
    <div className="space-y-6">
      {/* Score cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <ScoreCard label="Overall Fit" value={fitScore.overall} max={100} accent />
        <ScoreCard label="Skill Match" value={fitScore.skill_match} max={40} />
        <ScoreCard label="Experience" value={fitScore.experience_alignment} max={30} />
        <ScoreCard label="Keywords" value={fitScore.keyword_coverage} max={30} />
      </div>

      {/* Explanation */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
        <h4 className="text-sm font-semibold text-slate-300 mb-2">Analysis Summary</h4>
        <p className="text-slate-400 text-sm leading-relaxed">{fitScore.explanation}</p>
      </div>

      {/* Strengths */}
      {fitScore.strengths.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h4 className="text-sm font-semibold text-slate-300 mb-3">Strengths</h4>
          <div className="flex flex-wrap gap-2">
            {fitScore.strengths.map(s => (
              <Chip key={s} color="green">{s}</Chip>
            ))}
          </div>
        </div>
      )}

      {/* Missing skills */}
      <div className="grid md:grid-cols-2 gap-4">
        {skillGaps.missing_hard_skills.length > 0 && (
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <h4 className="text-sm font-semibold text-slate-300 mb-3">Missing Hard Skills</h4>
            <div className="flex flex-wrap gap-2">
              {skillGaps.missing_hard_skills.map(s => (
                <Chip key={s} color="red">{s}</Chip>
              ))}
            </div>
          </div>
        )}
        {skillGaps.missing_soft_skills.length > 0 && (
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <h4 className="text-sm font-semibold text-slate-300 mb-3">Missing Soft Skills</h4>
            <div className="flex flex-wrap gap-2">
              {skillGaps.missing_soft_skills.map(s => (
                <Chip key={s} color="amber">{s}</Chip>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Missing requirements breakdown */}
      {(skillGaps.missing_requirements.missing_experience.length > 0 ||
        skillGaps.missing_requirements.missing_keywords.length > 0) && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <h4 className="text-sm font-semibold text-slate-300">Additional Gaps</h4>
          {skillGaps.missing_requirements.missing_experience.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Experience Gaps</p>
              <ul className="space-y-1">
                {skillGaps.missing_requirements.missing_experience.map(e => (
                  <li key={e} className="text-sm text-slate-400 flex items-start gap-2">
                    <span className="text-amber-500 mt-0.5">•</span> {e}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {skillGaps.missing_requirements.missing_keywords.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Missing Keywords</p>
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
  const color = pct >= 70 ? 'text-green-400' : pct >= 40 ? 'text-amber-400' : 'text-red-400'

  return (
    <div className={`p-4 rounded-xl border ${accent ? 'bg-brand-500/10 border-brand-500/30' : 'bg-slate-900 border-slate-800'}`}>
      <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-bold ${accent ? 'text-brand-400' : color}`}>
        {value}
        <span className="text-xs font-normal text-slate-500 ml-1">/ {max}</span>
      </p>
      <div className="mt-2 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${accent ? 'bg-brand-500' : pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-amber-500' : 'bg-red-500'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

type ChipColor = 'green' | 'red' | 'amber' | 'slate'

function Chip({ color, children }: { color: ChipColor; children: React.ReactNode }) {
  const cls: Record<ChipColor, string> = {
    green: 'bg-green-500/10 text-green-400 border-green-500/20',
    red:   'bg-red-500/10 text-red-400 border-red-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    slate: 'bg-slate-700/50 text-slate-400 border-slate-700',
  }
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${cls[color]}`}>
      {children}
    </span>
  )
}
