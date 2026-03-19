import type { EligibilityResult } from "@/app/types";
import ConfidenceBar from "./ConfidenceBar";
import VerdictBadge from "./VerdictBadge";

interface EligibilityCardProps {
  result: EligibilityResult;
}

export default function EligibilityCard({ result }: EligibilityCardProps) {
  return (
    <div className="card" style={{
      marginBottom: "0.85rem",
      overflow: "hidden",
      transition: "box-shadow 0.2s ease, transform 0.15s ease",
    }}>
      {/* Colored top accent bar */}
      <div style={{
        height: "3px",
        background: result.verdict === "Clearly Eligible"
          ? "linear-gradient(90deg, var(--color-sage), var(--color-sage-light))"
          : result.verdict === "Maybe Eligible"
          ? "linear-gradient(90deg, var(--color-amber), var(--color-amber-light))"
          : "linear-gradient(90deg, var(--color-accent), var(--color-accent-light))",
      }} />

      <div style={{ padding: "1.1rem 1.25rem" }}>
        {/* Header row */}
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-start", gap: "0.4rem 0.5rem", marginBottom: "0.6rem" }}>
          <span style={{ fontWeight: 700, fontSize: "0.97rem", color: "var(--color-text-primary)", lineHeight: 1.3, flex: "1 1 auto" }}>
            {result.scheme_name}
          </span>
          <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", flexShrink: 0 }}>
            <VerdictBadge verdict={result.verdict} />
            <span style={{
              background: result.is_national ? "var(--color-sage-light)" : "var(--color-amber-light)",
              color: result.is_national ? "var(--color-sage)" : "var(--color-amber)",
              borderRadius: "999px",
              padding: "0.15rem 0.5rem",
              fontSize: "0.7rem",
              fontWeight: 700,
            }}>
              {result.is_national ? "National" : "State"}
            </span>
          </div>
        </div>

        <ConfidenceBar confidence={result.confidence} />

        {/* Reason */}
        <p style={{ fontSize: "0.84rem", color: "var(--color-text-secondary)", fontStyle: "italic", margin: "0 0 0.85rem", lineHeight: 1.55 }}>
          {result.reason}
        </p>

        {/* Conditions */}
        {(result.matched_conditions.length > 0 || result.failed_conditions.length > 0) && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.85rem" }}>
            {result.matched_conditions.length > 0 && (
              <div style={{
                background: "var(--color-eligible-bg)",
                borderRadius: "var(--radius-sm)",
                padding: "0.6rem 0.75rem",
              }}>
                <div style={{ fontSize: "0.66rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--color-sage)", marginBottom: "0.4rem" }}>
                  ✓ Matched
                </div>
                <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "2px" }}>
                  {result.matched_conditions.map((c) => (
                    <li key={c} style={{ fontSize: "0.78rem", color: "var(--color-eligible-text)" }}>
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {result.failed_conditions.length > 0 && (
              <div style={{
                background: "var(--color-not-bg)",
                borderRadius: "var(--radius-sm)",
                padding: "0.6rem 0.75rem",
              }}>
                <div style={{ fontSize: "0.66rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--color-accent)", marginBottom: "0.4rem" }}>
                  ✗ Not Met
                </div>
                <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "2px" }}>
                  {result.failed_conditions.map((c) => (
                    <li key={c} style={{ fontSize: "0.78rem", color: "var(--color-not-text)" }}>
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Benefits */}
        {result.benefits && result.benefits !== "Not specified" && (
          <details style={{ marginBottom: "0.75rem" }}>
            <summary style={{
              fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)",
              cursor: "pointer", padding: "0.35rem 0",
              display: "flex", alignItems: "center", gap: "0.4rem",
            }}>
              What you get
            </summary>
            <p style={{ fontSize: "0.82rem", color: "var(--color-text-primary)", margin: "0.4rem 0 0 1.5rem", lineHeight: 1.55 }}>
              {result.benefits}
            </p>
          </details>
        )}

        {/* Documents */}
        {result.required_documents.length > 0 && (
          <details style={{ marginBottom: "0.85rem" }}>
            <summary style={{
              fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)",
              cursor: "pointer", padding: "0.35rem 0",
              display: "flex", alignItems: "center", gap: "0.4rem",
            }}>
              Required Documents ({result.required_documents.length})
            </summary>
            <ul style={{ listStyle: "none", margin: "0.4rem 0 0 1.5rem", padding: 0, display: "flex", flexDirection: "column", gap: "3px" }}>
              {result.required_documents.map((d) => (
                <li key={d} style={{ fontSize: "0.8rem", color: "var(--color-text-primary)" }}>
                  · {d}
                </li>
              ))}
            </ul>
          </details>
        )}

        {/* Apply button */}
        <a
          href={result.official_link}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.35rem",
            background: "var(--color-sage)",
            color: "#fff",
            borderRadius: "var(--radius-sm)",
            padding: "0.45rem 1rem",
            fontSize: "0.82rem",
            fontWeight: 700,
            textDecoration: "none",
            transition: "opacity 0.15s ease",
            letterSpacing: "0.01em",
          }}
        >
          Apply Now →
        </a>
      </div>
    </div>
  );
}
