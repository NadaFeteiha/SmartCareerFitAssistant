import axios from 'axios'
import type { FullAnalysis, LLMConfig } from '../types'

const BASE = '/api'

export async function uploadPdf(file: File): Promise<string> {
  const form = new FormData()
  form.append('file', file)
  const res = await axios.post<{ text: string }>(`${BASE}/upload-pdf`, form)
  return res.data.text
}

export async function analyze(resumeText: string, jobText: string): Promise<FullAnalysis> {
  const form = new FormData()
  form.append('resume_text', resumeText)
  form.append('job_text', jobText)
  const res = await axios.post<FullAnalysis>(`${BASE}/analyze`, form)
  return res.data
}

export async function downloadResumePdf(resumeMarkdown: string): Promise<void> {
  const form = new FormData()
  form.append('resume_markdown', resumeMarkdown)
  const res = await axios.post(`${BASE}/download/resume`, form, { responseType: 'blob' })
  triggerDownload(res.data as Blob, 'resume.pdf')
}

export async function downloadCoverLetterPdf(coverLetterText: string): Promise<void> {
  const form = new FormData()
  form.append('cover_letter_text', coverLetterText)
  const res = await axios.post(`${BASE}/download/cover-letter`, form, { responseType: 'blob' })
  triggerDownload(res.data as Blob, 'cover_letter.pdf')
}

export async function getConfig(): Promise<{ provider: string; model_name: string; has_api_key: boolean }> {
  const res = await axios.get(`${BASE}/config`)
  return res.data
}

export async function saveConfig(config: LLMConfig): Promise<void> {
  await axios.post(`${BASE}/config`, config)
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
