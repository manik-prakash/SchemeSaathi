"use client";

import { useEffect, useState } from "react";

const STEPS = [
  { label: "Searching live web for schemes..." },
  { label: "LLM extracting scheme details..." },
  { label: "Checking your eligibility..." },
  { label: "Ranking and scoring results..." },
  { label: "Validating official links..." },
];

export default function LoadingOverlay() {
  const [activeStep, setActiveStep] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const stepInterval = setInterval(() => {
      setActiveStep((s) => (s < STEPS.length - 1 ? s + 1 : s));
    }, 4000);
    const elapsedInterval = setInterval(() => {
      setElapsed((e) => e + 1);
    }, 1000);
    return () => {
      clearInterval(stepInterval);
      clearInterval(elapsedInterval);
    };
  }, []);

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      zIndex: 100,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "rgba(253,248,243,0.92)",
      backdropFilter: "blur(4px)",
    }}>
      <div className="card animate-fade-up" style={{
        padding: "2rem 2.25rem",
        width: "min(420px, 90vw)",
        boxShadow: "var(--shadow-hover)",
      }}>
        {/* Spinner + title */}
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.5rem" }}>
          <div style={{
            width: "40px", height: "40px", flexShrink: 0,
            border: "3px solid var(--color-border)",
            borderTopColor: "var(--color-sage)",
            borderRadius: "50%",
            animation: "spin 0.8s linear infinite",
          }} />
          <div>
            <p style={{ margin: 0, fontWeight: 700, fontSize: "0.95rem", color: "var(--color-text-primary)" }}>
              Checking eligibility
            </p>
            <p style={{ margin: 0, fontSize: "0.78rem", color: "var(--color-text-muted)" }}>
              {elapsed}s elapsed · this may take 15–30s
            </p>
          </div>
        </div>

        {/* Step list */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {STEPS.map((step, i) => {
            const isDone = i < activeStep;
            const isActive = i === activeStep;
            const isPending = i > activeStep;
            return (
              <div key={i} style={{
                display: "flex",
                alignItems: "center",
                gap: "0.65rem",
                padding: "0.5rem 0.65rem",
                borderRadius: "var(--radius-sm)",
                background: isActive ? "var(--color-bg-muted)" : "transparent",
                transition: "background 0.3s ease",
                opacity: isPending ? 0.4 : 1,
              }}>
                {/* State indicator */}
                <div style={{
                  width: "20px", height: "20px", flexShrink: 0,
                  borderRadius: "50%",
                  background: isDone ? "var(--color-eligible-bg)" : isActive ? "var(--color-amber-light)" : "var(--color-border)",
                  border: `2px solid ${isDone ? "var(--color-sage)" : isActive ? "var(--color-amber)" : "var(--color-border)"}`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "0.65rem",
                  transition: "all 0.3s ease",
                }}>
                  {isDone ? "✓" : isActive ? (
                    <span style={{
                      width: "6px", height: "6px",
                      background: "var(--color-amber)",
                      borderRadius: "50%",
                      animation: "pulse-dot 1.2s ease-in-out infinite",
                    }} />
                  ) : null}
                </div>

                <span style={{
                  fontSize: "0.82rem",
                  fontWeight: isActive ? 600 : 400,
                  color: isDone ? "var(--color-text-muted)" : isActive ? "var(--color-text-primary)" : "var(--color-text-muted)",
                  textDecoration: isDone ? "line-through" : "none",
                }}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div style={{
          marginTop: "1.25rem",
          height: "4px",
          background: "var(--color-border)",
          borderRadius: "999px",
          overflow: "hidden",
        }}>
          <div style={{
            height: "100%",
            background: "linear-gradient(90deg, var(--color-sage), var(--color-amber))",
            borderRadius: "999px",
            width: `${((activeStep + 1) / STEPS.length) * 100}%`,
            transition: "width 0.6s ease",
          }} />
        </div>
      </div>
    </div>
  );
}
