// Course types
export interface Course {
  id: string
  name: string
  description: string | null
  created_by: string
  institution_id: string | null
  pedagogy_config: PedagogyConfig
  status: 'draft' | 'active' | 'archived'
  base_model: string
  temperature: number
  created_at: string
  updated_at: string
}

export interface PedagogyConfig {
  style: 'socratic' | 'guided_discovery' | 'direct_instruction' | 'worked_examples'
  response_patterns: ResponsePattern[]
  never_do: string[]
  always_do: string[]
  voice_description: string | null
}

export interface ResponsePattern {
  situation: string
  strategies: string[]
}

// Concept types
export interface Concept {
  id: string
  course_id: string
  name: string
  description: string | null
  prerequisites: string[]
  estimated_time_minutes: number | null
  difficulty_level: number | null
  learning_objectives: LearningObjective[]
  sequence_order: number | null
}

export interface LearningObjective {
  description: string
  bloom_level?: string
}

// Misconception types
export interface Misconception {
  id: string
  concept_id: string
  name: string
  description: string
  manifestation: string | null
  diagnostic_question: string | null
  correction_approach: string | null
  example_student_response: string | null
  example_tutor_response: string | null
  times_observed: number
  times_resolved: number
}

// Tutor session types
export interface Session {
  session_id: string
  course_id: string
  student_id: string
  current_concept_id: string | null
  current_concept_name: string | null
  started_at: string
  message_count: number
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  pedagogical_move?: string
}

// Assessment types
export interface MasteryEstimate {
  concept_id: string
  concept_name: string
  estimate: number
  confidence: number
  interaction_count: number
  last_updated: string | null
}

export interface MasteryReport {
  student_id: string
  course_id: string
  overall_mastery: number
  overall_confidence: number
  concepts: MasteryEstimate[]
  concepts_completed: string[]
  current_concept_id: string | null
  generated_at: string
}

export interface GamingFlag {
  type: string
  severity: 'low' | 'medium' | 'high'
  timestamp: string
  evidence: string
  resolved: boolean
}

export interface VerificationQuestion {
  concept_id: string
  concept_name: string
  question: string
  rationale: string
  look_for: string
  difficulty: 'easy' | 'medium' | 'hard'
}

export interface VerificationReport {
  id: string
  student_id: string
  course_id: string
  generated_at: string
  verification_status: string
  summary: {
    overall_mastery: number
    mastered_concepts: number
    total_concepts: number
    gaming_flags_count: number
    needs_attention: boolean
  }
  mastery_by_concept: MasteryEstimate[]
  concerns: GamingFlag[]
  recommended_questions: VerificationQuestion[]
}

// Analytics types
export interface ClassOverview {
  course_id: string
  course_name: string
  total_students: number
  active_students: number
  average_mastery: number
  students_with_gaming_flags: number
  completion_rate: number
}

export interface StudentSummary {
  student_id: string
  student_name: string | null
  overall_mastery: number
  concepts_completed: number
  total_concepts: number
  has_gaming_flags: boolean
  last_interaction: string | null
}
