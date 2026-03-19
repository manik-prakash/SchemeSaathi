export interface UserProfile {
  age: number;
  gender: "Any" | "Male" | "Female" | "Other";
  state: string;
  student_status: "Yes" | "No";
  annual_family_income: number;
  category: "General" | "OBC" | "SC" | "ST" | "Minority";
  disability_status: "Yes" | "No";
  education_level: "School" | "Post-Matric" | "Undergraduate" | "Graduate" | "Postgraduate";
  occupation: "Student" | "Farmer" | "Self-Employed" | "Unemployed" | "Employed";
  area_type: "Rural" | "Urban";
}

export interface EligibilityResult {
  scheme_name: string;
  verdict: "Clearly Eligible" | "Maybe Eligible" | "Likely Not Eligible";
  matched_conditions: string[];
  failed_conditions: string[];
  confidence: number;
  reason: string;
  required_documents: string[];
  official_link: string;
  benefits: string;
  is_national: boolean;
}

export interface AgentTraceStep {
  step_number: number;
  action: string;
  tool_name: string;
  tool_input: Record<string, unknown>;
  observation: string;
}

export interface AgentOutput {
  final_answer: string;
  results: EligibilityResult[];
  trace_steps: AgentTraceStep[];
}

export interface EligibilityRequest {
  profile: UserProfile;
  follow_up?: string;
}
