import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <section className="mx-auto flex min-h-[60vh] max-w-4xl flex-col items-start justify-center px-6 py-20 lg:px-8">
      <div className="relative w-full overflow-hidden rounded-3xl border border-white/10 bg-premium-mesh bg-gradient-to-br from-white/[0.04] via-white/[0.02] to-transparent px-8 py-12 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] sm:px-12 sm:py-16">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-pitch/0 via-pitch/60 to-pitch/0"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -top-28 -right-24 size-72 rounded-full bg-pitch/12 blur-3xl"
        />
        <div className="relative">
          <p className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
            404 · Off the pitch
          </p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
            We couldn't find that route.
          </h1>
          <p className="mt-4 max-w-xl text-base text-white/65 sm:text-lg">
            The page you're looking for doesn't exist or has been moved. Head back
            to the overview or jump straight into the tactical brief.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              to="/"
              className="inline-flex items-center justify-center rounded-full bg-gradient-to-b from-pitch to-pitch-deep px-6 py-3 text-sm font-semibold text-ink shadow-[0_8px_22px_-8px_color-mix(in_srgb,var(--color-pitch)_55%,transparent),inset_0_1px_0_color-mix(in_srgb,#ffffff_25%,transparent)] transition hover:from-pitch-soft hover:to-pitch"
            >
              Back to overview
              <span aria-hidden className="ml-2">
                →
              </span>
            </Link>
            <Link
              to="/analysis"
              className="inline-flex items-center justify-center rounded-full border border-white/15 bg-white/[0.03] px-5 py-3 text-sm font-semibold text-white/85 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] transition hover:border-white/25 hover:bg-white/[0.06]"
            >
              Open tactical analysis
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

