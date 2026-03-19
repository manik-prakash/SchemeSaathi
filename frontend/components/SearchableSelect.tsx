"use client";

import { useEffect, useRef, useState } from "react";

export const INDIAN_STATES_AND_UTS = [
  "All",
  // States
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
  "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
  "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
  "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
  // Union Territories
  "Andaman and Nicobar Islands", "Chandigarh",
  "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
  "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
];

interface SearchableSelectProps {
  options: string[];
  value: string;
  placeholder?: string;
  onSelect: (value: string) => void;
  disabled?: boolean;
}

export default function SearchableSelect({
  options,
  value,
  placeholder = "Search...",
  onSelect,
  disabled = false,
}: SearchableSelectProps) {
  const [query, setQuery] = useState(value);
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = options.filter((o) =>
    o.toLowerCase().includes(query.toLowerCase())
  );

  // Keep display in sync when value changes externally
  useEffect(() => {
    setQuery(value);
  }, [value]);

  function handleSelect(option: string) {
    onSelect(option);
    setQuery(option);
    setOpen(false);
    setHighlighted(0);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!open) {
      if (e.key === "ArrowDown" || e.key === "Enter") setOpen(true);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlighted((h) => Math.min(h + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlighted((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filtered[highlighted]) handleSelect(filtered[highlighted]);
    } else if (e.key === "Escape") {
      setOpen(false);
      setQuery(value);
    }
  }

  // Close when clicking outside
  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setQuery(value);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [value]);

  return (
    <div ref={containerRef} style={{ position: "relative", width: "100%" }}>
      <input
        ref={inputRef}
        className="field-base"
        type="text"
        value={query}
        placeholder={placeholder}
        disabled={disabled}
        autoComplete="off"
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
          setHighlighted(0);
        }}
        onFocus={() => {
          setOpen(true);
          setHighlighted(0);
        }}
        onKeyDown={handleKeyDown}
        style={{ cursor: disabled ? "not-allowed" : "text" }}
      />

      {open && filtered.length > 0 && (
        <ul
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            zIndex: 50,
            background: "var(--color-bg-card)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-sm)",
            boxShadow: "var(--shadow-hover)",
            maxHeight: "220px",
            overflowY: "auto",
            margin: 0,
            padding: "4px 0",
            listStyle: "none",
          }}
        >
          {filtered.map((option, i) => (
            <li
              key={option}
              onMouseDown={() => handleSelect(option)}
              onMouseEnter={() => setHighlighted(i)}
              style={{
                padding: "0.4rem 0.75rem",
                fontSize: "0.9rem",
                cursor: "pointer",
                background:
                  i === highlighted
                    ? "var(--color-bg-muted)"
                    : "transparent",
                color:
                  option === value
                    ? "var(--color-sage)"
                    : "var(--color-text-primary)",
                fontWeight: option === value ? 600 : 400,
              }}
            >
              {option}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
