"use client";

import { useRef, useState } from "react";
import { checkEligibility } from "./api";
import type { AgentOutput, UserProfile } from "./types";
import LoadingOverlay from "@/components/LoadingOverlay";
import ProfileForm from "@/components/ProfileForm";
import ResultsPanel from "@/components/ResultsPanel";

const DEFAULT_PROFILE: UserProfile = {
  age: 19,
  gender: "Any",
  state: "All",
  student_status: "Yes",
  annual_family_income: 200000,
  category: "General",
  disability_status: "No",
  education_level: "Undergraduate",
  occupation: "Student",
  area_type: "Urban",
};

type Status = "idle" | "loading" | "success" | "error";

export default function Home() {
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [followUp, setFollowUp] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [output, setOutput] = useState<AgentOutput | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const resultsRef = useRef<HTMLDivElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");
    setOutput(null);
    try {
      const result = await checkEligibility({
        profile,
        follow_up: followUp.trim() || undefined,
      });
      setOutput(result);
      setStatus("success");
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 120);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unknown error");
      setStatus("error");
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {status === "loading" && <LoadingOverlay />}

      {/* ── Header ── */}
      <header style={{
        background: "var(--color-bg-card)",
        borderBottom: "1.5px solid var(--color-border)",
        padding: "0.9rem 2rem",
        display: "flex",
        alignItems: "center",
        gap: "0.85rem",
        position: "sticky",
        top: 0,
        zIndex: 40,
        boxShadow: "0 1px 8px rgba(80,40,10,0.07)",
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: "1rem", fontWeight: 700, color: "var(--color-text-primary)", lineHeight: 1.2 }}>
            SchemeSathi
          </h1>
          <p style={{ margin: 0, fontSize: "0.73rem", color: "var(--color-text-muted)", lineHeight: 1.3 }}>
            AI-powered checker for Indian government schemes
          </p>
        </div>

        {status === "success" && output && (
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{
              background: "var(--color-eligible-bg)",
              color: "var(--color-eligible-text)",
              borderRadius: "999px",
              padding: "0.25rem 0.75rem",
              fontSize: "0.75rem",
              fontWeight: 600,
            }}>
              {output.results.length} scheme{output.results.length !== 1 ? "s" : ""} found
            </span>
          </div>
        )}
      </header>

      {/* ── Main ── */}
      <main style={{
        flex: 1,
        maxWidth: "1120px",
        width: "100%",
        margin: "0 auto",
        padding: "1.75rem 1.5rem 3rem",
        display: "grid",
        gridTemplateColumns: "360px 1fr",
        gap: "1.75rem",
        alignItems: "start",
      }}>
        {/* Left — Form */}
        <div style={{
          position: "sticky",
          top: "72px",
          maxHeight: "calc(100vh - 88px)",
          overflowY: "auto",
          scrollbarWidth: "thin",
        }}>
          <div className="card" style={{ padding: "1.5rem", boxShadow: "var(--shadow-form)" }}>
            <h2 style={{ margin: "0 0 1.25rem", fontSize: "0.95rem", fontWeight: 700, color: "var(--color-text-primary)" }}>
              Your Profile
            </h2>
            <ProfileForm
              profile={profile}
              followUp={followUp}
              onChange={setProfile}
              onFollowUpChange={setFollowUp}
              onSubmit={handleSubmit}
              disabled={status === "loading"}
            />
          </div>
        </div>

        {/* Right — Results */}
        <div ref={resultsRef} style={{
          position: "sticky",
          top: "72px",
          maxHeight: "calc(100vh - 88px)",
          overflowY: "auto",
          scrollbarWidth: "thin",
          minHeight: "300px",
        }}>
          {status === "idle" && (
            <div className="animate-fade-in" style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              minHeight: "400px",
              textAlign: "center",
              gap: "1rem",
              padding: "2rem",
            }}>
              <p style={{ margin: 0, fontSize: "1rem", fontWeight: 600, color: "var(--color-text-primary)" }}>
                Ready to check your eligibility
              </p>
              <p style={{ margin: 0, fontSize: "0.875rem", color: "var(--color-text-muted)", maxWidth: "320px", lineHeight: 1.6 }}>
                Fill in your profile on the left and click{" "}
                <strong style={{ color: "var(--color-sage)", fontWeight: 700 }}>Check My Eligibility</strong>
                {" "}to discover government schemes you qualify for.
              </p>
              <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.5rem" }}>
                {["Live web search", "Eligibility check", "Smart ranking"].map((item) => (
                  <span key={item} style={{
                    fontSize: "0.75rem",
                    color: "var(--color-text-muted)",
                    background: "var(--color-bg-muted)",
                    borderRadius: "999px",
                    padding: "0.3rem 0.75rem",
                  }}>{item}</span>
                ))}
              </div>
            </div>
          )}

          {status === "error" && (
            <div className="animate-fade-up card" style={{
              padding: "1.25rem 1.5rem",
              borderLeft: "4px solid var(--color-accent)",
              background: "var(--color-not-bg)",
            }}>
              <p style={{ margin: "0 0 0.4rem", fontWeight: 700, color: "var(--color-not-text)", fontSize: "0.9rem" }}>
                Connection Error
              </p>
              <p style={{ margin: "0 0 0.5rem", fontSize: "0.85rem", color: "var(--color-not-text)" }}>
                {errorMessage}
              </p>
              <p style={{ margin: 0, fontSize: "0.78rem", color: "var(--color-text-muted)" }}>
                Make sure the FastAPI backend is running:{" "}
                <code style={{ background: "var(--color-bg-muted)", padding: "1px 6px", borderRadius: "4px", fontSize: "0.78rem" }}>
                  uvicorn api:app --reload --port 8000
                </code>
              </p>
            </div>
          )}

          {status === "success" && output && (
            <div className="animate-fade-up">
              <ResultsPanel output={output} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
