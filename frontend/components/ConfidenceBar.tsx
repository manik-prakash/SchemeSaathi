"use client";

interface ConfidenceBarProps {
  confidence: number;
}

export default function ConfidenceBar({ confidence }: ConfidenceBarProps) {
  const pct = Math.round(confidence * 100);
  const color = confidence >= 0.7 ? "var(--color-sage)" : confidence >= 0.4 ? "var(--color-amber)" : "var(--color-accent)";
  const textColor = confidence >= 0.7 ? "var(--color-sage)" : confidence >= 0.4 ? "var(--color-amber)" : "var(--color-accent)";
  const barWidth = `${pct}%`;

  return (
    <div style={{ margin: "0.1rem 0 0.7rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "5px" }}>
        <span style={{ fontSize: "0.73rem", color: "var(--color-text-muted)", fontWeight: 500 }}>
          Confidence
        </span>
        <span style={{ fontSize: "0.73rem", fontWeight: 700, color: textColor }}>
          {pct}%
        </span>
      </div>
      <div style={{
        background: "var(--color-border)",
        borderRadius: "999px",
        height: "6px",
        overflow: "hidden",
      }}>
        <div style={{
          height: "6px",
          borderRadius: "999px",
          background: color,
          width: barWidth,
          "--bar-width": barWidth,
          animation: "bar-grow 0.7s ease-out both",
        } as React.CSSProperties} />
      </div>
    </div>
  );
}
