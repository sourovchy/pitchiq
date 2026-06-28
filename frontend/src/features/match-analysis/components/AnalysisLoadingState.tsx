import { useEffect, useState } from "react";

const STEPS = [
  {
    label: "Analyzing tactical matchup",
    detail: "Reading recent structural patterns and historical fixtures.",
  },
  {
    label: "Loading tournament knowledge",
    detail: "Pulling squad, formation, and context data from the knowledge base.",
  },
  {
    label: "Consulting Gemini",
    detail: "Running the specialist tactical-analyst role.",
  },
  {
    label: "Generating tactical report",
    detail: "Composing the structured JSON brief and validating the schema.",
  },
] as const;

const STEP_INTERVAL_MS = 2200;

interface AnalysisLoadingStateProps {
  homeTeam: string;
  awayTeam: string;
}

export function AnalysisLoadingState({
  homeTeam,
  awayTeam,
}: AnalysisLoadingStateProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % STEPS.length);
    }, STEP_INTERVAL_MS);
    return () => window.clearInterval(id);
  }, []);

  return (
    <section
      role="status"
      aria-live="polite"
      aria-busy="true"
      className="relative overflow-hidden rounded-3xl border border-pitch/25 bg-gradient-to-br from-pitch/[0.08] via-white/[0.02] to-transparent p-6 shadow-[inset_0_1px_0_color-mix(in_srgb,var(--color-pitch-soft)_12%,transparent)] sm:p-8"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/60 to-transparent"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-28 -right-24 size-72 rounded-full bg-pitch/12 blur-3xl"
      />
      <div className="relative flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
            Live analysis
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-balance">
            {homeTeam || "Home"} <span className="text-white/30">vs</span>{" "}
            {awayTeam || "Away"}
          </h2>
          <p className="mt-2 text-sm text-white/55">
            The tactical analyst is composing a structured brief. This usually
            finishes in 8 – 15 seconds.
          </p>
        </div>
        <div className="inline-flex items-center gap-2 self-start rounded-full border border-pitch/30 bg-pitch/10 px-3 py-1.5 text-[11px] font-semibold tracking-[0.18em] text-pitch uppercase shadow-[inset_0_1px_0_color-mix(in_srgb,var(--color-pitch-soft)_20%,transparent)]">
          <span
            aria-hidden
            className="size-1.5 animate-pulse rounded-full bg-pitch shadow-[0_0_12px_color-mix(in_srgb,var(--color-pitch)_80%,transparent)]"
          />
          Working
        </div>
      </div>

      <ol className="relative mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((step, index) => {
          const state =
            index < activeIndex
              ? "done"
              : index === activeIndex
                ? "active"
                : "queued";
          return (
            <li
              key={step.label}
              aria-current={state === "active" ? "step" : undefined}
              className={[
                "relative overflow-hidden rounded-2xl border p-4 transition shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)]",
                state === "active"
                  ? "border-pitch/45 bg-gradient-to-br from-pitch/[0.14] via-pitch/[0.06] to-transparent shadow-[0_0_22px_-6px_color-mix(in_srgb,var(--color-pitch)_45%,transparent)]"
                  : state === "done"
                    ? "border-pitch/20 bg-white/[0.035]"
                    : "border-white/10 bg-white/[0.02]",
              ].join(" ")}
            >
              <div
                aria-hidden
                className={[
                  "pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent to-transparent",
                  state === "active"
                    ? "via-pitch/70"
                    : state === "done"
                      ? "via-pitch/35"
                      : "via-white/10",
                ].join(" ")}
              />
              <div className="flex items-center justify-between">
                <span
                  className={[
                    "inline-flex size-6 items-center justify-center rounded-full text-[11px] font-semibold tabular-nums",
                    state === "active"
                      ? "bg-gradient-to-b from-pitch-soft to-pitch text-ink shadow-[0_0_12px_color-mix(in_srgb,var(--color-pitch)_70%,transparent),inset_0_1px_0_color-mix(in_srgb,#ffffff_40%,transparent)]"
                      : state === "done"
                        ? "bg-pitch/15 text-pitch shadow-[inset_0_1px_0_color-mix(in_srgb,var(--color-pitch-soft)_20%,transparent)]"
                        : "bg-white/10 text-white/50",
                  ].join(" ")}
                >
                  {state === "done" ? "✓" : index + 1}
                </span>
                {state === "active" ? (
                  <span
                    aria-hidden
                    className="size-1.5 animate-pulse rounded-full bg-pitch shadow-[0_0_12px_color-mix(in_srgb,var(--color-pitch)_80%,transparent)]"
                  />
                ) : null}
              </div>
              <p
                className={[
                  "mt-3 text-sm font-semibold tracking-tight",
                  state === "queued" ? "text-white/55" : "text-white",
                ].join(" ")}
              >
                {step.label}
              </p>
              <p
                className={[
                  "mt-1 text-xs leading-5",
                  state === "active" ? "text-white/70" : "text-white/45",
                ].join(" ")}
              >
                {step.detail}
              </p>
            </li>
          );
        })}
      </ol>

      <p className="relative mt-6 flex items-center gap-2 text-xs text-white/45">
        <span
          aria-hidden
          className="inline-block h-px w-6 bg-gradient-to-r from-pitch/0 via-pitch/55 to-pitch/0"
        />
        Validating output against the Pydantic schema.
      </p>
    </section>
  );
}