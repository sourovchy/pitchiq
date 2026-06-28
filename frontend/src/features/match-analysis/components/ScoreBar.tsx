interface ScoreBarProps {
  label: string;
  homeValue: number;
  awayValue: number;
  homeName: string;
  awayName: string;
}

export function ScoreBar({
  label,
  homeValue,
  awayValue,
  homeName,
  awayName,
}: ScoreBarProps) {
  const safeHome = Math.max(0, homeValue);
  const safeAway = Math.max(0, awayValue);
  const total = Math.max(1, safeHome + safeAway);
  const homePct = (safeHome / total) * 100;
  const awayPct = (safeAway / total) * 100;

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.04] to-transparent p-5 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)]">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/35 to-transparent"
      />
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold tracking-[0.22em] text-white/45 uppercase">
          {label}
        </p>
        <p className="text-xs font-medium text-white/55 tabular-nums">
          {safeHome} <span className="text-white/25">–</span> {safeAway}
        </p>
      </div>
      <div
        className="mt-4 flex h-2 overflow-hidden rounded-full bg-white/10 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)]"
        role="img"
        aria-label={`${homeName} ${safeHome}, ${awayName} ${safeAway}`}
      >
        <div
          className="h-full bg-gradient-to-r from-pitch-deep via-pitch to-pitch-soft shadow-[0_0_12px_color-mix(in_srgb,var(--color-pitch)_45%,transparent)]"
          style={{ width: `${homePct}%` }}
          aria-hidden
        />
        <div
          className="h-full bg-gradient-to-r from-pitch-soft/80 via-pitch-soft to-pitch-soft/60"
          style={{ width: `${awayPct}%` }}
          aria-hidden
        />
      </div>
      <div className="mt-3 flex justify-between text-xs">
        <span className="max-w-[45%] truncate font-medium text-white/75">
          {homeName}
        </span>
        <span className="max-w-[45%] truncate text-right font-medium text-white/75">
          {awayName}
        </span>
      </div>
    </div>
  );
}