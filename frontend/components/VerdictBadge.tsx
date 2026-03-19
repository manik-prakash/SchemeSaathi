import type { EligibilityResult } from "@/app/types";

interface VerdictBadgeProps {
  verdict: EligibilityResult["verdict"];
}

const STYLES: Record<EligibilityResult["verdict"], { bg: string; color: string; border: string }> = {
  "Clearly Eligible":   { bg: "var(--color-eligible-bg)", color: "var(--color-eligible-text)", border: "var(--color-sage-light)" },
  "Maybe Eligible":     { bg: "var(--color-maybe-bg)",    color: "var(--color-maybe-text)",    border: "var(--color-amber-light)" },
  "Likely Not Eligible":{ bg: "var(--color-not-bg)",      color: "var(--color-not-text)",      border: "var(--color-accent-light)" },
};

export default function VerdictBadge({ verdict }: VerdictBadgeProps) {
  const s = STYLES[verdict];
  return (
    <span style={{
      display: "inline-block",
      background: s.bg,
      color: s.color,
      border: `1px solid ${s.border}`,
      borderRadius: "999px",
      padding: "0.18rem 0.6rem",
      fontSize: "0.73rem",
      fontWeight: 700,
      whiteSpace: "nowrap",
      letterSpacing: "0.01em",
    }}>
      {verdict}
    </span>
  );
}
