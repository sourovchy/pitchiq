import type { AnalysisResponse } from "../../../types/analysis";

interface MatchHeaderProps {
  analysis: AnalysisResponse;
}

export function MatchHeader({ analysis }: MatchHeaderProps) {
  const { homeTeam, awayTeam, predictedWinner, confidence } = analysis;
  const homeKey = homeTeam.name.toLowerCase();
  const awayKey = awayTeam.name.toLowerCase();
  const winnerKey = predictedWinner.toLowerCase();

  const isDraw = winnerKey === "draw";
  const isHomeWinner = winnerKey === homeKey;
  const isAwayWinner = winnerKey === awayKey;
  const winnerLabel = isDraw
    ? "Draw"
    : isHomeWinner
      ? homeTeam.name
      : isAwayWinner
        ? awayTeam.name
        : predictedWinner;

  const confidenceClamped = Math.max(0, Math.min(100, confidence));
  const confidenceTone =
    confidenceClamped >= 70
      ? "text-pitch"
      : confidenceClamped >= 50
        ? "text-pitch-soft"
        : "text-white/65";

  return (
    <header className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.05] via-white/[0.025] to-transparent p-6 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_6%,transparent)] sm:p-8">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/60 to-transparent"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-32 -right-24 size-72 rounded-full bg-pitch/12 blur-3xl"
      />
      <div className="relative flex items-center justify-between gap-3">
        <p className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
          Tactical verdict
        </p>
        <span className="inline-flex items-center rounded-full border border-white/15 bg-white/[0.04] px-2.5 py-1 text-[10px] font-semibold tracking-[0.2em] text-white/65 uppercase shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)]">
          Match prediction
        </span>
      </div>

      <div className="relative mt-5 grid gap-6 lg:grid-cols-[1fr_auto] lg:items-end">
        <div>
          <h2 className="text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
            <span>{homeTeam.name}</span>
            <span className="mx-3 text-white/25">vs</span>
            <span>{awayTeam.name}</span>
          </h2>
          <p className="mt-4 max-w-2xl text-base leading-7 text-white/70 sm:text-lg">
            {analysis.matchOverview}
          </p>
        </div>

        <div className="relative overflow-hidden rounded-2xl border border-pitch/35 bg-gradient-to-br from-pitch/[0.12] via-pitch/[0.06] to-transparent px-5 py-4 shadow-[inset_0_1px_0_color-mix(in_srgb,var(--color-pitch-soft)_18%,transparent)] sm:min-w-[16rem]">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/70 to-transparent"
          />
          <p className="text-[10px] font-semibold tracking-[0.22em] text-pitch uppercase">
            Predicted winner
          </p>
          <p className="mt-2 text-2xl font-semibold tracking-tight">
            {winnerLabel}
          </p>
          <div className="mt-3 flex items-center justify-between gap-3">
            <span className="text-xs text-white/55">Confidence</span>
            <span className={`text-sm font-semibold tabular-nums ${confidenceTone}`}>
              {confidenceClamped}%
            </span>
          </div>
          <div
            className="mt-2 h-2 overflow-hidden rounded-full bg-white/10 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)]"
            role="progressbar"
            aria-valuenow={confidenceClamped}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Prediction confidence"
          >
            <div
              className="h-full rounded-full bg-gradient-to-r from-pitch-deep via-pitch to-pitch-soft shadow-[0_0_14px_color-mix(in_srgb,var(--color-pitch)_65%,transparent)]"
              style={{ width: `${confidenceClamped}%` }}
            />
          </div>
        </div>
      </div>
    </header>
  );
}