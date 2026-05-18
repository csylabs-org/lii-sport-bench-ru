export type Tier = 1 | 2 | 3;
export type Difficulty = "Basic" | "Applied" | "Expert";

export interface Question {
  id: string;
  sport_prefix: string;
  category_prefix: string;
  number: number;
  audience: string;
  difficulty: Difficulty;
  is_mcq: boolean;
  question: string;
  reference_answer: string;
  rubric: string;
  tier: Tier;
  sport_file: string;
}

export interface CandidateOutput {
  question_id: string;
  model: string;
  content: string;
  prompt_tokens: number;
  completion_tokens: number;
  elapsed_ms: number;
  ok: boolean;
  error?: string;
}

export interface JudgeScore {
  question_id: string;
  candidate_model: string;
  judge_model: string;
  accuracy: number;
  completeness: number;
  bonus: number;
  ru_linguistic: number;
  overall: number;
  reasoning: string;
  ok: boolean;
  error?: string;
}

export interface AggregatedRow {
  candidate: string;
  bucket: string;
  bucket_type: "overall" | "sport" | "difficulty" | "audience" | "tier";
  n: number;
  accuracy: number;
  completeness: number;
  bonus: number;
  ru_linguistic: number;
  overall: number;
}
