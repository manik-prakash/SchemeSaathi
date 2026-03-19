import type { AgentOutput, EligibilityRequest } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function checkEligibility(
  payload: EligibilityRequest
): Promise<AgentOutput> {
  const res = await fetch(`${API_BASE}/check-eligibility`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API error ${res.status}: ${detail}`);
  }

  return res.json() as Promise<AgentOutput>;
}
