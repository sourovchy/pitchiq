import type { FormationMatchup as FormationMatchupData } from "../../../types/analysis";

interface FormationsSectionProps {
  matchup: FormationMatchupData;
  homeName: string;
  awayName: string;
}

export function FormationsSection({
  matchup,
  homeName,
  awayName,
}: FormationsSectionProps) {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.04] via-white/[0.02] to-transparent p-5 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] sm:p-6">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/40 to-transparent"
      />
      <div className="flex items-center justify-between">
        <h4 className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
          Formation matchup
        </h4>
        <span className="text-[10px] tracking-[0.2em] text-white/40 uppercase">
          Shape vs shape
        </span>
      </div>
      <div className="mt-5 grid grid-cols-[1fr_auto_1fr] items-stretch gap-3">
        <FormationCell label={homeName} formation={matchup.home} side="home" />
        <div
          aria-hidden
          className="flex items-center justify-center text-xs font-semibold tracking-[0.2em] text-white/35 uppercase"
        >
          vs
        </div>
        <FormationCell label={awayName} formation={matchup.away} side="away" />
      </div>
      <p className="mt-5 rounded-2xl border border-white/8 bg-white/[0.025] px-4 py-3 text-sm leading-6 text-white/80 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_4%,transparent)]">
        {matchup.matchup}
      </p>
    </section>
  );
}

interface FormationCellProps {
  label: string;
  formation: string;
  side: "home" | "away";
}

const SIDE_ALIGN: Record<FormationCellProps["side"], string> = {
  home: "text-left",
  away: "text-right",
};

const SIDE_COLOR: Record<FormationCellProps["side"], string> = {
  home: "text-pitch",
  away: "text-pitch-soft",
};

const SIDE_RING: Record<FormationCellProps["side"], string> = {
  home: "border-pitch/15",
  away: "border-pitch-soft/15",
};

function FormationCell({ label, formation, side }: FormationCellProps) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border ${SIDE_RING[side]} bg-gradient-to-br from-white/[0.035] to-transparent px-4 py-4 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] ${SIDE_ALIGN[side]}`}
    >
      <div
        aria-hidden
        className={`pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent ${
          side === "home" ? "via-pitch/40" : "via-pitch-soft/35"
        } to-transparent`}
      />
      <p className="text-xs font-medium text-white/55">{label}</p>
      <p className={`mt-1 text-2xl font-semibold tracking-tight ${SIDE_COLOR[side]}`}>
        {formation}
      </p>
    </div>
  );
}