import { AnalysisApiError } from "../../../services/analysisService";

interface AnalysisErrorStateProps {
  error: AnalysisApiError;
  onRetry?: () => void;
}

const ERROR_TITLE: Record<string, string> = {
  gemini_not_configured: "Tactical engine offline",
  gemini_unavailable: "The analyst didn't respond",
  invalid_analysis_response: "The brief couldn't be formed",
  invalid_request: "Check the team names",
  request_timeout: "Took too long to respond",
  request_cancelled: "Request cancelled",
  network_error: "Network problem",
  unknown_error: "Something broke down",
};

const ERROR_HINT: Record<string, string> = {
  gemini_not_configured:
    "The backend is missing its Gemini credentials. Set GEMINI_API_KEY and retry.",
  gemini_unavailable:
    "The model endpoint rejected the request. Retry in a moment, or try a different matchup.",
  invalid_analysis_response:
    "The response didn't match the tactical schema. Retry — the analyst will regenerate the brief.",
  invalid_request:
    "Make sure both teams are spelled clearly and represent different national sides.",
  request_timeout:
    "The 30 second budget elapsed. Retry to send the brief again.",
  request_cancelled:
    "The previous request was cancelled before it finished.",
  network_error:
    "We couldn't reach the API. Check your connection and retry.",
  unknown_error:
    "An unexpected error happened. Retry, and contact support if it persists.",
};

export function AnalysisErrorState({ error, onRetry }: AnalysisErrorStateProps) {
  const title = ERROR_TITLE[error.code] ?? "Something broke down";
  const hint = ERROR_HINT[error.code] ?? ERROR_HINT.unknown_error;

  return (
    <section
      role="alert"
      className="relative overflow-hidden rounded-3xl border border-red-400/25 bg-gradient-to-br from-red-400/[0.10] via-white/[0.02] to-transparent p-6 shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)] sm:p-8"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-red-300/55 to-transparent"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-28 -right-24 size-72 rounded-full bg-red-400/10 blur-3xl"
      />
      <div className="relative flex items-center justify-between gap-3">
        <p className="text-[10px] font-semibold tracking-[0.24em] text-red-300 uppercase">
          {title}
        </p>
        {error.status ? (
          <span className="inline-flex items-center rounded-full border border-white/15 bg-white/[0.04] px-2.5 py-1 text-[10px] font-semibold tracking-[0.2em] text-white/55 uppercase shadow-[inset_0_1px_0_color-mix(in_srgb,#ffffff_5%,transparent)]">
            HTTP {error.status}
          </span>
        ) : null}
      </div>
      <p className="relative mt-4 text-base font-medium text-white sm:text-lg">
        {error.message}
      </p>
      <p className="relative mt-3 max-w-2xl text-sm leading-6 text-white/55">
        {hint}
      </p>
      {onRetry ? (
        <div className="relative mt-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={onRetry}
            className="group relative inline-flex items-center justify-center overflow-hidden rounded-full bg-gradient-to-b from-pitch to-pitch-deep px-6 py-2.5 text-sm font-semibold text-ink shadow-[0_8px_22px_-8px_color-mix(in_srgb,var(--color-pitch)_55%,transparent),inset_0_1px_0_color-mix(in_srgb,#ffffff_25%,transparent)] transition hover:from-pitch-soft hover:to-pitch"
          >
            Try again
            <span aria-hidden className="ml-2">
              ↻
            </span>
          </button>
          <span className="text-xs text-white/40">
            Resends the last matchup to the analyst.
          </span>
        </div>
      ) : null}
    </section>
  );
}