import axios from 'axios'
import type {
  AssistAction,
  AuthResponse,
  AuthUser,
  FullAnalysis,
  GitHubImportResult,
  LLMConfig,
  SkillConfirmations,
  StructuredResume,
  UserProfile,
} from '../types'

const BASE = '/api'
const TOKEN_KEY = 'scfa_token'

export const tokenStorage = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

const http = axios.create({ baseURL: BASE })

http.interceptors.request.use(config => {
  const token = tokenStorage.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function register(email: string, password: string): Promise<AuthResponse> {
  const res = await http.post<AuthResponse>('/auth/register', { email, password })
  return res.data
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await http.post<AuthResponse>('/auth/login', { email, password })
  return res.data
}

export async function fetchMe(): Promise<AuthUser> {
  const res = await http.get<AuthUser>('/auth/me')
  return res.data
}

export async function forgotPassword(email: string): Promise<{ message: string; reset_token?: string }> {
  const res = await http.post('/auth/forgot', { email })
  return res.data
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  await http.post('/auth/reset', { token, new_password: newPassword })
}

// ── Resume (structured) ──────────────────────────────────────────────────────

export async function getResume(): Promise<StructuredResume> {
  const res = await http.get<StructuredResume>('/resume')
  return res.data
}

export async function saveResume(resume: StructuredResume): Promise<void> {
  await http.put('/resume', { resume })
}

export async function deleteResume(): Promise<void> {
  await http.delete('/resume')
}

export async function importResumeText(text: string): Promise<StructuredResume> {
  const res = await http.post<StructuredResume>('/resume/import', { text })
  return res.data
}

export async function parseResumeText(text: string): Promise<StructuredResume> {
  const res = await http.post<StructuredResume>('/resume/parse', { text })
  return res.data
}

export async function getSkillConfirmations(): Promise<SkillConfirmations> {
  const res = await http.get<{ confirmations: SkillConfirmations }>('/user/skill-confirmations')
  return res.data.confirmations
}

export async function saveSkillConfirmation(skillName: string, hasSkill: boolean): Promise<void> {
  await http.post('/user/skill-confirmations', { skill_name: skillName, has_skill: hasSkill })
}

export async function importGithubProjects(
  username: string,
  maxRepos = 6,
  jobText = '',
): Promise<GitHubImportResult> {
  const res = await http.post<GitHubImportResult>('/github/import', {
    username,
    max_repos: maxRepos,
    job_text: jobText,
  })
  return res.data
}

export async function getUserProfile(): Promise<UserProfile> {
  const res = await http.get<UserProfile>('/user/profile')
  return res.data
}

export async function saveUserProfile(profile: UserProfile): Promise<void> {
  await http.put('/user/profile', profile)
}

export async function assistText(text: string, action: AssistAction): Promise<string> {
  const res = await http.post<{ text: string }>('/resume/assist', { text, action })
  return res.data.text
}

// ── PDF / Analysis ───────────────────────────────────────────────────────────

export async function uploadPdf(file: File): Promise<{ text: string; resume: StructuredResume }> {
  const form = new FormData()
  form.append('file', file)
  const res = await http.post<{ text: string; resume: StructuredResume }>('/upload-pdf', form)
  return res.data
}

export async function analyze(jobText: string): Promise<FullAnalysis> {
  const form = new FormData()
  form.append('job_text', jobText)
  const res = await http.post<FullAnalysis>('/analyze', form)
  return res.data
}

export async function downloadResumePdf(resumeMarkdown: string): Promise<void> {
  const form = new FormData()
  form.append('resume_markdown', resumeMarkdown)
  const res = await http.post('/download/resume', form, { responseType: 'blob' })
  triggerDownload(res.data as Blob, 'resume.pdf')
}

export async function downloadCoverLetterPdf(coverLetterText: string): Promise<void> {
  const form = new FormData()
  form.append('cover_letter_text', coverLetterText)
  const res = await http.post('/download/cover-letter', form, { responseType: 'blob' })
  triggerDownload(res.data as Blob, 'cover_letter.pdf')
}

export async function getConfig(): Promise<{ provider: string; model_name: string; has_api_key: boolean }> {
  const res = await http.get('/config')
  return res.data
}

export async function saveConfig(config: LLMConfig): Promise<void> {
  await http.post('/config', config)
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
