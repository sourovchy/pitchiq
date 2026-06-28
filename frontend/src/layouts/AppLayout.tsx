import { NavLink, Outlet } from "react-router";

interface NavItem {
  label: string;
  to: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Overview", to: "/" },
  { label: "Match analysis", to: "/analysis" },
];

export function AppLayout() {
  return (
    <div className="min-h-screen bg-ink text-white">
      <header className="sticky top-0 z-30 border-b border-white/10 bg-ink/70 shadow-[0_1px_0_color-mix(in_srgb,var(--color-pitch)_15%,transparent),0_8px_24px_-12px_color-mix(in_srgb,#000_60%,transparent)] backdrop-blur-xl backdrop-saturate-150">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 -bottom-px h-px bg-gradient-to-r from-transparent via-pitch/40 to-transparent"
        />
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4 lg:px-8">
          <a
            href="/"
            className="group inline-flex items-center gap-3 text-sm font-semibold tracking-[0.22em] uppercase transition"
          >
            <span
              aria-hidden
              className="relative inline-flex size-8 items-center justify-center rounded-xl bg-gradient-to-br from-pitch/25 via-pitch/10 to-transparent ring-1 ring-pitch/40 transition group-hover:ring-pitch/70"
            >
              <span className="size-2 rounded-full bg-pitch shadow-[0_0_14px_var(--color-pitch-glow)]" />
              <span
                aria-hidden
                className="absolute inset-0 rounded-xl bg-pitch/0 transition group-hover:bg-pitch/5"
              />
            </span>
            <span className="text-white">
              Pitch<span className="text-pitch">IQ</span>
            </span>
            <span className="hidden rounded-full border border-pitch/25 bg-pitch/[0.08] px-2.5 py-0.5 text-[10px] font-medium tracking-[0.22em] text-pitch/90 sm:inline">
              WC 2026
            </span>
          </a>
          <nav aria-label="Primary">
            <ul className="flex flex-wrap items-center gap-1 rounded-full border border-white/10 bg-white/[0.03] p-1">
              {NAV_ITEMS.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) =>
                      [
                        "inline-flex items-center rounded-full px-3.5 py-1.5 text-sm font-medium transition",
                        isActive
                          ? "bg-gradient-to-b from-pitch/25 to-pitch/15 text-pitch shadow-[inset_0_0_0_1px_color-mix(in_srgb,var(--color-pitch)_35%,transparent)]"
                          : "text-white/65 hover:bg-white/[0.05] hover:text-white",
                      ].join(" ")
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="relative mx-auto max-w-7xl px-6 pt-12 pb-10 text-xs text-white/40 lg:px-8">
        <div
          aria-hidden
          className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent"
        />
        <div className="flex flex-wrap items-center justify-between gap-3 pt-6">
          <p className="tracking-wide">© 2026 PitchIQ · Football Intelligence, Reimagined.</p>
          <p className="tracking-[0.22em] uppercase text-white/50">
            Built for Hack Days CUET · FIFA World Cup 2026
          </p>
        </div>
      </footer>
    </div>
  );
}

