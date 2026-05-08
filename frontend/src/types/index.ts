export interface FitScore {
  overall: number
  skill_match: number
  experience_alignment: number
  keyword_coverage: number
  strengths: string[]
  explanation: string
}

export interface LearningItem {
  skill: string
  priority: 'high' | 'medium' | 'low'
  reason: string
  suggestion: string
}

export interface MissingRequirements {
  missing_skills: string[]
  missing_experience: string[]
  missing_keywords: string[]
}

export interface SkillGapReport {
  missing_hard_skills: string[]
  missing_soft_skills: string[]
  missing_requirements: MissingRequirements
  learning_roadmap: LearningItem[]
}

export interface FullAnalysis {
  fit_score: FitScore
  skill_gaps: SkillGapReport
  optimized_resume: string
  cover_letter: string
}

export type Theme = 'dark' | 'light'

export type LLMProvider = 'ollama' | 'anthropic'

export interface LLMConfig {
  provider: LLMProvider
  api_key: string
  model_name: string
}

export interface AuthUser {
  id: number
  email: string
}

export type SkillConfirmations = Record<string, boolean>

export interface UserProfile {
  phone: string
  linkedin: string
  github: string
}

export interface AuthResponse {
  token: string
  user: AuthUser
}

// ── Structured resume ────────────────────────────────────────────────────────

export interface PersonalInfo {
  name: string
  title: string
  email: string
  phone: string
  location: string
  portfolio: string
  linkedin: string
  github: string
  summary: string
}

export interface EducationEntry {
  id: string
  degree: string
  school: string
  link: string
  start_date: string
  end_date: string
  location: string
  description: string
  hidden?: boolean
}

export interface ExperienceEntry {
  id: string
  title: string
  company: string
  link: string
  start_date: string
  end_date: string
  location: string
  description: string
  hidden?: boolean
}

export interface ProjectEntry {
  id: string
  name: string
  link: string
  start_date: string
  end_date: string
  description: string
  hidden?: boolean
}

export interface CustomEntry {
  id: string
  title: string
  subtitle: string
  start_date: string
  end_date: string
  description: string
  hidden?: boolean
}

export interface CustomSection {
  id: string
  title: string
  entries: CustomEntry[]
}

export interface StructuredResume {
  personal: PersonalInfo
  skills: string[]
  education: EducationEntry[]
  experience: ExperienceEntry[]
  projects: ProjectEntry[]
  custom: CustomSection[]
}

export interface GitHubImportResult {
  status: string
  added_projects: number
  matched_by_job?: boolean
  resume: StructuredResume
}

export type AssistAction = 'improve_writing' | 'suggest_content' | 'grammar_check' | 'shorter'

export type EntryKind = 'education' | 'experience' | 'project' | 'custom'
