import type { CoachRecommendation as CoachRecommendationData } from "../../../types/analysis";

interface CoachRecommendationProps {
  homeName: string;
  awayName: string;
  recommendation: CoachRecommendationData;
}

export function CoachRecommendation({
  homeName,
  awayName,
  recommendation,
}: CoachRecommendationProps) {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-pitch/25 bg-gradient-to-br from-pitch/[0.07] via-white/[0.02] to-transparent p-5 shadow-[inset_0_1px_0_color-mix(in_srgb,var(--color-pitch-soft)_10%,transparent)] sm:p-6">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/55 to-transparent"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 -right-20 size-64 rounded-full bg-pitch/10 blur-3xl"
      />
      <h4 className="relative text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
        Coach recommendation
      </h4>
      <div className="relative mt-5 grid gap-5 md:grid-cols-2">
        <Plan label={homeName} plan={recommendation.home} side="home" />
        <Plan label={awayName} plan={recommendation.away} side="away" />
      </div>
      <div className="relative mt-6 overflow-hidden rounded-2xl border border-pitch/35 bg-gradient-to-br from-pitch/[0.12] via-pitch/[0.06] to-transparent p-4 shadow-[inset_0_1px_0_color-mix(in_srgb,var(--color-pitch-soft)_20%,transparent)]">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/70 to-transparent"
        />
        <p className="text-[10px] font-semibold tracking-[0.22em] text-pitch uppercase">
          Decisive adjustment
        </p>
        <p className="mt-2 text-sm leading-6 text-white/90">
          {recommendation.decisiveAdjustment}
        </p>
      </div>
    </section>
  );
}

interface PlanProps {
  label: string;
  plan: string;
  side: "home" | "away";
}

const SIDE_BADGE: Record<PlanProps["side"], string> = {
  home: "border-pitch/35 bg-pitch/10 text-pitch",
  away: "border-pitch-soft/35 bg-pitch-soft/10 text-pitch-soft",
};

function Plan({ label, plan, side }: PlanProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.04] to-transparent p-4 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)]">
      <div
        aria-hidden
        className={`pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent ${
          side === "home" ? "via-pitch/35" : "via-pitch-soft/30"
        } to-transparent`}
      />
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-white/90">{label}</p>
        <span
          className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold tracking-[0.2em] uppercase shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] ${SIDE_BADGE[side]}`}
        >
          {side === "home" ? "Home plan" : "Away plan"}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-white/75">{plan}</p>
    </div>
  );
}