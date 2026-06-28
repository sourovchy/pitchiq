import { Link } from "react-router";

const FEATURES = [
  {
    label: "Live",
    title: "Tactical match analysis",
    description:
      "Pick any two national teams. Receive a structured pre-match brief covering formations, structural strengths, key duels, and expected game flow.",
    to: "/analysis",
    status: "Available",
    accent: "pitch",
  },
] as const;

const HIGHLIGHTS = [
  { label: "Tournament", value: "FIFA World Cup 2026" },
  { label: "Format", value: "Structured JSON brief" },
  { label: "Latency", value: "~8 – 15 seconds" },
];

export function HomePage() {
  return (
    <>
      <section className="relative isolate overflow-hidden mx-auto max-w-7xl px-6 pt-14 pb-16 sm:pt-20 lg:px-8 lg:pt-28 lg:pb-24">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[520px] bg-[radial-gradient(700px_320px_at_50%_0%,color-mix(in_srgb,var(--color-pitch)_22%,transparent),transparent_70%)]"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -right-32 top-20 -z-10 size-[420px] rounded-full bg-pitch/[0.07] blur-3xl"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -left-24 bottom-0 -z-10 size-[320px] rounded-full bg-pitch-deep/15 blur-3xl"
        />

        <div className="max-w-3xl animate-[rise-in_600ms_ease-out]">
          <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-pitch/30 bg-pitch/[0.1] px-3 py-1 text-[11px] font-semibold tracking-[0.24em] text-pitch uppercase shadow-[0_0_24px_color-mix(in_srgb,var(--color-pitch)_20%,transparent)]">
            <span
              aria-hidden
              className="relative inline-flex size-2 items-center justify-center"
            >
              <span className="absolute inline-flex size-full animate-[pulse-glow_2.4s_ease-in-out_infinite] rounded-full bg-pitch" />
              <span className="relative inline-flex size-1.5 rounded-full bg-pitch" />
            </span>
            Football Intelligence, Reimagined.
          </p>
          <h1 className="text-5xl leading-[0.95] font-semibold tracking-[-0.045em] text-balance sm:text-7xl lg:text-[5.25rem]">
            See the match before it unfolds.
          </h1>
          <p className="mt-7 max-w-2xl text-base leading-7 text-white/70 sm:text-lg">
            <span className="font-semibold text-white">PitchIQ</span> turns the qualitative read on a World Cup fixture into a
            structured tactical brief — formations, structural strengths, key
            duels, expected game flow, and the coaching levers that swing the
            result.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-3">
            <Link
              to="/analysis"
              className="group relative inline-flex items-center justify-center overflow-hidden rounded-full bg-gradient-to-b from-pitch to-pitch-deep px-7 py-3 text-sm font-semibold text-ink shadow-[0_8px_28px_-8px_color-mix(in_srgb,var(--color-pitch)_55%,transparent),inset_0_1px_0_color-mix(in_srgb,#ffffff_25%,transparent)] transition hover:from-pitch-soft hover:to-pitch"
            >
              <span className="relative">Start a tactical brief</span>
              <span
                aria-hidden
                className="relative ml-2 transition group-hover:translate-x-0.5"
              >
                →
              </span>
            </Link>
          </div>
        </div>

        <dl className="mt-14 grid max-w-3xl grid-cols-1 gap-3 sm:grid-cols-3">
          {HIGHLIGHTS.map((item) => (
            <div
              key={item.label}
              className="group relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.04] via-white/[0.02] to-transparent p-4 transition hover:border-pitch/30 hover:shadow-[0_0_24px_color-mix(in_srgb,var(--color-pitch)_18%,transparent)]"
            >
              <div
                aria-hidden
                className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent"
              />
              <dt className="text-[10px] font-semibold tracking-[0.22em] text-white/50 uppercase">
                {item.label}
              </dt>
              <dd className="mt-2 text-sm font-medium text-white">
                {item.value}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section
        aria-label="Features"
        className="mx-auto max-w-7xl px-6 pb-20 lg:px-8 lg:pb-28"
      >
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
              Modules
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              Built for the modern tactical analyst.
            </h2>
          </div>
          <p className="hidden max-w-sm text-sm text-white/55 sm:block">
            One focused workflow, shipped end-to-end for the FIFA World Cup 2026.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <article
              key={feature.title}
              className="group relative flex flex-col overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.05] via-white/[0.025] to-transparent p-6 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_6%,transparent)] transition hover:-translate-y-0.5 hover:border-white/20 hover:shadow-[0_24px_48px_-24px_color-mix(in_srgb,#000_70%,transparent),0_0_24px_color-mix(in_srgb,var(--color-pitch)_12%,transparent)]"
            >
              <div
                aria-hidden
                className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent"
              />
              <div
                aria-hidden
                className={[
                  "pointer-events-none absolute -right-16 -top-16 size-44 rounded-full blur-3xl transition opacity-60",
                  feature.accent === "pitch"
                    ? "bg-pitch/15 group-hover:bg-pitch/25"
                    : "bg-pitch-soft/10 group-hover:bg-pitch-soft/20",
                ].join(" ")}
              />
              <div className="relative flex items-center justify-between">
                <p className="text-[10px] font-semibold tracking-[0.22em] text-pitch uppercase">
                  {feature.label}
                </p>
                <span
                  className={[
                    "inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold tracking-[0.18em] uppercase",
                    feature.accent === "pitch"
                      ? "border-pitch/40 bg-pitch/10 text-pitch"
                      : "border-white/15 bg-white/[0.04] text-white/65",
                  ].join(" ")}
                >
                  {feature.status}
                </span>
              </div>
              <h3 className="relative mt-4 text-xl font-semibold tracking-tight text-white">
                {feature.title}
              </h3>
              <p className="relative mt-3 text-sm leading-6 text-white/65">
                {feature.description}
              </p>
              <div className="relative mt-6 pt-4">
                <Link
                  to={feature.to}
                  className="inline-flex items-center text-sm font-semibold text-pitch transition group-hover:text-pitch-soft"
                >
                  Open module
                  <span
                    aria-hidden
                    className="ml-1 transition group-hover:translate-x-0.5"
                  >
                    →
                  </span>
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

