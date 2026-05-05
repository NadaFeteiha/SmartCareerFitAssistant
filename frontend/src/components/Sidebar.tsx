import type { UserProfile } from '../types'

interface Props {
  open: boolean
  profile: UserProfile
  onChange: (p: UserProfile) => void
  isDark: boolean
}

export default function Sidebar({ open, profile, onChange, isDark: _isDark }: Props) {
  function set(key: keyof UserProfile, value: string) {
    onChange({ ...profile, [key]: value })
  }

  return (
    <aside
      className={`
        transition-all duration-300 overflow-hidden shrink-0
        ${open ? 'w-72' : 'w-0'}
        bg-slate-900 border-r border-slate-800 min-h-screen
      `}
    >
      <div className="w-72 p-5 space-y-5">
        <h2 className="font-semibold text-slate-200 text-sm uppercase tracking-widest mb-4">
          Your Profile
        </h2>

        <Field label="Current Job Title">
          <input
            type="text"
            value={profile.jobTitle}
            onChange={e => set('jobTitle', e.target.value)}
            placeholder="e.g. Software Engineer"
            className={inputCls}
          />
        </Field>

        <Field label="Target Roles">
          <input
            type="text"
            value={profile.targetRoles}
            onChange={e => set('targetRoles', e.target.value)}
            placeholder="e.g. Senior Engineer, Tech Lead"
            className={inputCls}
          />
        </Field>

        <Field label="Cover Letter Tone">
          <select
            value={profile.tone}
            onChange={e => set('tone', e.target.value)}
            className={inputCls}
          >
            <option value="professional">Professional</option>
            <option value="enthusiastic">Enthusiastic</option>
            <option value="concise">Concise</option>
            <option value="storytelling">Storytelling</option>
          </select>
        </Field>

        <Field label="Key Strengths">
          <textarea
            value={profile.strengths}
            onChange={e => set('strengths', e.target.value)}
            placeholder="e.g. problem-solving, leadership"
            rows={2}
            className={`${inputCls} resize-none`}
          />
        </Field>

        <Field label="Career Goals">
          <textarea
            value={profile.goals}
            onChange={e => set('goals', e.target.value)}
            placeholder="e.g. move into ML engineering"
            rows={2}
            className={`${inputCls} resize-none`}
          />
        </Field>
      </div>
    </aside>
  )
}

const inputCls =
  'w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</label>
      {children}
    </div>
  )
}
