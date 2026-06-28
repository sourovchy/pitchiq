import type { GameFlow as GameFlowData } from "../../../types/analysis";

interface GameFlowProps {
  flow: GameFlowData;
}

const PHASES = [
  { key: "openingPhase", label: "Opening phase", hint: "First 20 minutes" },
  { key: "middlePhase", label: "Middle phase", hint: "20 – 70 minutes" },
  { key: "closingPhase", label: "Closing phase", hint: "Final 20 minutes" },
] as const satisfies Array<{ key: keyof GameFlowData; label: string; hint: string }>;

export function GameFlow({ flow }: GameFlowProps) {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.04] via-white/[0.02] to-transparent p-5 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] sm:p-6">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/40 to-transparent"
      />
      <h4 className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
        Expected game flow
      </h4>
      <ol className="mt-5 grid gap-4 md:grid-cols-3">
        {PHASES.map((phase, index) => (
          <li
            key={phase.key}
            className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.035] to-transparent p-4 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] transition hover:-translate-y-0.5 hover:border-pitch/30 hover:shadow-[0_8px_24px_-12px_color-mix(in_srgb,var(--color-pitch)_30%,transparent)]"
          >
            <div
              aria-hidden
              className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/35 to-transparent"
            />
            <div className="flex items-center gap-3">
              <span
                aria-hidden
                className="inline-flex size-7 items-center justify-center rounded-full border border-pitch/35 bg-gradient-to-b from-pitch/15 to-pitch/5 text-[11px] font-semibold text-pitch shadow-[inset_0_1px_0_color-mix(in_srgb,var(--color-pitch-soft)_25%,transparent),0_0_12px_color-mix(in_srgb,var(--color-pitch)_35%,transparent)] tabular-nums"
              >
                {index + 1}
              </span>
              <div>
                <p className="text-sm font-semibold tracking-tight">
                  {phase.label}
                </p>
                <p className="text-[10px] tracking-[0.2em] text-white/40 uppercase">
                  {phase.hint}
                </p>
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-white/75">
              {flow[phase.key]}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}