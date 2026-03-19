import type { AgentTraceStep } from "@/app/types";

const TOOL_META: Record<string, { color: string; label: string }> = {
  session_context:     { color: "#8b6f5a", label: "Profile" },
  scheme_finder:       { color: "#5a7d62", label: "Web Search" },
  eligibility_checker: { color: "#7a8b5a", label: "Eligibility" },
  calculator:          { color: "#b8832e", label: "Scoring" },
  web_search:          { color: "#5a6d8b", label: "Link Check" },
};

interface AgentTraceProps {
  steps: AgentTraceStep[];
}

export default function AgentTrace({ steps }: AgentTraceProps) {
  if (!steps.length) return null;

  return (
    <details style={{ marginTop: "1.75rem" }}>
      <summary style={{
        display: "flex",
        alignItems: "center",
        gap: "0.6rem",
        padding: "0.65rem 1rem",
        background: "var(--color-bg-muted)",
        border: "1.5px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        cursor: "pointer",
        userSelect: "none",
        fontSize: "0.82rem",
        fontWeight: 600,
        color: "var(--color-text-secondary)",
      }}>
        <span>Agent Trace</span>
        <span style={{
          marginLeft: "auto",
          background: "var(--color-border)",
          borderRadius: "999px",
          padding: "0.1rem 0.5rem",
          fontSize: "0.7rem",
          fontWeight: 700,
          color: "var(--color-text-muted)",
        }}>
          {steps.length} steps
        </span>
      </summary>

      <div style={{
        border: "1.5px solid var(--color-border)",
        borderTop: "none",
        borderRadius: "0 0 var(--radius-md) var(--radius-md)",
        overflow: "hidden",
      }}>
        {steps.map((step, i) => {
          const meta = TOOL_META[step.tool_name] ?? { icon: "", color: "#8b6f5a", label: step.tool_name };
          return (
            <details key={step.step_number} style={{
              borderBottom: i < steps.length - 1 ? "1px solid var(--color-border)" : "none",
            }}>
              <summary style={{
                display: "flex",
                alignItems: "center",
                gap: "0.6rem",
                padding: "0.6rem 1rem",
                cursor: "pointer",
                userSelect: "none",
                background: "var(--color-bg-card)",
                transition: "background 0.15s ease",
              }}>
                {/* Step number */}
                <span style={{
                  width: "20px", height: "20px", flexShrink: 0,
                  borderRadius: "50%",
                  background: "var(--color-bg-muted)",
                  border: "1.5px solid var(--color-border)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "0.65rem",
                  fontWeight: 700,
                  color: "var(--color-text-muted)",
                }}>
                  {step.step_number}
                </span>

                {/* Tool badge */}
                <span style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.25rem",
                  background: `${meta.color}18`,
                  borderRadius: "4px",
                  padding: "0.15rem 0.45rem",
                  fontSize: "0.7rem",
                  fontWeight: 700,
                  color: meta.color,
                  flexShrink: 0,
                }}>
                  {meta.label}
                </span>

                <span style={{ fontSize: "0.8rem", color: "var(--color-text-primary)", lineHeight: 1.3 }}>
                  {step.action}
                </span>
              </summary>

              <div style={{
                padding: "0.75rem 1rem 0.85rem 2.85rem",
                background: "var(--color-bg-muted)",
                borderTop: "1px solid var(--color-border)",
              }}>
                <p style={{ margin: "0 0 0.5rem", fontSize: "0.8rem", color: "var(--color-text-secondary)", lineHeight: 1.5 }}>
                  <strong style={{ color: "var(--color-text-primary)" }}>Observation:</strong>{" "}
                  {step.observation}
                </p>
                {Object.keys(step.tool_input).length > 0 && (
                  <pre style={{
                    margin: 0,
                    background: "var(--color-bg-card)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-sm)",
                    padding: "0.5rem 0.75rem",
                    fontSize: "0.73rem",
                    overflowX: "auto",
                    color: "var(--color-text-muted)",
                    lineHeight: 1.5,
                  }}>
                    {JSON.stringify(step.tool_input, null, 2)}
                  </pre>
                )}
              </div>
            </details>
          );
        })}
      </div>
    </details>
  );
}
