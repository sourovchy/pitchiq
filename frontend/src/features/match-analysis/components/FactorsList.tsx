interface FactorsListProps {
  title: string;
  homeName: string;
  awayName: string;
  homeItems: string[];
  awayItems: string[];
}

export function FactorsList({
  title,
  homeName,
  awayName,
  homeItems,
  awayItems,
}: FactorsListProps) {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.04] via-white/[0.02] to-transparent p-5 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] sm:p-6">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-pitch/40 to-transparent"
      />
      <h4 className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
        {title}
      </h4>
      <div className="mt-5 grid gap-6 sm:grid-cols-2">
        <Column label={homeName} items={homeItems} accent="pitch" />
        <Column label={awayName} items={awayItems} accent="soft" />
      </div>
    </section>
  );
}

interface ColumnProps {
  label: string;
  items: string[];
  accent: "pitch" | "soft";
}

const DOT_COLOR: Record<ColumnProps["accent"], string> = {
  pitch:
    "bg-pitch shadow-[0_0_10px_color-mix(in_srgb,var(--color-pitch)_55%,transparent)]",
  soft:
    "bg-pitch-soft shadow-[0_0_10px_color-mix(in_srgb,var(--color-pitch-soft)_50%,transparent)]",
};

function Column({ label, items, accent }: ColumnProps) {
  return (
    <div>
      <p className="text-sm font-semibold text-white/85">{label}</p>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-white/45">No items returned.</p>
      ) : (
        <ul className="mt-3 space-y-3 text-sm leading-6 text-white/85">
          {items.map((item, index) => (
            <li key={`${label}-${index}`} className="flex gap-3">
              <span
                aria-hidden
                className={`mt-2 size-1.5 flex-none rounded-full ${DOT_COLOR[accent]}`}
              />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}