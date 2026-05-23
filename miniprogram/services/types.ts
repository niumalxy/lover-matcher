// 与后端 API 对应的 DTO 类型

export interface ApiEnvelope<T> {
  code: number
  msg: string
  data: T
}

export interface UserOut {
  id: string
  openid: string
  name: string
  gender: 'M' | 'F' | ''
  expected_gender: 'M' | 'F' | 'ANY' | ''
  contact: string
  avatar_url: string
  roles: string
}

export interface CustomQuestion {
  question: string
  ideal_answer: string
  priority: 'low' | 'medium' | 'high'
}

export interface StructuredProfile {
  self_intro: string
  personality: string[]
  hobbies: string[]
  hard_requirements: string[]
  soft_requirements: string[]
  speaking_style: string
  custom_questions: CustomQuestion[]
}

export interface ProfileOut {
  user_id: string
  raw_input: string
  structured: StructuredProfile
  updated_at: string
}

export interface CandidateSummary {
  user_id: string
  name: string
  gender: string
  avatar_url: string
  self_intro: string
}

export interface CandidateListResult {
  viewer_user_id: string
  items: CandidateSummary[]
}

export interface CandidateDetail extends CandidateSummary {
  personality: string[]
  hobbies: string[]
}

export type ConversationStatus = 'active' | 'matched' | 'ended' | 'blacklisted'
export type MessageSender = 'matcher' | 'agent'

export interface ConversationOut {
  id: string
  matchee_user_id: string
  matcher_user_id: string
  status: ConversationStatus
  created_at: string
  updated_at: string
  peer_name: string
  peer_avatar_url: string
}

export interface MessageOut {
  id: string
  conversation_id: string
  sender: MessageSender
  content: string
  created_at: string
}

export interface SendMessageResult {
  reply: string
  status: ConversationStatus
  match_id: string | null
  evaluation_reason: string
}

export interface MatchOut {
  id: string
  conversation_id: string
  matchee_user_id: string
  matcher_user_id: string
  matchee_decision: 'pending' | 'approved' | 'rejected'
  created_at: string
  decided_at: string
  peer_name: string
  peer_avatar_url: string
  peer_contact: string
}
