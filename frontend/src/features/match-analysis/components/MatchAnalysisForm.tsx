import { useId, useState, type FormEvent } from "react";

import type { AnalysisRequestPayload } from "../../../types/analysis";

interface MatchAnalysisFormProps {
  onSubmit: (payload: AnalysisRequestPayload) => void;
  isLoading: boolean;
}

const MIN_LENGTH = 2;
const MAX_LENGTH = 80;
const POPULAR_MATCHUPS = [
  ["Argentina", "France"],
  ["Brazil", "England"],
  ["Spain", "Germany"],
  ["Portugal", "Netherlands"],
] as const;

export function MatchAnalysisForm({ onSubmit, isLoading }: MatchAnalysisFormProps) {
  const [homeTeam, setHomeTeam] = useState("");
  const [awayTeam, setAwayTeam] = useState("");
  const [touched, setTouched] = useState({ home: false, away: false });
  const formId = useId();
  const homeId = `${formId}-home`;
  const awayId = `${formId}-away`;

  const trimmedHome = homeTeam.trim();
  const trimmedAway = awayTeam.trim();

  const homeTooShort = touched.home && trimmedHome.length > 0 && trimmedHome.length < MIN_LENGTH;
  const awayTooShort = touched.away && trimmedAway.length > 0 && trimmedAway.length < MIN_LENGTH;
  const homeEmpty = touched.home && trimmedHome.length === 0;
  const awayEmpty = touched.away && trimmedAway.length === 0;
  const sameTeam =
    touched.home &&
    touched.away &&
    trimmedHome.length > 0 &&
    trimmedAway.length > 0 &&
    trimmedHome.toLowerCase() === trimmedAway.toLowerCase();

  const isValid =
    trimmedHome.length >= MIN_LENGTH &&
    trimmedHome.length <= MAX_LENGTH &&
    trimmedAway.length >= MIN_LENGTH &&
    trimmedAway.length <= MAX_LENGTH &&
    trimmedHome.toLowerCase() !== trimmedAway.toLowerCase();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setTouched({ home: true, away: true });
    if (!isValid) return;
    onSubmit({ homeTeam: trimmedHome, awayTeam: trimmedAway });
  }

  function applyMatchup(home: string, away: string) {
    setHomeTeam(home);
    setAwayTeam(away);
    setTouched({ home: true, away: true });
  }

  return (
    <form
      noValidate
      onSubmit={handleSubmit}
      className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.05] via-white/[0.025] to-transparent p-6 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_6%,transparent)] sm:p-8"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/40 to-transparent"
      />
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
            Tactical brief
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-balance">
            Pick the two national teams and let the analyst think.
          </h2>
        </div>
        <p className="text-xs text-white/45">
          Structured JSON · validated server-side · ~8 – 15s
        </p>
      </div>
      <p className="mt-2 text-sm text-white/55">
        Use official country names (e.g. Argentina, France, Brazil). Clear naming
        produces sharper tactical analysis.
      </p>

      <div className="mt-6 grid gap-5 sm:grid-cols-2">
        <Field
          id={homeId}
          label="Home team"
          value={homeTeam}
          onChange={(next) => {
            setHomeTeam(next);
            if (!touched.home) setTouched((t) => ({ ...t, home: true }));
          }}
          onBlur={() => setTouched((t) => ({ ...t, home: true }))}
          maxLength={MAX_LENGTH}
          placeholder="e.g. Argentina"
          error={homeTooShort || homeEmpty ? "Enter a team name (2+ characters)." : null}
        />
        <Field
          id={awayId}
          label="Away team"
          value={awayTeam}
          onChange={(next) => {
            setAwayTeam(next);
            if (!touched.away) setTouched((t) => ({ ...t, away: true }));
          }}
          onBlur={() => setTouched((t) => ({ ...t, away: true }))}
          maxLength={MAX_LENGTH}
          placeholder="e.g. France"
          error={awayTooShort || awayEmpty ? "Enter a team name (2+ characters)." : null}
        />
      </div>

      {sameTeam ? (
        <p
          role="alert"
          className="mt-3 inline-flex items-center gap-2 rounded-full border border-red-400/30 bg-red-400/[0.08] px-3 py-1 text-xs text-red-300"
        >
          <span aria-hidden>●</span>
          Home and away teams must be different.
        </p>
      ) : null}

      <div className="mt-6 flex flex-wrap items-center gap-2">
        <span className="text-[10px] font-semibold tracking-[0.22em] text-white/40 uppercase">
          Try a fixture
        </span>
        {POPULAR_MATCHUPS.map(([home, away]) => (
          <button
            key={`${home}-${away}`}
            type="button"
            onClick={() => applyMatchup(home, away)}
            className="inline-flex items-center rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white/70 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] transition hover:-translate-y-0.5 hover:border-pitch/40 hover:bg-pitch/10 hover:text-pitch hover:shadow-[0_0_16px_color-mix(in_srgb,var(--color-pitch)_20%,transparent)]"
          >
            {home} <span className="mx-2 text-white/30">vs</span> {away}
          </button>
        ))}
      </div>

      <div className="mt-8 flex flex-col-reverse items-stretch gap-3 border-t border-white/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-white/45">
          Analysis covers formations, strengths, weaknesses, duels, game flow,
          and coaching levers.
        </p>
        <button
          type="submit"
          disabled={!isValid || isLoading}
          className="group relative inline-flex items-center justify-center overflow-hidden rounded-full bg-gradient-to-b from-pitch to-pitch-deep px-7 py-3 text-sm font-semibold text-ink shadow-[0_8px_24px_-8px_color-mix(in_srgb,var(--color-pitch)_55%,transparent),inset_0_1px_0_color-mix(in_srgb,#ffffff_25%,transparent)] transition hover:from-pitch-soft hover:to-pitch disabled:cursor-not-allowed disabled:bg-white/10 disabled:from-white/10 disabled:to-white/10 disabled:text-white/40 disabled:shadow-none"
        >
          {isLoading ? (
            <>
              <span
                aria-hidden
                className="mr-2 inline-block size-2 animate-pulse rounded-full bg-ink"
              />
              Analyzing matchup…
            </>
          ) : (
            <>
              Generate tactical brief
              <span aria-hidden className="ml-2">
                →
              </span>
            </>
          )}
        </button>
      </div>
    </form>
  );
}

