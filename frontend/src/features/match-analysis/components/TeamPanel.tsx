import type { TeamProfile } from "../../../types/analysis";

interface TeamPanelProps {
  team: TeamProfile;
  side: "home" | "away";
}

const SIDE_ACCENT: Record<TeamPanelProps["side"], string> = {
  home: "border-pitch/20 hover:border-pitch/40 hover:shadow-[0_8px_28px_-12px_color-mix(in_srgb,var(--color-pitch)_35%,transparent)]",
  away: "border-pitch-soft/15 hover:border-pitch-soft/35 hover:shadow-[0_8px_28px_-12px_color-mix(in_srgb,var(--color-pitch-soft)_30%,transparent)]",
};

const SIDE_BADGE: Record<TeamPanelProps["side"], string> = {
  home: "border-pitch/35 bg-pitch/10 text-pitch",
  away: "border-pitch-soft/35 bg-pitch-soft/10 text-pitch-soft",
};

export function TeamPanel({ team, side }: TeamPanelProps) {
  const sideLabel = side === "home" ? "Home profile" : "Away profile";

  return (
    <article
      className={`relative overflow-hidden rounded-2xl border bg-gradient-to-br from-white/[0.04] to-transparent p-5 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] transition hover:-translate-y-0.5 ${SIDE_ACCENT[side]}`}
    >
      <div
        aria-hidden
        className={`pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent ${
          side === "home" ? "via-pitch/45" : "via-pitch-soft/40"
        } to-transparent`}
      />
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold tracking-[0.22em] text-white/45 uppercase">
          {sideLabel}
        </p>
        <span
          className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold tracking-[0.2em] uppercase shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] ${SIDE_BADGE[side]}`}
        >
          {side === "home" ? "Home" : "Away"}
        </span>
      </div>
      <h3 className="mt-3 text-xl font-semibold tracking-tight">{team.name}</h3>
      <dl className="mt-5 space-y-5">
        <Row label="Formation" value={team.formation} />
        <Row label="Playing style" value={team.playingStyle} />
        <Row label="Tactical identity" value={team.tacticalIdentity} />
      </dl>
    </article>
  );
}

interface RowProps {
  label: string;
  value: string;
}

function Row({ label, value }: RowProps) {
  return (
    <div>
      <dt className="text-[10px] font-semibold tracking-[0.22em] text-white/45 uppercase">
        {label}
      </dt>
      <dd className="mt-1.5 text-sm leading-6 text-white/85">{value}</dd>
    </div>
  );
}