import type { Importance, TacticalInsight } from "../../../types/analysis";

interface TacticalInsightsProps {
  insights: TacticalInsight[];
}

const IMPORTANCE_LABEL: Record<Importance, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
};

const IMPORTANCE_STYLE: Record<Importance, string> = {
  critical: "border-pitch/40 bg-pitch/10 text-pitch",
  high: "border-pitch-soft/40 bg-pitch-soft/10 text-pitch-soft",
  medium: "border-white/15 bg-white/[0.04] text-white/65",
};

export function TacticalInsights({ insights }: TacticalInsightsProps) {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.04] via-white/[0.02] to-transparent p-5 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] sm:p-6">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/40 to-transparent"
      />
      <h4 className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
        Tactical insights
      </h4>
      {insights.length === 0 ? (
        <p className="mt-5 text-sm text-white/55">
          No tactical insights returned.
        </p>
      ) : (
        <ul className="mt-5 grid gap-3 sm:grid-cols-2">
          {insights.map((insight, index) => (
            <li
              key={`insight-${index}`}
              className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.035] to-transparent p-4 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] transition hover:-translate-y-0.5 hover:border-pitch/30 hover:shadow-[0_8px_24px_-12px_color-mix(in_srgb,var(--color-pitch)_30%,transparent)]"
            >
              <div
                aria-hidden
                className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/35 to-transparent"
              />
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-semibold tracking-tight">
                  {insight.title}
                </p>
                <span
                  className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold tracking-[0.2em] uppercase shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] ${IMPORTANCE_STYLE[insight.importance]}`}
                >
                  {IMPORTANCE_LABEL[insight.importance]}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-white/80">
                {insight.detail}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}