interface FieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (next: string) => void;
  onBlur: () => void;
  placeholder: string;
  maxLength: number;
  error: string | null;
}

function Field({
  id,
  label,
  value,
  onChange,
  onBlur,
  placeholder,
  maxLength,
  error,
}: FieldProps) {
  const errorId = `${id}-error`;
  const hasError = error !== null;

  return (
    <div className="flex flex-col gap-2">
      <label
        htmlFor={id}
        className="text-[10px] font-semibold tracking-[0.22em] text-white/55 uppercase"
      >
        {label}
      </label>
      <input
        id={id}
        name={id}
        type="text"
        value={value}
        maxLength={maxLength}
        onChange={(event) => onChange(event.target.value)}
        onBlur={onBlur}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck={false}
        aria-invalid={hasError}
        aria-describedby={hasError ? errorId : undefined}
        className={[
          "w-full rounded-2xl border bg-white/[0.04] px-4 py-3 text-base text-white placeholder:text-white/30 transition focus:outline-none focus:ring-4",
          hasError
            ? "border-red-400/40 focus:border-red-300 focus:ring-red-400/10"
            : "border-white/10 hover:border-white/20 focus:border-pitch focus:ring-pitch/15",
        ].join(" ")}
      />
      {hasError ? (
        <p id={errorId} className="text-xs text-red-300">
          {error}
        </p>
      ) : null}
    </div>
  );
}