import type { Edge, KeyBattle } from "../../../types/analysis";

interface KeyBattlesProps {
  homeName: string;
  awayName: string;
  battles: KeyBattle[];
}

const EDGE_LABEL: Record<Edge, string> = {
  home: "Home edge",
  away: "Away edge",
  even: "Even duel",
};

const EDGE_STYLE: Record<Edge, string> = {
  home: "border-pitch/40 bg-pitch/10 text-pitch",
  away: "border-pitch-soft/40 bg-pitch-soft/10 text-pitch-soft",
  even: "border-white/15 bg-white/[0.04] text-white/70",
};

export function KeyBattles({ homeName, awayName, battles }: KeyBattlesProps) {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.04] via-white/[0.02] to-transparent p-5 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] sm:p-6">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/40 to-transparent"
      />
      <div className="flex items-center justify-between">
        <h4 className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
          Key battles
        </h4>
        <span className="text-[10px] tracking-[0.2em] text-white/40 uppercase">
          Ranked by impact
        </span>
      </div>
      {battles.length === 0 ? (
        <p className="mt-5 text-sm text-white/55">
          No key battles returned for this matchup.
        </p>
      ) : (
        <ul className="mt-5 grid gap-3 sm:grid-cols-2">
          {battles.map((battle, index) => (
            <li
              key={`battle-${index}`}
              className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.035] to-transparent p-4 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] transition hover:-translate-y-0.5 hover:border-pitch/30 hover:shadow-[0_8px_24px_-12px_color-mix(in_srgb,var(--color-pitch)_30%,transparent)]"
            >
              <div
                aria-hidden
                className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/35 to-transparent"
              />
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold tracking-tight">
                    {battle.zone}
                  </p>
                  <p className="mt-1 text-sm text-white/70">
                    {battle.homePlayerOrUnit}
                    <span className="mx-2 text-white/30">vs</span>
                    {battle.awayPlayerOrUnit}
                  </p>
                </div>
                <span
                  className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold tracking-[0.2em] uppercase shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] ${EDGE_STYLE[battle.edge]}`}
                >
                  {EDGE_LABEL[battle.edge]}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-white/80">
                {battle.analysis}
              </p>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-5 text-xs text-white/40">
        {homeName} and {awayName} duels ranked by structural importance.
      </p>
    </section>
  );
}