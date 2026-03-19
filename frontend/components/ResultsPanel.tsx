import type { AgentOutput } from "@/app/types";
import AgentTrace from "./AgentTrace";
import EligibilityCard from "./EligibilityCard";

interface ResultsPanelProps {
  output: AgentOutput;
}

export default function ResultsPanel({ output }: ResultsPanelProps) {
  const clearCount = output.results.filter((r) => r.verdict === "Clearly Eligible").length;
  const maybeCount = output.results.filter((r) => r.verdict === "Maybe Eligible").length;

  return (
    <div>
      {/* Summary card */}
      <div style={{
        background: "var(--color-amber-light)",
        border: "1.5px solid var(--color-border)",
        borderLeft: "4px solid var(--color-amber)",
        borderRadius: "var(--radius-md)",
        padding: "1rem 1.25rem",
        marginBottom: "1.5rem",
        lineHeight: 1.65,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
          <span style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--color-amber)" }}>
            AI Summary
          </span>
        </div>
        <p style={{ margin: 0, fontSize: "0.875rem", color: "var(--color-text-primary)", whiteSpace: "pre-wrap" }}>
          {output.final_answer}
        </p>
      </div>

      {/* Stats row */}
      {output.results.length > 0 && (
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem", flexWrap: "wrap" }}>
          <h2 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "var(--color-text-primary)" }}>
            Matching Schemes
          </h2>
          {clearCount > 0 && (
            <span style={{
              background: "var(--color-eligible-bg)",
              color: "var(--color-eligible-text)",
              borderRadius: "999px",
              padding: "0.2rem 0.65rem",
              fontSize: "0.72rem",
              fontWeight: 700,
            }}>
              {clearCount} clearly eligible
            </span>
          )}
          {maybeCount > 0 && (
            <span style={{
              background: "var(--color-maybe-bg)",
              color: "var(--color-maybe-text)",
              borderRadius: "999px",
              padding: "0.2rem 0.65rem",
              fontSize: "0.72rem",
              fontWeight: 700,
            }}>
              {maybeCount} maybe eligible
            </span>
          )}
        </div>
      )}

      {/* Cards */}
      {output.results.length > 0 ? (
        <div className="stagger">
          {output.results.map((result) => (
            <EligibilityCard key={result.scheme_name} result={result} />
          ))}
        </div>
      ) : (
        <div style={{
          background: "var(--color-bg-muted)",
          border: "1.5px solid var(--color-border)",
          borderRadius: "var(--radius-md)",
          padding: "2rem",
          textAlign: "center",
          color: "var(--color-text-muted)",
        }}>
          <p style={{ margin: "0 0 0.25rem", fontWeight: 600, color: "var(--color-text-secondary)" }}>No strong matches found</p>
          <p style={{ margin: 0, fontSize: "0.83rem" }}>Try adjusting income, education level, or state.</p>
        </div>
      )}

      <AgentTrace steps={output.trace_steps} />
    </div>
  );
}
