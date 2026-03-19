"use client";

import type { UserProfile } from "@/app/types";
import SearchableSelect, { INDIAN_STATES_AND_UTS } from "./SearchableSelect";

interface ProfileFormProps {
  profile: UserProfile;
  followUp: string;
  onChange: (profile: UserProfile) => void;
  onFollowUpChange: (val: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  disabled: boolean;
}

function Label({ children, hint }: { children: React.ReactNode; hint?: string }) {
  return (
    <label style={{ display: "block", marginBottom: "0.3rem" }}>
      <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--color-text-secondary)" }}>
        {children}
      </span>
      {hint && (
        <span style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", marginLeft: "0.4rem" }}>
          {hint}
        </span>
      )}
    </label>
  );
}

function FieldGroup({ children }: { children: React.ReactNode }) {
  return <div style={{ marginBottom: "0.85rem" }}>{children}</div>;
}

function SelectField({
  value, options, onChange, disabled,
}: {
  value: string; options: string[]; onChange: (val: string) => void; disabled: boolean;
}) {
  return (
    <select
      className="field-base"
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
    >
      {options.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}

function SectionHeader({ label }: { label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.45rem", marginBottom: "0.85rem", marginTop: "0.25rem" }}>
      <span style={{
        fontSize: "0.68rem",
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        color: "var(--color-text-muted)",
      }}>{label}</span>
      <div style={{ flex: 1, height: "1px", background: "var(--color-border)" }} />
    </div>
  );
}

export default function ProfileForm({
  profile, followUp, onChange, onFollowUpChange, onSubmit, disabled,
}: ProfileFormProps) {
  function set<K extends keyof UserProfile>(key: K, value: UserProfile[K]) {
    onChange({ ...profile, [key]: value });
  }

  return (
    <form onSubmit={onSubmit}>
      {/* Personal */}
      <SectionHeader label="Personal Details" />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 0.75rem" }}>
        <FieldGroup>
          <Label>Age</Label>
          <input
            className="field-base"
            type="number"
            min={0} max={120}
            value={profile.age}
            disabled={disabled}
            onChange={(e) => set("age", Number(e.target.value))}
          />
        </FieldGroup>
        <FieldGroup>
          <Label>Gender</Label>
          <SelectField
            value={profile.gender}
            options={["Any", "Male", "Female", "Other"]}
            onChange={(v) => set("gender", v as UserProfile["gender"])}
            disabled={disabled}
          />
        </FieldGroup>
      </div>

      <FieldGroup>
        <Label>State / Union Territory</Label>
        <SearchableSelect
          options={INDIAN_STATES_AND_UTS}
          value={profile.state}
          placeholder="Search or select state..."
          onSelect={(v) => set("state", v)}
          disabled={disabled}
        />
      </FieldGroup>

      <FieldGroup>
        <Label>Area Type</Label>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {["Rural", "Urban"].map((opt) => (
            <button
              key={opt}
              type="button"
              disabled={disabled}
              onClick={() => set("area_type", opt as UserProfile["area_type"])}
              style={{
                flex: 1,
                padding: "0.45rem",
                borderRadius: "var(--radius-sm)",
                border: "1.5px solid",
                borderColor: profile.area_type === opt ? "var(--color-sage)" : "var(--color-border)",
                background: profile.area_type === opt ? "var(--color-sage-light)" : "var(--color-bg-input)",
                color: profile.area_type === opt ? "var(--color-sage)" : "var(--color-text-secondary)",
                fontSize: "0.83rem",
                fontWeight: profile.area_type === opt ? 700 : 500,
                cursor: disabled ? "not-allowed" : "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {opt === "Rural" ? "Rural" : "Urban"}
            </button>
          ))}
        </div>
      </FieldGroup>

      {/* Education */}
      <SectionHeader label="Education & Occupation" />

      <FieldGroup>
        <Label>Student Status</Label>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {["Yes", "No"].map((opt) => (
            <button
              key={opt}
              type="button"
              disabled={disabled}
              onClick={() => set("student_status", opt as UserProfile["student_status"])}
              style={{
                flex: 1,
                padding: "0.45rem",
                borderRadius: "var(--radius-sm)",
                border: "1.5px solid",
                borderColor: profile.student_status === opt ? "var(--color-amber)" : "var(--color-border)",
                background: profile.student_status === opt ? "var(--color-amber-light)" : "var(--color-bg-input)",
                color: profile.student_status === opt ? "var(--color-amber)" : "var(--color-text-secondary)",
                fontSize: "0.83rem",
                fontWeight: profile.student_status === opt ? 700 : 500,
                cursor: disabled ? "not-allowed" : "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {opt === "Yes" ? "Yes, I'm a student" : "No"}
            </button>
          ))}
        </div>
      </FieldGroup>

      <FieldGroup>
        <Label>Education Level</Label>
        <SelectField
          value={profile.education_level}
          options={["School", "Post-Matric", "Undergraduate", "Graduate", "Postgraduate"]}
          onChange={(v) => set("education_level", v as UserProfile["education_level"])}
          disabled={disabled}
        />
      </FieldGroup>

      <FieldGroup>
        <Label>Occupation</Label>
        <SelectField
          value={profile.occupation}
          options={["Student", "Farmer", "Self-Employed", "Unemployed", "Employed"]}
          onChange={(v) => set("occupation", v as UserProfile["occupation"])}
          disabled={disabled}
        />
      </FieldGroup>

      {/* Financial */}
      <SectionHeader label="Financial & Social" />

      <FieldGroup>
        <Label hint="per year">Annual Family Income (₹)</Label>
        <div style={{ position: "relative" }}>
          <span style={{
            position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)",
            fontSize: "0.85rem", color: "var(--color-text-muted)", pointerEvents: "none",
          }}>₹</span>
          <input
            className="field-base"
            type="number"
            min={0} max={5000000} step={10000}
            value={profile.annual_family_income}
            disabled={disabled}
            onChange={(e) => set("annual_family_income", Number(e.target.value))}
            style={{ paddingLeft: "1.6rem" }}
          />
        </div>
        <div style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", marginTop: "0.25rem" }}>
          ≈ ₹{Math.round(profile.annual_family_income / 1000)}k/yr · ₹{Math.round(profile.annual_family_income / 12000)}k/mo
        </div>
      </FieldGroup>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 0.75rem" }}>
        <FieldGroup>
          <Label>Category</Label>
          <SelectField
            value={profile.category}
            options={["General", "OBC", "SC", "ST", "Minority"]}
            onChange={(v) => set("category", v as UserProfile["category"])}
            disabled={disabled}
          />
        </FieldGroup>
        <FieldGroup>
          <Label>Disability</Label>
          <SelectField
            value={profile.disability_status}
            options={["No", "Yes"]}
            onChange={(v) => set("disability_status", v as UserProfile["disability_status"])}
            disabled={disabled}
          />
        </FieldGroup>
      </div>

      {/* Optional */}
      <SectionHeader label="Optional Hint" />
      <FieldGroup>
        <Label>Refinement</Label>
        <textarea
          className="field-base"
          rows={2}
          placeholder="e.g. prioritize scholarship schemes only"
          value={followUp}
          disabled={disabled}
          onChange={(e) => onFollowUpChange(e.target.value)}
          style={{ resize: "vertical", fontFamily: "inherit", lineHeight: 1.5 }}
        />
      </FieldGroup>

      {/* Submit */}
      <button
        type="submit"
        disabled={disabled}
        style={{
          width: "100%",
          padding: "0.8rem 1rem",
          marginTop: "0.25rem",
          background: disabled
            ? "var(--color-bg-muted)"
            : "linear-gradient(135deg, var(--color-sage) 0%, #4a7a55 100%)",
          color: disabled ? "var(--color-text-muted)" : "#fff",
          border: "none",
          borderRadius: "var(--radius-sm)",
          fontSize: "0.9rem",
          fontWeight: 700,
          cursor: disabled ? "not-allowed" : "pointer",
          transition: "opacity 0.2s ease, transform 0.1s ease",
          letterSpacing: "0.02em",
          boxShadow: disabled ? "none" : "0 2px 8px rgba(90,125,98,0.35)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "0.5rem",
        }}
      >
        {disabled ? (
          <>
            <span style={{
              width: "14px", height: "14px",
              border: "2px solid rgba(150,120,90,0.3)",
              borderTopColor: "var(--color-text-muted)",
              borderRadius: "50%",
              animation: "spin 0.7s linear infinite",
              display: "inline-block",
            }} />
            Checking eligibility...
          </>
        ) : (
          "Check My Eligibility →"
        )}
      </button>
    </form>
  );
}
