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

export interface UserProfile {
  jobTitle: string
  targetRoles: string
  tone: string
  strengths: string
  goals: string
}
